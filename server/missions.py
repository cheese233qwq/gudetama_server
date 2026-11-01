"""Normal challenges and their presents in the isolated local tutorial database.

GameDef supplies IDs/counter types/localized titles; goals and preview rewards
below are from Wiki Challenges. Param defaults/activation/key mapping and
counter evaluation are explicit local rules, not recovered server algorithms.
Reward delivery uses the original mission notice -> present box protocol.
"""
import logging
import time
from .library import c
from .protocol import encode, decode
from . import gameplay

LOG = logging.getLogger('gudetama.local')
ENTER = 144  # QnqServletConstants.as:416; HomeScene.as:2764-2775.
CHECK, MAILS, RECEIVE, BULK = 159, 66, 72, 73
TYPES = {ENTER, CHECK, MAILS, RECEIVE, BULK}
# Legacy three-spec reference; the active full catalogue is mission_catalogue.
# mission_id, displayed number, goal, title key, preview reward, counter type
SPECS = (
    (1, 1, 3, 'mission.title.rank', (0, 0, 5000), 2),
    (2, 2, 10, 'mission.title.rank', (8, 11, 3), 2),
    (220, 103, 30, 'mission.title.gude.make.total', (8, 12, 1), 136),
)


def enabled(db):
    from .tutorial import enabled as tutorial_enabled
    return tutorial_enabled(db)


def ensure_box(db):
    db.execute('''CREATE TABLE IF NOT EXISTS normal_mission_presents(
        mail_key INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER NOT NULL REFERENCES accounts(uid), mission_id INTEGER NOT NULL,
        mail BLOB NOT NULL, created_unix INTEGER NOT NULL, claimed_unix INTEGER,
        UNIQUE(uid,mission_id))''')
    db.execute('CREATE INDEX IF NOT EXISTS mission_unclaimed_by_uid ON normal_mission_presents(uid,mail_key) WHERE claimed_unix IS NULL')


def sync(player, db, definition, *, now=None):
    if not enabled(db) or player.noticeFlagData.tutorialProgress < 7:
        return []
    db.execute('''CREATE TABLE IF NOT EXISTS normal_mission_progress(
        uid INTEGER NOT NULL REFERENCES accounts(uid), mission_id INTEGER NOT NULL,
        mission_key INTEGER NOT NULL, param BLOB NOT NULL,
        current_value INTEGER NOT NULL CHECK(current_value BETWEEN 0 AND 32767),
        updated_unix INTEGER NOT NULL, policy TEXT NOT NULL,
        PRIMARY KEY(uid,mission_id), UNIQUE(uid,mission_key))''')
    ensure_box(db)
    from . import mission_catalogue
    values = mission_catalogue.counters(player,db,definition)
    features = [x.value if isinstance(x,c.Int) else x for x in player.features.value]
    if not {8,11}<=set(features):
        db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',
                   (player.uid,'local-normal-missions-v1',encode(player),int(time.time())))
        player.features = c.IntArray(sorted(set(features)|{8,11}))
        db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
    result = []
    for spec in mission_catalogue.catalogue(definition):
        ident,number,goal,title,reward,counter=(spec[k] for k in ('id','number','goal','title','reward','counter'))
        md = definition.missionMap.get(ident)
        if md is None or (md.number,md.eventId,md.counterType) != (number,0,counter):
            raise ValueError('normal mission definition mismatch')
        if title not in definition.dict.uitext:
            raise ValueError('normal mission title missing')
        if reward[0] == 8 and reward[1] not in definition.usefulMap:
            raise ValueError('normal mission preview item missing')
        row = db.execute('SELECT mission_key,param,current_value FROM normal_mission_progress WHERE uid=? AND mission_id=?',
                         (player.uid,ident)).fetchone()
        # Local stable key = archived ID, scoped to this account. No new Packet
        # field is added. category/guide=0, no expiry, cumulative counter.
        param = c.MissionParam(number=number,type=1,category=0,guide=0,
            goalValue=goal,finishSecs=-1,targetDescKey='',titleKey=title,
            nextTitleKey='',rewards=c.ObjArray([c.ItemParam(kind=reward[0],id=reward[1],num=reward[2])]),
            titleParam=mission_catalogue.title_param(spec),counterType=counter)
        value=values[spec['kind']]
        current = min(32767,value[spec['arg']] if isinstance(value,dict) else value)
        if row:
            if row[0] != ident or row[1] != encode(param):
                raise ValueError('unknown existing normal mission policy')
            current = max(row[2],current)  # Local cumulative progress never regresses.
            if current != row[2]:
                db.execute('UPDATE normal_mission_progress SET current_value=?,updated_unix=? WHERE uid=? AND mission_id=?',
                           (current,int(time.time()),player.uid,ident))
        else:
            db.execute('INSERT INTO normal_mission_progress VALUES(?,?,?,?,?,?,?)',
                       (player.uid,ident,ident,encode(param),current,int(time.time()),'local-normal-v1'))
        result.append(c.MissionData(key=ident,param=param,currentValue=current,id=ident))
    from . import daily_missions
    daily,_=daily_missions.sync(player,db,definition,now=now)
    return result+daily


def extras(player,db,definition):
    now=int(time.time())
    missions = sync(player,db,definition,now=now)
    if not missions:return []
    # ResidentMenuUI_Gudetama.as:497-501; UserDataWrapper.as:2363-2452.
    # MissionScene subtracts TimeZoneUtil.epochMillisToOffsetSecs(), so the
    # fourth slot is an absolute deadline in the client's 2010 epoch.
    daily=[m.key for m in missions if m.id>=1000]
    from .daily_missions import day_window
    deadline=day_window(now)[2]-1262271600
    return [c.ObjArray([c.String('m_mod:'),c.ObjArray(missions),c.IntArray(daily),c.IntArray([deadline])]),
            c.String(f'prs:{len(pending(player,db))},0')]


def pending(player,db):
    return [decode(row[0]) for row in db.execute(
        'SELECT mail FROM normal_mission_presents WHERE uid=? AND claimed_unix IS NULL ORDER BY mail_key',
        (player.uid,))]


def deliver(player,db,mail,definition):
    """Credit once inside the player transaction; client addItems consumes deltas.

    InfoListDialog.as:468-478 / :552-561; UserDataWrapper.as:2004-2057,3905-3915.
    Overflow keeps the present unclaimed, never silently truncates a reward.
    """
    item = mail.item
    param = item
    if item.num <= 0:raise ValueError('invalid BOX quantity')
    if item.kind in (0,1):
        free,paid=('freeMoney','chargeMoney') if item.kind==0 else ('freeMetal','chargeMetal')
        if getattr(player,free)+getattr(player,paid)+item.num > gameplay.MONEY_MAX:
            raise ValueError('mission GP reward exceeds balance limit')
        setattr(player,free,getattr(player,free)+item.num)
    elif item.kind == 8:
        spec = definition.usefulMap.get(item.id)
        owned = player.usefulMap.get(item.id)
        if spec is None:
            raise ValueError('mission reward inventory missing')
        if owned is None:
            owned=c.UsefulData(id=item.id,num=0,available=False,nextAvailablePurchaseSec=0)
            player.usefulMap[item.id]=owned
        if owned.num+item.num > spec.possessionLimit:
            raise ValueError('mission reward inventory limit exceeded')
        owned.num += item.num
    elif item.kind in (6,7,9,11):
        from .local_gacha import Engine
        param = Engine().award(player,definition,item)
    elif item.kind == 4:
        from .player import blank
        kd=definition.kitchenwareMap.get(item.id)
        if kd is None:raise ValueError('unknown challenge kitchenware')
        param=player.kitchenwareMap.get(kd.type)
        if param is None:
            param=blank(c.KitchenwareData,type=kd.type,paramMap={},assistUsefulIds=c.IntArray([]),assistEncodedUids=c.IntArray([]))
            player.kitchenwareMap[kd.type]=param
        param.paramMap[kd.id]=c.KitchenwareParam(id=kd.id,available=True)
    elif item.kind == 12:
        from .player import blank
        if item.id not in definition.avatarMap:raise ValueError('unknown challenge avatar')
        param=player.avatarMap.get(item.id)
        if param is None:
            param=blank(c.AvatarData,id=item.id,available=True,acquired=True)
            player.avatarMap[item.id]=param
        param.available=param.acquired=True
    elif item.kind == 13:
        if item.id not in definition.commentMap:raise ValueError('unknown event comment reward')
        if item.id not in [x.value for x in player.commentList]:player.commentList.append(c.Int(item.id))
    elif item.kind == 19:
        if item.id not in definition.cupGachaMap or item.num!=1:raise ValueError('unsupported event cup reward')
        slots=player.cupGachaData.cupGachaIds.value
        if 0 not in slots:raise ValueError('cup slots full; reward remains in BOX')
        slot=slots.index(0);slots[slot]=item.id
        import uuid
        from .local_gacha import Engine
        Engine().sync(player,db,definition)
        db.execute('INSERT INTO local_cup_runs VALUES(?,?,?,?,NULL,NULL)',(str(uuid.uuid4()),player.uid,slot,item.id))
        param=c.ObjArray([c.Int(slot),c.IntArray([item.id])])
    else:
        raise ValueError('unsupported mission reward kind')
    updated = db.execute('UPDATE normal_mission_presents SET claimed_unix=? WHERE uid=? AND mail_key=? AND claimed_unix IS NULL',
                        (int(time.time()),player.uid,mail.uniqueKey))
    if updated.rowcount != 1:raise ValueError('mission present already claimed')
    db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
    return item,param


def rewards(accounts,packet,session,definition):
    if not session.initialized or packet.type not in TYPES-{ENTER} or any(
            not gameplay.null(x) for x in (packet.payloadObj0,packet.payloadObj1)):
        raise ValueError('invalid mission reward request')
    key = gameplay.integers(packet.payloadInt,1)[0] if packet.type == RECEIVE else None
    if packet.type != RECEIVE and not gameplay.null(packet.payloadInt):
        raise ValueError('mission reward query has no integer payload')
    def operation(player,db):
        if not enabled(db) or player.noticeFlagData.tutorialProgress < 7:
            raise ValueError('mission rewards require isolated completed tutorial account')
        extra = gameplay.settle_touch(player,db,packet.payloadExtra,definition)
        from . import event_gameplay
        extra.extend(event_gameplay.sync(player,db,definition))
        rows = sync(player,db,definition)
        if packet.type == CHECK:
            cleared = []
            for mission in rows:
                if mission.id==1006:
                    mission.currentValue=db.execute('SELECT count(*) FROM normal_mission_presents WHERE uid=? AND mission_id BETWEEN ? AND ?',(player.uid,mission.key-4,mission.key-1)).fetchone()[0]
                    db.execute('UPDATE normal_mission_progress SET current_value=? WHERE uid=? AND mission_id=?',(mission.currentValue,player.uid,mission.id))
                if mission.currentValue < mission.param.goalValue:continue
                mail_mission_id=mission.key if mission.id>=1000 else mission.id
                if db.execute('SELECT 1 FROM normal_mission_presents WHERE uid=? AND mission_id=?',
                              (player.uid,mail_mission_id)).fetchone():continue
                now = int(time.time())
                cur = db.execute('INSERT INTO normal_mission_presents(uid,mission_id,mail,created_unix) VALUES(?,?,?,?)',
                                 (player.uid,mail_mission_id,b'',now))
                if cur.lastrowid > 2147483647:raise ValueError('mission mail key overflow')
                title = definition.dict.uitext[mission.param.titleKey].value.replace('<GOAL_VALUE>',str(mission.param.goalValue))
                if isinstance(mission.param.titleParam,c.ObjArray):
                    condition,value=mission.param.titleParam.value
                    value=value.value
                    names={'UseUsefulItem':definition.usefulMap,'GudetamaTarget':definition.gudetamaMap}
                    replacement=names[condition.value][value].name if condition.value in names else definition.dict.uitext[value].value
                    title=title.replace('<VALUE_1>',replacement)
                mail = c.SystemMailData(type=0,kind=0,senderEncodedUid=0,item=mission.param.rewards.value[0],
                    title=title,url='',urlAndroid='',alreadyRead=False,noticeIconId=0,deleteSec=-1,
                    manualDeletion=False,uniqueKey=cur.lastrowid,message=title,receivedSecs=now-1262271600)
                db.execute('UPDATE normal_mission_presents SET mail=? WHERE mail_key=?',(encode(mail),cur.lastrowid))
                cleared.append(mission)
            result = c.ObjArray(cleared)
        elif packet.type == MAILS:
            result = c.ObjArray(pending(player,db))
        else:
            mails = pending(player,db)
            if packet.type == RECEIVE:
                selected = [m for m in mails if m.uniqueKey == key]
                if len(selected) != 1:raise ValueError('unknown or already claimed mission present')
            else:selected = mails
            granted = [deliver(player,db,m,definition) for m in selected]
            receipt = c.MailPresentResult(items=c.ObjArray([x[0] for x in granted]),params=c.ObjArray([x[1] for x in granted]))
            if packet.type == RECEIVE:
                result = c.ObjArray([receipt,c.Null()])
            else:
                result = c.ObjArray([c.ObjArray(pending(player,db)),c.ObjArray(selected),receipt])
            LOG.info('mission_presents_claim_prepared uid=%s count=%s',player.uid,len(selected))
        # HttpConnector.as:516,541,921-934: these callers apply extras AFTER
        # callbacks (which addItems / increment or decrement unread counts).
        # Correct a touch settlement's absolute balance to include this award.
        extra = [c.String(f'touch_u:{player.freeMoney}') if isinstance(x,c.String)
                 and x.value.startswith('touch_u:') else x for x in extra]
        extra.append(c.String(f'prs:{len(pending(player,db))},0'))
        result,extra = result,c.ObjArray(extra)
        encode(result);encode(extra)
        return result,extra
    return accounts.transact(session.uiid,operation)


def enter(accounts,packet,session,definition):
    if not session.initialized or packet.type != ENTER or any(
            not gameplay.null(x) for x in (packet.payloadInt,packet.payloadObj0,packet.payloadObj1)):
        raise ValueError('invalid normal mission entry')
    def operation(player,db):
        if not enabled(db) or player.noticeFlagData.tutorialProgress < 7:
            raise ValueError('normal mission list requires isolated completed tutorial account')
        extra = gameplay.settle_touch(player,db,packet.payloadExtra,definition)
        extra.extend(extras(player,db,definition))
        db.execute('UPDATE player_state SET scene=144,revision=revision+1 WHERE uid=?',(player.uid,))
        result,extra = c.ObjArray([]),c.ObjArray(extra)
        encode(result);encode(extra)  # Serialization failure rolls back progress.
        return result,extra
    result = accounts.transact(session.uiid,operation)
    LOG.info('normal_missions_queried rewards=present_box')
    return result
