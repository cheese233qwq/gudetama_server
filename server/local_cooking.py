"""Isolated NON-OFFICIAL cooking. Original Packet and response objects only."""
import argparse
import json
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from .library import ROOT,c
from .player import blank
from .protocol import encode,decode
from . import gameplay, local_voices, cooking_items, roulette_control, roulette_layout, event_gameplay
from .local_cooking_rules import Rules
from .paths import validate_save_path

LOG = logging.getLogger("gudetama.local")
START,CANCEL,ROULETTE,SPIN,COMPLETE,FINISH,PLACE = 134217909,134217910,134217923,134217963,134217912,134217942,134217954
UNLOCK = 134217925
TYPES = {START,CANCEL,ROULETTE,SPIN,COMPLETE,FINISH,PLACE,UNLOCK,249,cooking_items.SELECT}
ACTIVE = ("cooking","roulette","spinning","resolved")


def validate_database(path,rules):
    path = validate_save_path(path)
    db = sqlite3.connect(path.as_uri()+"?mode=ro",uri=True)
    try:
        row = db.execute("SELECT value FROM cooking_mode_metadata WHERE name='rules'").fetchone()
        if not row or not rules.extends(Rules(json.loads(row[0]))):
            raise ValueError("database not marked for these exact isolated rules")
    except sqlite3.Error as e:
        raise ValueError("unprepared compatible database") from e
    finally:
        db.close()
    if row[0] != rules.json:
        # Explicit local-mode startup may expand recipe/character allowlists.
        # Preserve player bytes, balances, run UUIDs and per-run rule snapshots.
        writable = sqlite3.connect(path)
        try:
            writable.execute('BEGIN IMMEDIATE')
            current = writable.execute("SELECT value FROM cooking_mode_metadata WHERE name='rules'").fetchone()[0]
            if not rules.extends(Rules(json.loads(current))):
                raise ValueError('concurrent/incompatible cooking policy change')
            writable.execute('CREATE TABLE IF NOT EXISTS cooking_rule_changes(change_id TEXT PRIMARY KEY,before_rules TEXT NOT NULL,after_rules TEXT NOT NULL,created_unix INTEGER NOT NULL)')
            if current != rules.json:
                writable.execute('INSERT INTO cooking_rule_changes VALUES(?,?,?,?)',(str(uuid.uuid4()),current,rules.json,int(time.time())))
                writable.execute("UPDATE cooking_mode_metadata SET value=? WHERE name='rules'",(rules.json,))
            writable.commit()
        except BaseException:
            writable.rollback()
            raise
        finally:
            writable.close()


def prepare(source,destination,uid,definition,rules):
    from .cooking_fixture import create
    report = create(source,destination,uid,definition)
    db = sqlite3.connect(destination)
    try:
        initialize_database(db,rules)
    finally:
        db.close()
    report.update(mode="local_compatible",rules=rules.settings,rules_sha256=rules.digest)
    return report


def initialize_database(db,rules):
    """Initialize a NEW isolated cooking database, without granting a fixture."""
    db.executescript("""
        CREATE TABLE cooking_mode_metadata(name TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE cooking_runs(run_id TEXT PRIMARY KEY,uid INTEGER NOT NULL REFERENCES accounts(uid),
          kitchen_type INTEGER NOT NULL,recipe_id INTEGER NOT NULL,gudetama_id INTEGER NOT NULL,
          started_unix INTEGER NOT NULL,deadline_unix INTEGER NOT NULL,cost INTEGER NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('cooking','roulette','spinning','resolved','claimed','cancelled')),
          percent INTEGER,result_type INTEGER,result_id INTEGER,reward INTEGER,rules_json TEXT NOT NULL,
          claimed_unix INTEGER,cancelled_unix INTEGER);
        CREATE UNIQUE INDEX cooking_active ON cooking_runs(uid,kitchen_type)
          WHERE status IN ('cooking','roulette','spinning','resolved');
        CREATE INDEX cooking_claimed_by_uid ON cooking_runs(uid) WHERE status='claimed';
        CREATE TABLE cooking_context(uid INTEGER PRIMARY KEY REFERENCES accounts(uid),run_id TEXT NOT NULL REFERENCES cooking_runs(run_id));
        """)
    db.execute("INSERT INTO cooking_mode_metadata VALUES('rules',?)",(rules.json,))
    db.commit()


class Engine:
    def __init__(self,rules,clock=None):
        self.rules,self.clock = rules,clock or time.time
        self.progression_sync = None
        self.candidate_policy = None

    def enable_collection(self,p,db,definition):
        """Compatibility entry point; collection now requires purchase."""
        from .shop import enable_catalogue
        enable_catalogue(p,db,definition)

    def enable_candidates(self,p,db,d):
        """Sync ordinary defaults; gacha appends require a genuine recipe award."""
        from . import cooking_progression
        cooking_progression.repair_appends(p,db,d)
        keep = cooking_progression.retained(p,db)
        pending = {}
        for rid in self.rules.settings['recipe_ids']:
            rd,note = d.recipeNoteMap.get(rid),p.recipeNoteMap.get(rid)
            if rd is None or rd.eventId or note is None or not (note.visible and note.available and note.purchased):
                continue
            kd = d.kitchenwareMap.get(rd.kitchenwareId)
            kitchen = p.kitchenwareMap.get(kd.type) if kd else None
            param = kitchen.paramMap.get(kd.id) if kitchen else None
            if not param or not param.available:
                continue
            for gid in rd.defaults.value+rd.appends.value:
                gd,owned = d.gudetamaMap.get(gid),p.gudetamaMap.get(gid)
                if (gid not in self.rules.settings['gudetama_ids'] or gd is None or gd.cost < 0
                        or gd.reward < 0 or gd.targetType not in (-1,0)):
                    continue
                # Absence is meaningful: the original client lists appends
                # only if their recipe exists in the player's map.
                if gid in rd.appends.value:continue
                self.rules.candidates(d,rd,gd)
                if owned is not None and not isinstance(owned,c.GudetamaData):
                    raise ValueError('unknown cooking candidate state')
                auto = gameplay.null(gd.requiredGudetamas) or not gd.requiredGudetamas.value
                policy = self.candidate_policy or d
                available,current,goal = cooking_progression.progress(p,db,policy.gudetamaMap[gid])
                available = available or gid in keep
                unlocked = bool(available and (auto or (owned and owned.unlocked)))
                if owned is None or (owned.available,owned.unlocked,owned.currentValue,owned.targetValue) != (available,unlocked,current,goal):
                    pending[gid] = owned,available,unlocked,current,goal
        if not pending:
            return
        before = encode(p)
        for gid,(owned,available,unlocked,current,goal) in pending.items():
            db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',
                       (p.uid,f'local-compatible-cooking-candidate-{gid}',before,int(self.clock())))
            if owned is None:
                owned = blank(c.GudetamaData,id=gid)
                p.gudetamaMap[gid] = owned
            owned.available,owned.unlocked = available,unlocked
            owned.currentValue,owned.targetValue = current,goal
            LOG.info('local_candidate_prepared uid=%s character=%s inventory_granted=0',p.uid,gid)
        db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))

    def row(self,db,run_id,uid):
        cur = db.execute("SELECT * FROM cooking_runs WHERE run_id=? AND uid=?",(run_id,uid))
        row = cur.fetchone()
        if not row:
            raise ValueError("no bound cooking run")
        r = dict(zip([x[0] for x in cur.description],row))
        if not self.rules.extends(Rules(json.loads(r["rules_json"]))):
            raise ValueError("run rules mismatch")
        return r

    def project(self,p,db,session=None):
        if db.execute("SELECT 1 FROM kitchen_clocks WHERE uid=?",(p.uid,)).fetchone():
            raise ValueError("synthetic historical clocks not compatible")
        rows = db.execute("SELECT run_id,kitchen_type,recipe_id,gudetama_id,deadline_unix FROM cooking_runs WHERE uid=? AND status IN ('cooking','roulette','spinning','resolved')",(p.uid,)).fetchall()
        active = {r[1]:r for r in rows}
        for kind,k in p.kitchenwareMap.items():
            r = active.get(kind)
            if r:
                if (k.recipeNoteId,k.gudetamaId) != (r[2],r[3]):
                    raise ValueError("run/player mismatch")
                # Local mode has no overcook penalty. -1 selects the original
                # completed UI without projecting hours of spoilage after logout.
                k.restTimeSecs = max(-1,min(2147483647,r[4]-int(self.clock())))
            elif k.recipeNoteId:
                raise ValueError("active kitchen without run")
        if active.keys()-p.kitchenwareMap.keys():
            raise ValueError("missing run kitchen")
        if session is not None and session.cooking_run_id is None:
            ctx = db.execute("SELECT run_id FROM cooking_context WHERE uid=?",(p.uid,)).fetchone()
            session.cooking_run_id = ctx[0] if ctx else None

    @staticmethod
    def idle(k):
        k.recipeNoteId = k.gudetamaId = k.restTimeSecs = 0
        k.assistUsefulIds = c.IntArray([])
        k.assistEncodedUids = c.IntArray([])

    def process(self,accounts,packet,session,d):
        if not session.initialized or not gameplay.null(packet.payloadObj0) or not gameplay.null(packet.payloadObj1):
            raise ValueError("invalid cooking session/object payload")
        bound = session.cooking_run_id
        audit = {}
        def op(p,db):
            nonlocal bound
            cooking_items.ensure(db)
            roulette_control.ensure(db)
            roulette_layout.ensure(db)
            extra = gameplay.settle_touch(p,db,packet.payloadExtra,d)
            self.project(p,db)
            balance_before = p.freeMoney
            typ,now = packet.type,int(self.clock())
            extra.extend(event_gameplay.sync(p,db,d,now))
            if typ==249 and self.progression_sync is not None:
                extra.extend(self.progression_sync(p,db,d))
                self.enable_candidates(p,db,d)
                extra.append(c.ObjArray([c.String('gudetama:'),c.ObjArray(list(p.gudetamaMap.values()))]))
            if typ in (SPIN,FINISH,PLACE) and not gameplay.null(packet.payloadInt):
                raise ValueError("unexpected integer payload")
            if typ == UNLOCK:
                gid = gameplay.integers(packet.payloadInt,1)[0]
                from .cooking_unlock import unlock
                result = unlock(p,db,d,self,gid)
            elif typ == START:
                rid,gid,target = gameplay.integers(packet.payloadInt,3)
                from . import tutorial
                if tutorial.enabled(db) and p.noticeFlagData.tutorialProgress < 7 and (p.noticeFlagData.tutorialProgress != 4 or (rid,gid,target) != (1,6,0)):
                    raise ValueError('tutorial first cooking requires stage 4 and recipe 1/character 6')
                k,cost,duration = event_gameplay.qualify(self,p,db,d,rid,gid,target,now)
                old = db.execute("SELECT run_id FROM cooking_runs WHERE uid=? AND kitchen_type=? AND status IN ('cooking','roulette','spinning','resolved')",(p.uid,k.type)).fetchone()
                if old:
                    r = self.row(db,old[0],p.uid)
                    if (r["recipe_id"],r["gudetama_id"]) != (rid,gid):
                        raise ValueError("kitchen occupied")
                    if r["status"] != "cooking":
                        raise ValueError("cannot start again after roulette preparation")
                    bound = old[0]
                else:
                    if p.freeMoney < cost:
                        raise ValueError("insufficient free GP; paid currency excluded")
                    bound = str(uuid.uuid4())
                    db.execute("INSERT INTO cooking_runs(run_id,uid,kitchen_type,recipe_id,gudetama_id,started_unix,deadline_unix,cost,status,rules_json) VALUES(?,?,?,?,?,?,?,?,?,?)",(bound,p.uid,k.type,rid,gid,now,now+duration,cost,"cooking",self.rules.json))
                    p.freeMoney -= cost
                    k.recipeNoteId,k.gudetamaId,k.restTimeSecs = rid,gid,duration
                db.execute("INSERT INTO cooking_context VALUES(?,?) ON CONFLICT(uid) DO UPDATE SET run_id=excluded.run_id",(p.uid,bound))
                event_gameplay.bind_run(db,d,rid,bound,now)
                result = k
            elif typ == 249:
                kind = gameplay.integers(packet.payloadInt,1)[0]
                if kind not in (0,1,2,3,4):
                    raise ValueError("unsupported kitchen")
                k = p.kitchenwareMap.get(kind)
                result = c.IntHashMap({d.kitchenwareMap[i].grade:c.Int(0) for i,x in k.paramMap.items() if x.available}) if k else c.IntHashMap({})
            else:
                if typ in (CANCEL,ROULETTE):
                    args = gameplay.integers(packet.payloadInt,1 if typ == CANCEL else 3)
                    if typ == ROULETTE and any(x not in (0,1) for x in args[1:]):
                        raise ValueError("invalid refresh flags")
                    if bound is None or self.row(db,bound,p.uid)["kitchen_type"] != args[0]:
                        old = db.execute("SELECT run_id FROM cooking_runs WHERE uid=? AND kitchen_type=? AND status IN ('cooking','roulette','spinning','resolved')",(p.uid,args[0])).fetchone()
                        if not old:
                            raise ValueError("no cooking run for kitchen")
                        bound = old[0]
                        db.execute("INSERT INTO cooking_context VALUES(?,?) ON CONFLICT(uid) DO UPDATE SET run_id=excluded.run_id",(p.uid,bound))
                r = self.row(db,bound,p.uid)
                k = p.kitchenwareMap[r["kitchen_type"]]
                if typ == CANCEL:
                    if r["status"] == "claimed":
                        raise ValueError("claimed run cannot be cancelled")
                    refund = 0
                    if r["status"] != "cancelled":
                        refund = r["cost"]
                        p.freeMoney += refund
                        self.idle(k)
                        db.execute("UPDATE cooking_runs SET status='cancelled',cancelled_unix=? WHERE run_id=?",(now,bound))
                    result = c.ObjArray([k,c.IntArray([refund])])
                elif typ == ROULETTE:
                    if r["status"] not in ACTIVE or now <= r["deadline_unix"]:
                        raise ValueError("cooking not ready")
                    gd,rd = d.gudetamaMap[r["gudetama_id"]],d.recipeNoteMap[r["recipe_id"]]
                    base=self.rules.candidates(d,rd,gd)
                    if r["percent"] is None:
                        base=roulette_layout.create(db,bound,base,self.rules.random_below,
                            spread=p.noticeFlagData.tutorialProgress>=7)
                        roll,outcome,gid,reward = self.rules.draw(d,r["recipe_id"],r["gudetama_id"],parts=base)
                        db.execute("UPDATE cooking_runs SET status='roulette',percent=?,result_type=?,result_id=?,reward=? WHERE run_id=?",(roll,outcome,gid,reward,bound))
                        r = self.row(db,bound,p.uid)
                    base=roulette_layout.saved(db,bound,base)
                    if r['status']=='roulette':
                        # A fresh dialog starts with no selected item IDs.
                        db.execute('DELETE FROM cooking_item_selections WHERE run_id=? AND consumed_unix IS NULL',(bound,))
                    else:
                        base=cooking_items.weights(base,cooking_items.selected(db,bound),d)
                    parts = c.ObjArray([c.PossibleRouletteParam(type=t,percent=w) for t,w in base])
                    manual=roulette_control.configure(db,p,r)
                    assistant_profiles={}
                    if not gameplay.null(k.assistEncodedUids) and k.assistEncodedUids.value:
                        from . import friends
                        for blob, in db.execute('SELECT player FROM accounts WHERE player IS NOT NULL'):
                            helper=decode(blob)
                            if helper.encodedUid in k.assistEncodedUids.value:
                                assistant_profiles[helper.encodedUid]=friends.user_profile(db,p,helper)
                    result = c.ObjArray([parts,c.IntArray([0,0,-1 if manual else r["percent"]]),c.Null(),c.Null(),c.IntHashMap(assistant_profiles)])
                elif typ == cooking_items.SELECT:
                    result=cooking_items.select(p,db,d,r,packet)
                elif typ == SPIN:
                    if r["status"] not in ("roulette","spinning","resolved"):
                        raise ValueError("roulette not prepared")
                    if r["status"] == "roulette":
                        cooking_items.validate(p,d,r,cooking_items.selected(db,bound))
                        db.execute("UPDATE cooking_runs SET status='spinning' WHERE run_id=?",(bound,))
                    result = c.IntArray([0])
                elif typ == COMPLETE:
                    percent = gameplay.integers(packet.payloadInt,1)[0]
                    roulette_control.validate(db,p,r,percent)
                    if r['status']=='spinning':
                        # Manual mode submits a stop angle, never a reward ID.
                        # Pin that angle once, then settle configured segments.
                        db.execute('UPDATE cooking_runs SET percent=? WHERE run_id=?',(percent,bound))
                        r['percent']=percent
                        cooking_items.consume(p,db,d,r,self.rules,now)
                        r=self.row(db,bound,p.uid)
                    db.execute("UPDATE cooking_runs SET status='resolved' WHERE run_id=?",(bound,))
                    result = c.IntArray([r["result_type"],0])
                    extra.extend(cooking_items.inventory_extra(p,db,bound))
                elif typ == FINISH:
                    if r["status"] not in ("resolved","claimed"):
                        raise ValueError("no resolved result")
                    award = 0
                    extra_character=extra_points=0
                    if r["status"] == "resolved":
                        extra_character,extra_points=event_gameplay.finish_bonus(p,db,bound,now)
                        award = r["reward"]
                        p.freeMoney += award
                        original = p.gudetamaMap[r["gudetama_id"]]
                        outcome = p.gudetamaMap.get(r["result_id"])
                        if outcome is None:
                            outcome = blank(c.GudetamaData,id=r["result_id"],available=True,unlocked=True)
                            p.gudetamaMap[outcome.id] = outcome
                        quantity=1+extra_character
                        if outcome.count+quantity > 999 or outcome.num+quantity > 32767:
                            raise ValueError("character inventory full")
                        outcome.count += quantity
                        outcome.num += quantity
                        outcome.available = outcome.unlocked = True
                        original.alreadyChallenge = True
                        if r["result_type"] == 1:
                            original.cookedHappening = True
                        elif r["result_type"] == 2:
                            original.cookedFailure = True
                        p.rank = max(p.rank,sum(x.count > 0 or x.num > 0 for x in p.gudetamaMap.values()))
                        local_voices.unlock_first(p,d,r["result_id"])
                        self.idle(k)
                        db.execute("UPDATE cooking_runs SET status='claimed',claimed_unix=? WHERE run_id=?",(now,bound))
                    result = c.ObjArray([k,c.ObjArray([p.gudetamaMap[r["gudetama_id"]],p.gudetamaMap[r["result_id"]]]),c.IntArray([award,extra_character,extra_points]),c.Null(),c.Null(),c.Null()])
                elif typ == PLACE:
                    if r["status"] != "claimed":
                        raise ValueError("result not claimed")
                    p.placedGudetamaId = r["result_id"]
                    result = c.ObjArray([])
                else:
                    raise ValueError("unsupported compatible operation")
            if p.freeMoney < 0 or p.freeMoney+p.chargeMoney > gameplay.MONEY_MAX:
                raise ValueError("GP overflow")
            if typ == FINISH and self.progression_sync is not None:
                extra.extend(self.progression_sync(p,db,d))
                self.enable_candidates(p,db,d)
                extra.append(c.ObjArray([c.String('gudetama:'),c.ObjArray(list(p.gudetamaMap.values()))]))
            if typ == FINISH:
                from .profile import sync_unlock
                if sync_unlock(p,db,d):extra.append(c.ObjArray([c.String('feature:'),p.features]))
            from . import guides
            extra.extend(guides.extras(p,db,d))
            db.execute("UPDATE player_state SET revision=revision+1 WHERE uid=?",(p.uid,))
            extra = [x for x in extra if not isinstance(x,c.String) or not x.value.startswith("touch_u:")]
            extra.append(c.String(f"touch_u:{p.freeMoney}"))
            encoded_extra = c.ObjArray(extra)
            encode(result)
            encode(encoded_extra)
            if bound:
                r = self.row(db,bound,p.uid)
                audit.update(uid=p.uid, status=r['status'], recipe=r['recipe_id'],
                             gudetama=r['gudetama_id'], deadline=r['deadline_unix'],
                             remaining=max(-1,r['deadline_unix']-now),
                             balance_before=balance_before, balance_after=p.freeMoney)
            return result,encoded_extra
        answer = accounts.transact(session.uiid,op)
        session.cooking_run_id = bound
        LOG.info("local_cooking_committed type=%s run_id=%s state=%s",packet.type,bound,json.dumps(audit,sort_keys=True))
        return answer


def main():
    parser = argparse.ArgumentParser(description="Create NEW isolated compatible kitchen fixture")
    parser.add_argument("--source",type=Path,default=ROOT / "server/state/accounts.sqlite3")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--uid",type=int,default=1)
    parser.add_argument("--rules",type=Path)
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    if manifest.exists() or not manifest.is_relative_to(ROOT / "docs/evidence"):
        parser.error("new manifest under docs/evidence required")
    from .configuration import Configuration
    rules = Rules.load(args.rules) if args.rules else Rules()
    report = prepare(args.source,args.output,args.uid,Configuration("http://127.0.0.1:8080/gde/static/").definitions["ja"],rules)
    manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Created isolated compatible fixture; no source currency grant.")


if __name__ == "__main__":
    main()
