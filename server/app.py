import argparse
import ipaddress
import json
import logging
import socketserver
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
from .configuration import Configuration, LOCALES
from .library import ROOT, c
from .player import test_player, login_response, home_response
from .protocol import plaintext_response, main_response, request_packet, reject
from .state import Accounts, Sessions, fingerprint
from . import gameplay, cooking, shop, local_voices, tutorial,recipe_progression,guides,missions,local_gacha
from . import cooking_acceleration,profile,friends,events,home_items,event_gameplay

LOG = logging.getLogger("gudetama.local")
OFFSET_SECS = 1262271600


def validate_local_origin(origin):
    url = urlsplit(origin)
    if url.scheme != "http" or not url.hostname or url.username or url.password or url.path not in ("", "/") or url.query or url.fragment:
        raise ValueError("origin must be a plain local http://IP:port")
    address = ipaddress.ip_address(url.hostname)
    if not (address.is_loopback or address.is_private) or address.is_unspecified or address.is_multicast:
        raise ValueError("only loopback/private test addresses are permitted")
    if url.port is None:
        raise ValueError("explicit port required")
    return origin.rstrip("/")


class Application:
    def __init__(self, origin="http://127.0.0.1:8080", db_path=":memory:", mode="unified", rules=None):
        from .local_cooking import Engine, validate_database, initialize_database
        from .local_cooking_rules import Rules
        if mode not in ("unified", "historical", "local_compatible"):
            raise ValueError("unknown server mode")
        # Legacy command-line values are aliases, not different behavior modes.
        self.mode = 'unified'
        self.origin = validate_local_origin(origin)
        self.config = Configuration(self.origin + "/gde/static/", local_shop=True)
        rules = rules or Rules.current(self.config.definitions['ja'])
        if str(db_path) != ':memory:':
            validate_database(db_path, rules)
        self.local_cooking = Engine(rules)
        self.local_cooking.candidate_policy = self.config.definitions['ja']
        self.accounts = Accounts(db_path)
        if str(db_path) == ':memory:':
            initialize_database(self.accounts.db,rules)
        self.accounts.db.execute('CREATE TABLE IF NOT EXISTS tutorial_test_metadata(name TEXT PRIMARY KEY,value TEXT NOT NULL)')
        self.accounts.db.execute("INSERT OR REPLACE INTO tutorial_test_metadata VALUES('enabled','1')")
        self.accounts.db.commit()
        self.tutorial_test = True
        self.local_gacha = local_gacha.Engine()
        from .database import optimize_indexes
        optimize_indexes(self.accounts.db)
        if self.local_cooking:
            shop.prepare_database(self.accounts)
            if self.tutorial_test:
                self.local_cooking.progression_sync = lambda p,db,d:recipe_progression.refresh(p,db,d,self.config.definitions['ja'])+missions.extras(p,db,d)
        self.sessions = Sessions()

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD", "GET")
        status, mime, body = "200 OK", "application/octet-stream", b""
        try:
            if path == "/health" and method == "GET":
                mime = "application/json"
                body = json.dumps({"status": "ok", "setting_version": self.config.version, "cooking_mode": self.mode, "tutorial_test":self.tutorial_test,"client_runtime_verified": False}).encode()
            elif path.startswith("/gde/static/") and method in ("GET", "HEAD"):
                body, mime = self.config.asset(path[len("/gde/static/"):])
            elif path in ("/gde/uiid", "/gde/direct", "/gde/entrance", "/gde/main", "/gde/report"):
                if method != "POST":
                    status, body = "405 Method Not Allowed", reject("POST required")
                else:
                    size = int(environ.get("CONTENT_LENGTH") or 0)
                    if not 0 <= size <= 1024 * 1024:
                        raise ValueError("invalid request body size")
                    if size and environ.get("CONTENT_TYPE", "").split(";")[0] != "application/x-www-form-urlencoded":
                        raise ValueError("expected URLVariables form body")
                    raw = environ["wsgi.input"].read(size)
                    if len(raw) != size:
                        raise ValueError("truncated HTTP body")
                    fields = parse_qs(raw.decode("utf-8"), keep_blank_values=True, max_num_fields=20)
                    if any(len(value) != 1 for value in fields.values()):
                        raise ValueError("duplicate form fields")
                    body = self.route(path, {key: value[0] for key, value in fields.items()})
            else:
                status, body = "404 Not Found", reject("unsupported local route")
        except FileNotFoundError:
            status, body = "404 Not Found", b"asset unavailable"
            LOG.warning("missing_asset path=%s", path)
        except KeyError:
            # Confirmed response status -2 initiates client's re-entrance login.
            body = b"\xfe"
            LOG.warning("invalid_session path=%s", path)
        except (ValueError, UnicodeError, OverflowError) as error:
            body = reject("Local request rejected: " + str(error))
            LOG.warning("rejected path=%s reason=%s", path, error)
        except Exception:
            status, body = "500 Internal Server Error", reject("Local internal error; see server log")
            LOG.exception("request_failed path=%s", path)
        start_response(status, [("Content-Type", mime), ("Content-Length", str(len(body))), ("Cache-Control", "no-store")])
        LOG.info("http method=%s path=%s status=%s bytes=%s", method, path, status, len(body))
        return [b"" if method == "HEAD" else body]

    def route(self, path, form):
        if path == "/gde/report":
            # HttpConnector.sendTraceLog: ui, u, log; no response object consumer.
            if set(form) != {"ui", "u", "log"}:
                raise ValueError("report fields do not match client source")
            message = form["log"][:6000]
            if not any(word in message.lower() for word in ("receipt", "token", "sessionid", "keybytes", "access_token")):
                LOG.warning("client_report %s", message.replace("\r", "").replace("\n", " | "))
            return b""
        if path == "/gde/uiid":
            if form:
                raise ValueError("UIID request has no fields")
            return plaintext_response(c.String(self.accounts.new_uiid()))
        if path == "/gde/direct":
            if set(form) == {"d", "a", "va"} and form["d"] == "b" and form["a"] in ("0", "1") and form["va"] == "1.47.5":
                # InitialScene.as:249-260 accepts null and continues without a rate.
                return plaintext_response(c.Null())
            if form != {"d": "g"}:
                return reject("Direct operation not yet implemented")
            return plaintext_response(c.IntArray([self.config.version, 0]))
        if path == "/gde/entrance":
            required = {"u", "v", "p", "c", "i", "l", "o"}
            if not required <= form.keys() or form.keys() - required - {"n"}:
                raise ValueError("entrance fields do not match client source")
            # Engine.as:345-351: iOS=0, Android=1. HttpConnector.as:373-379
            # uses the same entrance fields and protocol version on both.
            if form["v"] != "1.47.5" or form["p"] not in ("0", "1") or form["c"] != "34" or form["o"] != "0":
                raise ValueError("only iOS/Android 1.47.5 / protocol 34 supported")
            if form["l"] not in LOCALES:
                raise ValueError("locale has no archived configuration")
            # Installed clients retain UIID when changing servers/saves and skip
            # /uiid. Accept their cached identifier as a fresh account on this
            # database, never replacing an existing player or importing progress.
            if not self.accounts.has(form['u']) and self.accounts.register_uiid(form['u']):
                LOG.info('account_registered source=cached_client_uiid')
            LOG.info("entrance platform=%s version=%s protocol=%s locale=%s",form["p"],form["v"],form["c"],form["l"])
            sid, session = self.sessions.create(form["u"], form["l"],platform=form["p"])
            return plaintext_response(c.ObjArray([
                c.IntArray([14, self.config.version, 0]), c.String(sid), c.ByteArray(session.key),
                c.String(self.config.resource_url),
            ]))
        if set(form) != {"s", "e"}:
            raise ValueError("main requires s and e")
        session = self.sessions.get(form["s"])
        with session.lock:
            packet = request_packet(form["e"], session.key)
            digest = fingerprint(form)
            if session.last_sequence == packet.sequence:
                if digest != session.last_fingerprint:
                    raise ValueError("sequence reused with different request")
                return session.last_response
            LOG.info("packet type=%s sequence=%s", packet.type, packet.sequence)
            if packet.type & 0xff000000 == 0x08000000 and isinstance(packet.payloadInt, c.IntArray):
                LOG.info("cooking_input type=%s integers=%s", packet.type, packet.payloadInt.value)
            if packet.type in (10, 11):
                times, locale = packet.payloadInt, packet.payloadObj0
                if not isinstance(times, c.IntArray) or len(times.value) != 1 or not isinstance(locale, c.String) or locale.value != session.locale or not gameplay.null(packet.payloadObj1):
                    raise ValueError("initialization requires [client offset seconds] and matching locale")
                factory = tutorial.new_player if self.tutorial_test else test_player
                self.accounts.player(session.uiid, lambda uid: factory(uid, session.locale, self.config.definitions[session.locale]))
                def initialize(player, db):
                    from .restoration import restore_silver_conversion
                    restore_silver_conversion(player,db)
                    event_gameplay.sync(player,db,self.config.definitions[session.locale])
                    if self.tutorial_test:
                        tutorial.restore_comments(player,db,self.config.definitions[session.locale])
                    if self.local_cooking:
                        self.local_cooking.project(player, db, session)
                        if not self.tutorial_test or player.noticeFlagData.tutorialProgress >= 7:
                            self.enable_gameplay(player,db,self.config.definitions[session.locale])
                    else:
                        cooking.project_clocks(player, db)
                    if isinstance(player.wantedGudetamas, c.IntArray):
                        if player.wantedGudetamas.value != [0, 0, 0] or player.playerName != "Local Test":
                            raise ValueError("unknown legacy wantedGudetamas; manual evidence review required")
                        from .protocol import encode
                        db.execute("INSERT OR IGNORE INTO player_migrations VALUES (?, ?, ?, ?)", (player.uid, "phase2-empty-wanted-objects", encode(player), int(time.time())))
                        player.wantedGudetamas = c.ObjArray([c.UserWantedData(id=0, updateTime=0) for _ in range(3)])
                        LOG.info("player_migration uid=%s name=phase2-empty-wanted-objects", player.uid)
                    extra = gameplay.settle_touch(player, db, packet.payloadExtra, self.config.definitions[session.locale])
                    if self.tutorial_test:
                        tutorial.reset_touch_exercise_on_login(player,db)
                    if self.local_cooking:
                        extra.append(local_voices.helper_extra(player,self.config.definitions[session.locale]))
                    if self.tutorial_test:
                        if player.noticeFlagData.tutorialProgress>=7:
                            db.execute('CREATE TABLE IF NOT EXISTS local_login_days(uid INTEGER NOT NULL REFERENCES accounts(uid),day INTEGER NOT NULL,PRIMARY KEY(uid,day))')
                            db.execute('INSERT OR IGNORE INTO local_login_days VALUES(?,?)',(player.uid,(int(time.time())+player.timeZoneOffset//1000)//86400))
                        extra.extend(missions.extras(player,db,self.config.definitions[session.locale]))
                    extra.append(events.extra(db,self.config.definitions[session.locale]))
                    if self.local_cooking and player.noticeFlagData.tutorialProgress>=7:
                        from . import home_events
                        extra.extend(home_events.issue(player,db,self.config.definitions[session.locale],refresh=True))
                        from . import home_rewards
                        extra.extend(home_rewards.sync(player,db,self.config.definitions[session.locale]))
                    player.locale = session.locale
                    result = login_response(player, times.value[0], int(time.time()) - OFFSET_SECS)
                    # Encode while transaction is open: failure must roll back.
                    return main_response(result, packet.sequence, session.key, c.ObjArray(extra) if extra else None)
                response = self.accounts.transact(session.uiid, initialize)
                session.initialized = True
                session.last_sequence = packet.sequence
                session.last_fingerprint = digest
                session.last_response = response
                return response
            from .local_cooking import TYPES as LOCAL_TYPES
            if packet.type in event_gameplay.TYPES:
                result,extra=event_gameplay.process(self.accounts,packet,session,self.config.definitions[session.locale],request_fingerprint=digest)
                response=main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response=packet.sequence,digest,response
                return response
            if packet.type == home_items.USE:
                result,extra=home_items.process(self.accounts,packet,session,self.config.definitions[session.locale],request_fingerprint=digest)
                response=main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response=packet.sequence,digest,response
                return response
            cup_purchase = packet.type == shop.PURCHASE and isinstance(packet.payloadInt,c.IntArray) and len(packet.payloadInt.value)==3 and packet.payloadInt.value[1]==19
            if self.local_gacha and (packet.type in local_gacha.TYPES or cup_purchase):
                result,extra = self.local_gacha.process(self.accounts,packet,session,self.config.definitions[session.locale],request_fingerprint=digest)
                response = main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response = packet.sequence,digest,response
                return response
            if self.local_cooking and self.tutorial_test and packet.type in missions.TYPES and self.accounts.player(session.uiid,None).noticeFlagData.tutorialProgress >= 7:
                handler = missions.enter if packet.type == missions.ENTER else missions.rewards
                result,extra = handler(self.accounts,packet,session,self.config.definitions[session.locale])
                response = main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response = packet.sequence,digest,response
                return response
            if self.local_cooking and packet.type in local_voices.TYPES and (packet.type == local_voices.HELPER or not self.tutorial_test or self.accounts.player(session.uiid,None).noticeFlagData.tutorialProgress >= 7):
                result,extra = local_voices.process(self.accounts,packet,session,self.config.definitions[session.locale])
                response = main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response = packet.sequence,digest,response
                return response
            if session.initialized and packet.type in cooking_acceleration.TYPES and self.accounts.player(session.uiid,None).noticeFlagData.tutorialProgress>=7:
                result,extra=cooking_acceleration.process(self.accounts,packet,session,self.config.definitions[session.locale],
                    self.local_cooking,request_fingerprint=digest)
                response=main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response=packet.sequence,digest,response
                return response
            if packet.type in friends.TYPES:
                result,extra=friends.process(self.accounts,packet,session,self.config.definitions[session.locale],self.local_cooking,request_fingerprint=digest)
                response=main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response=packet.sequence,digest,response
                return response
            from . import home_rewards
            if packet.type in home_rewards.TYPES:
                result,extra=home_rewards.process(self.accounts,packet,session,self.config.definitions[session.locale],request_fingerprint=digest)
                response=main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response=packet.sequence,digest,response
                return response
            if packet.type in profile.TYPES:
                result,extra=profile.process(self.accounts,packet,session,self.config.definitions[session.locale])
                response=main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response=packet.sequence,digest,response
                return response
            if self.tutorial_test and packet.type in tutorial.TYPES:
                if packet.type == tutorial.VOICE_EVENT and session.platform == '0':
                    # Local timing guard, not an official protocol rule.
                    # HomeScene action 7 disables touch until this reply;
                    # GuideTalkPanel still needs two frames to reach event 18.
                    # Do not sleep inside the SQLite player transaction.
                    if self.accounts.player(session.uiid,None).noticeFlagData.tutorialProgress == 5:
                        time.sleep(0.5)
                        LOG.info('ios_tutorial_voice_guard delay_ms=500')
                result, extra = tutorial.process(self.accounts,packet,session,self.config.definitions[session.locale],on_complete=self.complete_tutorial)
                response = main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response = packet.sequence,digest,response
                return response
            if self.local_cooking and packet.type in shop.TYPES:
                handler = shop.change if packet.type == shop.CHANGE else shop.open_shop if packet.type == shop.OPEN else shop.picturebook_money if packet.type == shop.PICTUREBOOK_MONEY else shop.process
                kwargs = {'request_fingerprint':digest} if handler is shop.process else {}
                result, extra = handler(self.accounts, packet, session, self.config.definitions[session.locale], **kwargs)
                response = main_response(result, packet.sequence, session.key, extra)
                session.last_sequence, session.last_fingerprint, session.last_response = packet.sequence, digest, response
                return response
            if self.local_cooking and packet.type == recipe_progression.PURCHASE:
                result,extra = recipe_progression.purchase(self.accounts,packet,session,self.config.definitions[session.locale],self.config.definitions['ja'],self.local_cooking)
                response = main_response(result,packet.sequence,session.key,extra)
                session.last_sequence,session.last_fingerprint,session.last_response = packet.sequence,digest,response
                return response
            if self.local_cooking and packet.type in LOCAL_TYPES:
                result, extra = self.local_cooking.process(self.accounts, packet, session, self.config.definitions[session.locale])
                response = main_response(result, packet.sequence, session.key, extra)
                session.last_sequence, session.last_fingerprint, session.last_response = packet.sequence, digest, response
                return response
            if packet.type in gameplay.TYPES or (self.local_cooking and packet.type in gameplay.LOCAL_COLLECTION_TYPES):
                result, extra = gameplay.process(self.accounts, packet, session, self.config.definitions[session.locale], allow_local_actions=bool(self.local_cooking))
                response = main_response(result, packet.sequence, session.key, extra)
                if packet.type == 60:
                    session.entered_home = True
                session.last_sequence = packet.sequence
                session.last_fingerprint = digest
                session.last_response = response
                return response
            if packet.payloadExtra is not None and not isinstance(packet.payloadExtra, c.Null) and (not isinstance(packet.payloadExtra, c.ObjArray) or packet.payloadExtra.value):
                return reject("Gameplay extra payload is not implemented; no changes applied")
            result = self.dispatch(packet, session)
            response = main_response(result, packet.sequence, session.key)
            session.last_sequence = packet.sequence
            session.last_fingerprint = digest
            session.last_response = response
            return response

    def enable_gameplay(self,player,db,definition):
        """Shared audited unlock policy, in the caller's player transaction."""
        if self.tutorial_test:
            recipe_progression.refresh(player,db,definition,self.config.definitions['ja'])
        self.local_cooking.enable_candidates(player,db,definition)
        shop.enable_catalogue(player,db,definition)
        local_voices.restore_collected(player,db,definition)
        if self.tutorial_test:
            missions.sync(player,db,definition)
            self.local_gacha.sync(player,db,definition)
        guides.sync(player,db,definition)

    def complete_tutorial(self,player,db,definition):
        self.enable_gameplay(player,db,definition)
        # ResidentMenuUI_Gudetama.as:517-561 dispatches typed *Info objects;
        # send them in the completion frame before the HomeScene callback.
        extra = [c.ObjArray([c.String('feature:'),player.features]),
                 c.ObjArray([c.String('gudetama:'),c.ObjArray(list(player.gudetamaMap.values()))]),
                 c.ObjArray([c.String('kitchenware:'),c.ObjArray(list(player.kitchenwareMap.values()))]),
                 c.ObjArray([c.String('recipe_note:'),c.ObjArray(list(player.recipeNoteMap.values()))])]
        extra.extend(missions.extras(player,db,definition))
        for prefix,field,cls,updates,removes in (
            ('useful:','usefulMap',c.UsefulInfo,'updateUsefuls','removeUsefulIds'),
            ('utensil:','utensilMap',c.UtensilInfo,'updateUtensils','removeUtensilIds'),
            ('decoration:','decorationMap',c.DecorationInfo,'updateDecorations','removeDecorationIds'),
            ('avatar:','avatarMap',c.AvatarInfo,'updateAvatars','removeAvatarIds'),
            ('stamp:','stampMap',c.StampInfo,'updateStamps','removeStampIds')):
            info = cls(**{updates:c.ObjArray(list(getattr(player,field).values())),removes:c.IntArray([])})
            extra.append(c.ObjArray([c.String(prefix),info]))
        return extra

    def dispatch(self, packet, session):
        if not session.initialized:
            raise ValueError("initialize player before other main requests")
        if packet.type == 16777403:
            if not session.entered_home:
                raise ValueError("enter home state before HOME_GET_INFO")
            player = self.accounts.player(session.uiid, lambda uid: None)
            return home_response(player)
        if packet.type in (25, 119):
            if not isinstance(packet.payloadObj0, c.String):
                raise ValueError("notification/analytics request requires string")
            return c.ObjArray([])  # Local acknowledgement only; no external call.
        raise ValueError(f"packet {packet.type} unsupported; no fabricated success")

    def close(self):
        self.accounts.close()


class ThreadedServer(socketserver.ThreadingMixIn, WSGIServer):
    daemon_threads = True


class QuietHandler(WSGIRequestHandler):
    def log_message(self, fmt, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--public-origin", default="http://127.0.0.1:8080")
    parser.add_argument("--state", type=Path, default=tutorial.DESTINATION)
    parser.add_argument("--mode", choices=("unified", "historical", "local_compatible"), default="unified", help="legacy mode names are aliases for unified")
    parser.add_argument("--rules", type=Path)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    bind = ipaddress.ip_address(args.host)
    if not (bind.is_loopback or bind.is_private):
        parser.error("bind only to a local/private address")
    args.state.parent.mkdir(parents=True, exist_ok=True)
    log_path=args.log or args.state.parent / 'server.log'
    log_path.parent.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")])
    from .local_cooking_rules import Rules
    app = Application(args.public_origin, str(args.state), args.mode, Rules.load(args.rules) if args.rules else None)
    httpd = make_server(args.host, args.port, app, server_class=ThreadedServer, handler_class=QuietHandler)
    LOG.info("listening host=%s port=%s advertised_origin=%s", args.host, args.port, app.origin)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        app.close()


if __name__ == "__main__":
    main()
