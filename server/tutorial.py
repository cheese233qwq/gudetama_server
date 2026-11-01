"""Original tutorial packets with explicit local rules in a marked test DB."""
import argparse
from contextlib import closing
import json
import sqlite3
import re
import time
import logging
from pathlib import Path
from .library import ROOT,c
from .protocol import encode,decode
from .player import test_player,blank
from .state import Accounts
from . import gameplay

OPENING,TERMS,FIRST_LOGIN = 77,100663307,100663309
NAME = 220
STARTER_COMMENTS = (1,2,3,4,5)
GUIDE,NEXT,CHECK,NOTICE = 202,203,204,210
VOICE_EVENT,HEAVEN_EVENT,FINISHED,UNLOCK_VOICE,HURRY,PUSH = 16777421,16777422,16777423,16777410,134217911,38
TYPES = {OPENING,TERMS,FIRST_LOGIN,NAME,GUIDE,NEXT,CHECK,NOTICE,VOICE_EVENT,HEAVEN_EVENT,FINISHED,UNLOCK_VOICE,HURRY,PUSH}
DESTINATION = ROOT/'server/state/tutorial-compatible/accounts.sqlite3'
LOG = logging.getLogger('gudetama.local')


def enabled(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='tutorial_test_metadata'").fetchone():
        return False
    return db.execute("SELECT value FROM tutorial_test_metadata WHERE name='enabled'").fetchone() == ('1',)


def new_player(uid,locale,definition):
    # Minimal renderable local seed, NOT recovered official starter inventory.
    # Unlike the previous test fixture, no guide is marked done or skipped.
    player = test_player(uid,locale,definition)
    player.playerName = ''
    player.doneFirstLogin = False
    player.noticeFlagData = c.NoticeFlagData(noticeFlags=c.ByteArray(bytes(31)),tutorialProgress=0,bitFlags=0)
    player.commentList = comment_choices(definition)
    player.comment = 1
    return player


def comment_choices(definition):
    # Local starter selection from archived greetings, NOT a recovered official
    # starter entitlement list. No mission/rare comments are unlocked wholesale.
    if any(i not in definition.commentMap or not definition.commentMap[i].name for i in STARTER_COMMENTS):
        raise ValueError('configured starter comments missing')
    return [c.Int(i) for i in STARTER_COMMENTS]


def restore_comments(player,db,definition):
    # Repair only the empty comment list in the isolated tutorial database.
    # CommentSelectDialog.as:130-149 reads this UserData list, not all GameDef.
    if not enabled(db) or player.commentList:return
    db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',
               (player.uid,'tutorial-starter-comments-v1',encode(player),int(time.time())))
    player.commentList = comment_choices(definition)
    if player.comment == 0:player.comment = 1
    db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))


def prepare(source,destination=DESTINATION,uid=1):
    from .configuration import Configuration
    from .local_cooking import initialize_database
    from .local_cooking_rules import Rules
    source,destination = Path(source).resolve(),Path(destination).resolve()
    if (not destination.is_relative_to(ROOT/'server/state') or destination == source
            or destination == (ROOT/'server/state/accounts.sqlite3').resolve()):
        raise ValueError('separate tutorial test database required')
    if destination.exists():
        with closing(sqlite3.connect(destination.as_uri()+'?mode=ro',uri=True)) as db:
            if not enabled(db):raise ValueError('existing destination is not a tutorial database')
        return {'created':False,'state':str(destination),'progress_reset':False}
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as db:
        row = db.execute('SELECT uiid,player FROM accounts WHERE uid=?',(uid,)).fetchone()
        if not row or not row[1]:raise ValueError('source test account missing')
        previous = decode(row[1])
    definition = Configuration('http://127.0.0.1:8080/gde/static/').definitions[previous.locale]
    destination.parent.mkdir(parents=True,exist_ok=True)
    # Never copy the million-GP balance, rewards, inventory or completed guides.
    with destination.open('xb'):pass
    accounts = Accounts(destination)
    try:
        initialize_database(accounts.db,Rules.load(ROOT/'server/local_cooking_rules.json'))
        accounts.db.execute('CREATE TABLE tutorial_test_metadata(name TEXT PRIMARY KEY,value TEXT NOT NULL)')
        accounts.db.execute("INSERT INTO tutorial_test_metadata VALUES('enabled','1')")
        player = new_player(uid,previous.locale,definition)
        # Same device UIID for reversible database switching; no app-data wipe.
        # Preserve only the touch cursor to distinguish pending client batches.
        player.sendTouchCount = previous.sendTouchCount
        accounts.db.execute('INSERT INTO accounts(uid,uiid,player) VALUES(?,?,?)',(uid,row[0],encode(player)))
        accounts.db.commit()
    finally:
        accounts.close()
    return {'created':True,'uid':uid,'state':str(destination),'tutorialProgress':0,'GP':0}


def process(accounts,packet,session,definition,*,on_complete=None):
    if not session.initialized or packet.type not in TYPES:
        raise ValueError('initialize tutorial player first')
    typ = packet.type
    if not gameplay.null(packet.payloadObj1) or (typ not in (FIRST_LOGIN,NAME) and not gameplay.null(packet.payloadObj0)):
        raise ValueError('unexpected tutorial object payload')
    if typ in (OPENING,TERMS,FIRST_LOGIN,NAME,VOICE_EVENT,HEAVEN_EVENT,FINISHED) and not gameplay.null(packet.payloadInt):
        raise ValueError('tutorial operation requires no integer payload')
    def operation(player,db):
        if not enabled(db):raise ValueError('separate tutorial database required')
        schema(db)
        extra = gameplay.settle_touch(player,db,packet.payloadExtra,definition)
        progress = player.noticeFlagData.tutorialProgress
        if typ in (OPENING,TERMS) and (player.doneFirstLogin or progress not in (0,1)):
            raise ValueError('not in opening tutorial stage')
        if typ == OPENING:
            db.execute('UPDATE player_state SET scene=? WHERE uid=?',(OPENING,player.uid))
            # OpeningScene AreaSelectDialog.as:667-683 supports null => all
            # configured rule.gudetamaTeamIds indices. Local region restriction
            # policy: none. Official regional restrictions are UNKNOWN.
            result = c.Null()
        elif typ == TERMS:
            if player.noticeFlagData.tutorialProgress == 0:
                player.noticeFlagData.tutorialProgress = 1
                db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
            # OpeningScene.as:205 callback expects Array and ignores its contents.
            result = c.ObjArray([])
        elif typ == NAME:
            # NameInputDialog.as:135-190: opening name check is a separate
            # request before FirstLoginInfo, callback consumes [[code],name].
            if player.doneFirstLogin or progress != 1:raise ValueError('name draft requires opening stage 1')
            if not isinstance(packet.payloadObj0,c.String):raise ValueError('name requires String payload')
            name = packet.payloadObj0.value
            code = name_status(name)
            if code == 0:player.playerName = name  # Local persisted opening draft.
            result = c.ObjArray([c.IntArray([code]),c.String(name)])
        elif typ == FIRST_LOGIN:
            info = packet.payloadObj0
            if not isinstance(info,c.FirstLoginInfo):raise ValueError('FirstLoginInfo required')
            if name_status(info.name) != 0 or info.locale != player.locale or info.deckIndex != -1 or info.avatar not in (0,1,2) or info.gender != 0 or not 0 <= info.area < len(definition.rule.gudetamaTeamIds.value) or (info.comment != 0 and info.comment not in definition.commentMap):
                raise ValueError('invalid first-login profile')
            if player.doneFirstLogin:
                row = db.execute('SELECT request FROM tutorial_profile WHERE uid=?',(player.uid,)).fetchone()
                if not row or row[0] != encode(info):raise ValueError('first-login profile already committed')
            else:
                if progress != 1:raise ValueError('agree to terms first')
                player.playerName,player.gender,player.area,player.comment = info.name,info.gender,info.area,info.comment
                # Local starter-avatar mapping, official server mapping UNKNOWN.
                player.avatar = info.avatar+1
                if player.avatar not in definition.avatarMap:raise ValueError('configured starter avatar missing')
                player.avatarMap[player.avatar] = c.AvatarData(id=player.avatar,acquired=True,available=True)
                player.timeZoneOffset = timezone_offset(info.timeZone)
                starter(player,definition)
                player.doneFirstLogin = True
                player.noticeFlagData.tutorialProgress = 2
                db.execute('INSERT INTO tutorial_profile VALUES(?,?)',(player.uid,encode(info)))
            result = c.ObjArray([player])
        elif typ in (GUIDE,NEXT,CHECK):
            requested = gameplay.integers(packet.payloadInt,1)[0]
            if not player.doneFirstLogin or not 2 <= progress <= 6:raise ValueError('not in home tutorial')
            if typ == GUIDE:
                if requested != progress:raise ValueError('guide must resume current progress')
            elif typ == NEXT:
                if requested not in (progress,progress+1) or requested > 6:raise ValueError('cannot skip tutorial steps')
                if requested == 5:raise ValueError('first cooking advances through CHECK after claiming')
                if requested == 6:
                    if not db.execute("SELECT 1 FROM tutorial_events WHERE uid=? AND kind='heaven' AND received=1",(player.uid,)).fetchone():raise ValueError('finish the heaven exercise first')
                player.noticeFlagData.tutorialProgress = requested
            else:
                if requested == 4 and progress == 4:
                    if not db.execute("SELECT 1 FROM cooking_runs WHERE uid=? AND recipe_id=1 AND status='claimed'",(player.uid,)).fetchone():raise ValueError('claim first cooking result before continuing')
                    player.noticeFlagData.tutorialProgress = 5
                elif not (requested == 4 and progress == 5):raise ValueError('invalid cooking tutorial checkpoint')
            result = definition.guideTalkTable[requested]
            extra.append(player.noticeFlagData)
        elif typ in (VOICE_EVENT,HEAVEN_EVENT):
            if progress != 5:raise ValueError('touch exercises require tutorial stage 5')
            kind = 'voice' if typ == VOICE_EVENT else 'heaven'
            if kind == 'heaven' and not db.execute("SELECT 1 FROM tutorial_events WHERE uid=? AND kind='voice' AND used>=1",(player.uid,)).fetchone():raise ValueError('complete voice touch first')
            # Non-official deterministic exercise: next eligible tap plays the
            # configured first voice; heaven spawns 20 existing animation items.
            gd = definition.gudetamaMap[player.placedGudetamaId]
            event = c.TouchEventParam(touchNum=1,event=256 if kind == 'voice' else 2048,voice=gd.voices.value[0] if kind == 'voice' else 0,paramByte=0 if kind == 'voice' else 20)
            db.execute('INSERT OR IGNORE INTO tutorial_events VALUES(?,?,?,?,0,0)',(player.uid,kind,encode(event),20 if kind == 'heaven' else 1))
            stored = db.execute('SELECT event FROM tutorial_events WHERE uid=? AND kind=?',(player.uid,kind)).fetchone()[0]
            player.touchInfo = c.TouchInfo(params=c.ObjArray([decode(stored)]),bonusRange=c.IntArray([]))
            result = player.touchInfo
        elif typ == UNLOCK_VOICE:
            if progress != 5 or gameplay.integers(packet.payloadInt,1) != [-1]:raise ValueError('unsupported tutorial voice selector')
            row = db.execute("SELECT 1 FROM tutorial_events WHERE uid=? AND kind='voice'",(player.uid,)).fetchone()
            if not row:raise ValueError('voice event not issued')
            from .local_voices import eligible
            if not eligible(player,definition,player.placedGudetamaId):raise ValueError('voice asset unavailable')
            player.gudetamaMap[player.placedGudetamaId].unlockedVoiceIndex |= 1
            result = c.ObjArray([c.Null()])
        elif typ == HURRY:
            kind,metals,paid = gameplay.integers(packet.payloadInt,3)
            if progress != 4 or kind != 0 or paid != 0 or metals < -1:raise ValueError('only free first-cooking tutorial acceleration supported')
            row = db.execute("SELECT run_id,deadline_unix FROM cooking_runs WHERE uid=? AND kitchen_type=0 AND recipe_id=1 AND gudetama_id=6 AND status='cooking'",(player.uid,)).fetchone()
            if not row:raise ValueError('no active tutorial cooking')
            rest = max(0,row[1]-int(time.time()))
            unit = definition.rule.hurryUpReduceMinutesPerMetal*60
            previous = db.execute('SELECT metals FROM tutorial_hurry WHERE run_id=?',(row[0],)).fetchone()
            if unit <= 0 or (metals != (rest+unit-1)//unit-1 and (not previous or metals != previous[0])):raise ValueError('invalid tutorial acceleration amount')
            deadline = min(row[1],int(time.time())-1)
            db.execute('INSERT OR IGNORE INTO tutorial_hurry VALUES(?,?)',(row[0],metals))
            db.execute('UPDATE cooking_runs SET deadline_unix=? WHERE run_id=?',(deadline,row[0]))
            player.kitchenwareMap[0].restTimeSecs = -1
            result = c.ObjArray([player.kitchenwareMap[0],c.IntArray([0])])
        elif typ == PUSH:
            flags = gameplay.integers(packet.payloadInt,1)[0]
            if progress < 6 or flags < 0 or flags > 63:raise ValueError('invalid push permission flags')
            player.pushFlags = flags
            result = c.Int(flags)
        elif typ == NOTICE:
            from . import guides
            index = gameplay.integers(packet.payloadInt,1)[0]
            flags = bytearray(player.noticeFlagData.noticeFlags.value)
            if not 0 <= index < len(flags) or progress < 7 or flags[index] & 15 not in (1,2):raise ValueError('notice has not been enabled')
            if index not in guides.SUPPORTED and flags[index] & 15 != 2:raise ValueError('guide business dependency not restored')
            flags[index] = (flags[index] & 240) | 2
            player.noticeFlagData.noticeFlags = c.ByteArray(bytes(flags))
            if index == 2:
                from . import shop
                shop.enable_catalogue(player,db,definition)
                extra.extend(shop.catalogue_extras(player))
            guides.sync(player,db,definition)
            result = c.Null()
            extra.append(player.noticeFlagData)
        elif typ == FINISHED:
            if progress not in (6,7):raise ValueError('complete all tutorial stages first')
            player.noticeFlagData.tutorialProgress = 7
            player.touchInfo = c.TouchInfo(params=c.ObjArray([]),bonusRange=c.IntArray([]))
            if on_complete is not None:
                extra.extend(on_complete(player,db,definition))
            from . import guides
            guides.sync(player,db,definition)
            result = c.Null()
            extra.append(player.noticeFlagData)
        else:raise ValueError('unknown tutorial operation')
        if typ not in (OPENING,TERMS):
            db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
        encode(result)
        extras = c.ObjArray(extra) if extra else None
        if extras is not None:encode(extras)
        return result,extras
    result = accounts.transact(session.uiid,operation)
    LOG.info('tutorial_committed packet=%s',typ)
    return result


def schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS tutorial_profile(uid INTEGER PRIMARY KEY,request BLOB NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS tutorial_events(uid INTEGER NOT NULL,kind TEXT NOT NULL,event BLOB NOT NULL,budget INTEGER NOT NULL,used INTEGER NOT NULL,received INTEGER NOT NULL,PRIMARY KEY(uid,kind))')
    db.execute('CREATE TABLE IF NOT EXISTS tutorial_hurry(run_id TEXT PRIMARY KEY,metals INTEGER NOT NULL)')


def name_status(name):
    # QnqServletConstants.as:10-12,210-218: length 2..8 and result codes.
    # AS String.length counts UTF-16 units. Official profanity rules UNKNOWN;
    # local validation rejects blank/control characters, has no invented blacklist.
    length = len(name.encode('utf-16-be'))//2
    if length < 2:return 3
    if length > 8:return 2
    if not name.strip() or any(ord(ch)<32 or ord(ch)==127 for ch in name):return 1
    return 0


def timezone_offset(zone):
    # Client TimeZoneUtil.as:25-104,302-311 supplies these fixed-offset labels.
    names = ['Etc/GMT+12','Etc/GMT+11','HST','AST','PST','MST','CST','EST','PRT','AGT','Etc/GMT+2','Etc/GMT+1','UTC','CET','EET','EAT','NET','PLT','BST','VST','CTT','JST','AET','SST','NST','MIT']
    # UserDataWrapper.as:493/502 forwards this to Date.setTime: milliseconds.
    if zone in names:return (names.index(zone)-12)*3600000
    match = re.fullmatch(r'GMT([+-])(\d{2})(\d{2})',zone)
    if not match or int(match[2]) > 14 or int(match[3]) > 59:raise ValueError('unknown client timezone')
    return (1 if match[1] == '+' else -1)*(int(match[2])*3600000+int(match[3])*60000)


def starter(player,d):
    # Explicit local tutorial seed; official initial inventory is UNKNOWN.
    kd,rd = d.kitchenwareMap[1],d.recipeNoteMap[1]
    if (kd.type,rd.kitchenwareId) != (0,1) or 6 not in rd.defaults.value:raise ValueError('tutorial configuration mismatch')
    player.kitchenwareMap[0] = blank(c.KitchenwareData,type=0,paramMap={1:c.KitchenwareParam(id=1,available=True)},assistUsefulIds=c.IntArray([]),assistEncodedUids=c.IntArray([]))
    player.recipeNoteMap[1] = c.RecipeNoteData(id=1,visible=True,available=True,purchased=True,targetValue=0,currentValue=0)
    for gid in rd.defaults.value:
        if gid not in player.gudetamaMap:player.gudetamaMap[gid] = blank(c.GudetamaData,id=gid,available=True,unlocked=True)
    player.features = c.IntArray([])  # Collection is purchased during shop notice 2.


def settle_touch(player,db,extras,d):
    """Tutorial-only capped event rewards, committed with the existing receipts."""
    if gameplay.null(extras) or (isinstance(extras,c.ObjArray) and not extras.value):return []
    schema(db)
    if not isinstance(extras,c.ObjArray) or any(not isinstance(x,c.String) for x in extras.value):raise ValueError('invalid tutorial extras')
    texts = [x.value for x in extras.value]
    touches = [x for x in texts if x.startswith('send_touch:')]
    heavens = [x for x in texts if x.startswith('send_heaven:')]
    if len(touches)>1 or len(heavens)>1 or len(texts)!=len(touches)+len(heavens):raise ValueError('unsupported tutorial extra')
    heaven = db.execute("SELECT event,budget,used FROM tutorial_events WHERE uid=? AND kind='heaven'",(player.uid,)).fetchone()
    if heavens:
        if not heaven or heavens[0] != 'send_heaven:'+event_string(decode(heaven[0])):raise ValueError('heaven event was not issued by server')
        db.execute("UPDATE tutorial_events SET received=1 WHERE uid=? AND kind='heaven'",(player.uid,))
    if not touches:return []
    text = touches[0]
    match = re.fullmatch(r'send_touch:([0-9]+(?:,[0-9]+)*)-([0-9]+)-([0-9]+)-([01])',text)
    if not match:raise ValueError('invalid tutorial touch batch')
    counts = [int(x) for x in match[1].split(',')]
    counts += [0]*(9-len(counts))
    # LocalData.as:453 sets isTouchStarted, but its read/write never persists
    # that flag. A saved pending batch legitimately arrives with started=0.
    if len(counts)!=9 or any(counts[i] for i in (2,3,4,5,6,7)) or (int(match[2]) and player.noticeFlagData.tutorialProgress<7) or not sum(counts) or max(counts)>2147483647:
        LOG.warning('tutorial_touch_rejected uid=%s counts=%s bonus=%s started=%s',player.uid,counts,match[2],match[4])
        raise ValueError('unsupported tutorial touch counts')
    baseline = int(match[3])
    receipt = db.execute('SELECT request FROM touch_receipts WHERE uid=? AND baseline=?',(player.uid,baseline)).fetchone()
    if receipt:
        if receipt[0]!=text:raise ValueError('touch baseline already used')
    else:
        if baseline != player.sendTouchCount:raise ValueError('stale/future tutorial touch baseline')
        credit = [counts[0],0,0,0,0,0,0,0,0]
        for kind,index in (('voice',1),('heaven',8)):
            if counts[index]:
                event = db.execute('SELECT budget,used,received FROM tutorial_events WHERE uid=? AND kind=?',(player.uid,kind)).fetchone()
                if not event or (kind=='heaven' and not event[2]) or counts[index]>event[0]:raise ValueError('unissued/excess event reward')
                credit[index] = min(counts[index],event[0]-event[1])
                db.execute('UPDATE tutorial_events SET used=used+? WHERE uid=? AND kind=?',(credit[index],player.uid,kind))
        from . import home_items
        bonus = home_items.bonus_credit(player,db,counts,int(match[2]))
        reward = (sum(n*w for n,w in zip(credit,d.rule.touchRewards.value)) + bonus*d.rule.touchRewards.value[0])*player.rank
        if player.freeMoney+player.chargeMoney+reward>gameplay.MONEY_MAX or baseline+sum(counts)>2147483647:raise ValueError('tutorial reward overflow')
        player.freeMoney += reward
        player.sendTouchCount += sum(counts)
        db.execute('INSERT INTO touch_receipts VALUES(?,?,?,?,?)',(player.uid,baseline,text,reward,int(time.time())))
        db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
    return [c.String(f'touch_u:{player.freeMoney}'),c.String(f'touch_count:{player.sendTouchCount}')]


def event_string(event):
    return f'{event.touchNum},{event.event},{event.voice},{event.paramByte}'


def rearm_voice_exercise(player,db,packet):
    """Replay the local exercise until the client requests the heaven stage.

    GameDef guide 5 issues action 7 before words 6..9 and interruption 11.
    GuideTalkPanel.as:488-500 ignores resume before interruption. An early tap
    otherwise consumes the sole event and leaves the later interruption stuck.
    HomeScene.as:2090-2100 flushes exhausted events through GENERAL_EXTRA=190;
    its response can replace TouchInfo (ResidentMenuUI_Gudetama.as:503-506).
    Event rewards remain capped by tutorial_events.used, independently of replay.
    """
    if packet.type != 190 or player.noticeFlagData.tutorialProgress != 5 or not enabled(db):return []
    params = player.touchInfo.params.value
    if len(params)!=1 or params[0].event!=256:return []
    issued = db.execute("SELECT event FROM tutorial_events WHERE uid=? AND kind='voice'",(player.uid,)).fetchone()
    if not issued:return []
    player.touchInfo = c.TouchInfo(params=c.ObjArray([decode(issued[0])]),bonusRange=c.IntArray([]))
    return [c.ObjArray([c.String('touch_info:'),player.touchInfo])]


def reset_touch_exercise_on_login(player, db):
    # The client restarts guide 5 from its first sentence (no sentence cursor
    # in the protocol). Never restore a still-armed event ahead of action 7.
    # Keep tutorial_events and all reward receipts; replay cannot mint rewards.
    if enabled(db) and player.noticeFlagData.tutorialProgress == 5:
        player.touchInfo = c.TouchInfo(params=c.ObjArray([]),bonusRange=c.IntArray([]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=ROOT/'server/state/phase5-compatible/accounts.sqlite3')
    parser.add_argument('--output',type=Path,default=DESTINATION)
    parser.add_argument('--uid',type=int,default=1)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source,args.output,args.uid)))
