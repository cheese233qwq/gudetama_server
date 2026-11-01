"""Local archived tour events: cook, deliver, rank, and audited BOX rewards.

Original static definitions/layouts are reused. Calendar, participation,
tie policy and delivery-to-BOX scheduling are explicitly local rules.
"""
import bisect
import logging
import time
from .library import c
from .player import blank
from .protocol import encode, decode
from .state import request_token
from . import gameplay, missions

INFO, ENTER, DELIVER, ALL = 51, 150, 33554433, 33554434
TYPES = {INFO, ENTER, DELIVER, ALL}
LOG=logging.getLogger('gudetama.local')


def profile(d, eid):
    # LOCAL association: 1000 + ranking ID, accepted only with matching
    # archived recipe candidates and delivery table. Not a recovered calendar.
    rank = d.rankingMap.get(eid-1000)
    if not rank or rank.groupType not in (0,1) or not rank.content.value:
        return None
    content = rank.content.value[0]
    tables = {x.deliverTableId:d.deliverPointTableMap.get(x.deliverTableId) for x in rank.content.value}
    rewards = d.rankingRewardMap.get(content.rewardId)
    recipes = [r for r in d.recipeNoteMap.values() if r.eventId==eid and d.kitchenwareMap[r.kitchenwareId].type==4]
    if any(x.type!=5 or x.daily or x.guild or x.rewardId!=content.rewardId or x.deliverPtsPercentMap for x in rank.content.value) or any(t is None for t in tables.values()) or not rewards or not recipes:
        return None
    ids = {gid for r in recipes for gid in r.defaults.value+r.appends.value}
    if not ids <= {int(i) for table in tables.values() for i in table.gudePointMap}:
        return None
    return rank,content,c.IntHashMap(tables),rewards,recipes


def ensure(db):
    db.execute('''CREATE TABLE IF NOT EXISTS local_event_cycles(
        cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,event_id INTEGER NOT NULL,
        ranking_id INTEGER NOT NULL,opened_unix INTEGER NOT NULL,deadline_unix INTEGER NOT NULL,
        settled_unix INTEGER, definition BLOB NOT NULL)''')
    db.execute('CREATE UNIQUE INDEX IF NOT EXISTS event_live_cycle ON local_event_cycles(event_id) WHERE settled_unix IS NULL')
    db.execute('''CREATE TABLE IF NOT EXISTS local_event_scores(
        cycle_id INTEGER NOT NULL REFERENCES local_event_cycles(cycle_id),
        uid INTEGER NOT NULL REFERENCES accounts(uid),points INTEGER NOT NULL CHECK(points BETWEEN 0 AND 2147483647),content_index INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(cycle_id,uid))''')
    db.execute('''CREATE TABLE IF NOT EXISTS local_event_deliveries(
        uid INTEGER NOT NULL REFERENCES accounts(uid),request_id TEXT NOT NULL,
        cycle_id INTEGER NOT NULL REFERENCES local_event_cycles(cycle_id),
        inventory BLOB NOT NULL,result BLOB NOT NULL,PRIMARY KEY(uid,request_id))''')
    db.execute('''CREATE TABLE IF NOT EXISTS local_event_cooking_runs(
        run_id TEXT PRIMARY KEY REFERENCES cooking_runs(run_id),cycle_id INTEGER NOT NULL REFERENCES local_event_cycles(cycle_id),
        hurry_item INTEGER NOT NULL DEFAULT 0,bonus_paid INTEGER NOT NULL DEFAULT 0)''')
    db.execute('''CREATE TABLE IF NOT EXISTS local_event_reward_mails(
        cycle_id INTEGER NOT NULL REFERENCES local_event_cycles(cycle_id),uid INTEGER NOT NULL REFERENCES accounts(uid),
        scope TEXT NOT NULL,reward_index INTEGER NOT NULL,item_index INTEGER NOT NULL,
        mail_key INTEGER NOT NULL UNIQUE REFERENCES normal_mission_presents(mail_key),
        PRIMARY KEY(cycle_id,uid,scope,reward_index,item_index))''')
    missions.ensure_box(db)
    if 'content_index' not in {r[1] for r in db.execute('PRAGMA table_info(local_event_scores)')}:
        db.execute('ALTER TABLE local_event_scores ADD COLUMN content_index INTEGER NOT NULL DEFAULT 0')


def calendar_changed(db,d,eid,enabled,deadline,now):
    ensure(db)
    settle(db,d,now)
    old=db.execute('SELECT cycle_id FROM local_event_cycles WHERE event_id=? AND settled_unix IS NULL',(eid,)).fetchone()
    if not enabled:
        if old:
            db.execute('UPDATE local_event_cycles SET deadline_unix=? WHERE cycle_id=?',(now,old[0]))
            settle(db,d,now)
        return
    spec=profile(d,eid)
    if not spec:return
    if old:
        db.execute('UPDATE local_event_cycles SET deadline_unix=? WHERE cycle_id=?',(deadline,old[0]))
    else:
        rank,content,table,rewards,recipes=spec
        # Freeze the scoring and reward definitions for this run of the event.
        frozen=encode(c.ObjArray([rank,table,rewards]))
        db.execute('INSERT INTO local_event_cycles(event_id,ranking_id,opened_unix,deadline_unix,definition) VALUES(?,?,?,?,?)',
                   (eid,rank.id,now,deadline,frozen))


def cycle(db,ranking_id,now,*,live=False):
    where=' AND settled_unix IS NULL AND deadline_unix>?' if live else ''
    row=db.execute('SELECT cycle_id,event_id,deadline_unix,definition,settled_unix FROM local_event_cycles WHERE ranking_id=?'+where+' ORDER BY cycle_id DESC LIMIT 1',
                   (ranking_id,now) if live else (ranking_id,)).fetchone()
    if not row:raise ValueError('no local event cycle for this ranking')
    return row


def standings(db,cycle_id,content_index=0):
    # Competition rank: equal points share rank; uid is stable display ordering.
    rows=db.execute('SELECT uid,points FROM local_event_scores WHERE cycle_id=? AND content_index=? AND points>0 ORDER BY points DESC,uid',(cycle_id,content_index)).fetchall()
    ranks={};previous=None;place=0
    for i,(uid,points) in enumerate(rows,1):
        if points!=previous:place=i
        ranks[uid]=place;previous=points
    return rows,ranks


def content_index(p,db,row):
    old=db.execute('SELECT content_index FROM local_event_scores WHERE cycle_id=? AND uid=?',(row[0],p.uid)).fetchone()
    if old:return old[0]
    rank=decode(row[3]).value[0]
    if rank.groupType==0:return 0
    index=rank.groupIdIndexMap.get(p.area)
    if index is None:
        if rank.hasDefaultGroupContent:return 0
        raise ValueError('player area is absent from this festival')
    index=index.value
    if not 0<=index<len(rank.content.value):raise ValueError('invalid archived festival content index')
    return index


def queue_reward(db,cy,uid,scope,index,item_index,item,title,now):
    if item.kind==17:return  # ItemParam.KIND_ONLY_SHOW: no inventory entitlement.
    if db.execute('SELECT 1 FROM local_event_reward_mails WHERE cycle_id=? AND uid=? AND scope=? AND reward_index=? AND item_index=?',
                  (cy,uid,scope,index,item_index)).fetchone():return
    if item.num<=0 or item.kind not in (0,1,6,7,8,9,13,19):
        raise ValueError('unsupported archived event reward')
    source=db.execute('SELECT min(mission_id) FROM normal_mission_presents WHERE uid=?',(uid,)).fetchone()[0]
    source=min(0,source or 0)-1
    cur=db.execute('INSERT INTO normal_mission_presents(uid,mission_id,mail,created_unix) VALUES(?,?,?,?)',(uid,source,b'',now))
    if cur.lastrowid>2147483647:raise ValueError('event BOX key overflow')
    mail=c.SystemMailData(type=0,kind=0,senderEncodedUid=0,item=item,title=title,url='',urlAndroid='',
        alreadyRead=False,noticeIconId=0,deleteSec=-1,manualDeletion=False,uniqueKey=cur.lastrowid,
        message=title+' · local event reward / claim in BOX',receivedSecs=now-1262271600)
    db.execute('UPDATE normal_mission_presents SET mail=? WHERE mail_key=?',(encode(mail),cur.lastrowid))
    db.execute('INSERT INTO local_event_reward_mails VALUES(?,?,?,?,?,?)',(cy,uid,scope,index,item_index,cur.lastrowid))


def thresholds(db,row,now):
    rank,tables,rewards=decode(row[3]).value
    scores=db.execute('SELECT uid,points,content_index FROM local_event_scores WHERE cycle_id=? AND points>0',(row[0],)).fetchall()
    totals={index:sum(value for uid,value,i in scores if i==index) for uid,points,index in scores}
    for uid,points,content in scores:
        total=totals[content]
        for scope,arr,value in (('point',rewards.pointRewards,points),('global',rewards.globalRewards,total)):
            for index,r in enumerate(arr.value or []):
                if value>=r.argi:
                    for j,item in enumerate(r.screeningItems.value):
                        queue_reward(db,row[0],uid,f'{scope}:{content}',index,j,item,f'LOCAL {rank.title} {scope} {r.argi}',now)


def rank_reward(rewards,place):
    table=rewards.rewardIdTable
    # Original table uses paired equal values for inclusive rank ranges;
    # select the step at this rank (no interpolation across reward brackets).
    pos=max(0,bisect.bisect_right(table.indexes.value,place)-1)
    ident=int(table.values.value[pos]*table.rate+table.offset)
    return next((r for r in rewards.rankingRewards.value if r.argi==ident),None)


def settle(db,d,now=None):
    now=int(time.time()) if now is None else now
    for row in db.execute('SELECT cycle_id,event_id,deadline_unix,definition,settled_unix FROM local_event_cycles WHERE settled_unix IS NULL AND deadline_unix<=?',(now,)).fetchall():
        thresholds(db,row,now)
        rank,table,rewards=decode(row[3]).value
        groups=[r[0] for r in db.execute('SELECT DISTINCT content_index FROM local_event_scores WHERE cycle_id=?',(row[0],))]
        for group in groups:
            scores,ranks=standings(db,row[0],group)
            for uid,points in scores:
                reward=rank_reward(rewards,ranks[uid])
                if reward:
                    for j,item in enumerate(reward.screeningItems.value):
                        queue_reward(db,row[0],uid,f'rank:{group}',ranks[uid],j,item,f'LOCAL {rank.title} rank {ranks[uid]}',now)
        db.execute('UPDATE local_event_cycles SET settled_unix=? WHERE cycle_id=?',(now,row[0]))


def sync(p,db,d,now=None):
    from . import events
    ensure(db)
    now=int(time.time()) if now is None else now
    # Upgrade calendar-only entries lazily without resetting existing scores.
    for eid,deadline in events.active(db,now):
        if profile(d,eid) and not db.execute('SELECT 1 FROM local_event_cycles WHERE event_id=? AND settled_unix IS NULL',(eid,)).fetchone():
            calendar_changed(db,d,eid,True,deadline,now)
    settle(db,d,now)
    if p.noticeFlagData.tutorialProgress<7:return []
    live=db.execute('SELECT event_id FROM local_event_cycles WHERE settled_unix IS NULL AND deadline_unix>?',(now,)).fetchall()
    valid=set()
    changed_notes=[];changed_roles=[];changed_k=[]
    for (eid,) in live:
        spec=profile(d,eid)
        if not spec:continue
        for rd in spec[4]:
            kd=d.kitchenwareMap[rd.kitchenwareId]
            if kd.type!=4:continue
            valid.add(rd.id)
            k=p.kitchenwareMap.get(kd.type)
            if k is None:
                k=blank(c.KitchenwareData,type=kd.type,paramMap={},assistUsefulIds=c.IntArray([]),assistEncodedUids=c.IntArray([]))
                p.kitchenwareMap[kd.type]=k
            if kd.id not in k.paramMap or not k.paramMap[kd.id].available:
                k.paramMap[kd.id]=c.KitchenwareParam(id=kd.id,available=True);changed_k.append(k)
            note=p.recipeNoteMap.get(rd.id)
            if not note:
                note=c.RecipeNoteData(id=rd.id,visible=True,available=True,purchased=True,targetValue=0,currentValue=0)
                p.recipeNoteMap[rd.id]=note;changed_notes.append(note)
            elif not (note.visible and note.available and note.purchased):
                note.visible=note.available=note.purchased=True;changed_notes.append(note)
            for gid in rd.defaults.value:
                gd=d.gudetamaMap[gid]
                if gd.targetType!=-1 or not gameplay.null(gd.requiredGudetamas):continue
                owned=p.gudetamaMap.get(gid)
                if not owned:
                    owned=blank(c.GudetamaData,id=gid);p.gudetamaMap[gid]=owned
                if not (owned.available and owned.unlocked):
                    owned.available=owned.unlocked=True;changed_roles.append(owned)
    for rid,note in p.recipeNoteMap.items():
        if d.recipeNoteMap[rid].eventId and rid not in valid and note.visible:
            note.visible=note.available=False;changed_notes.append(note)
    # Retain a running kitchen after close so costs can still be recovered.
    k=p.kitchenwareMap.get(4)
    if k and not valid and not k.recipeNoteId:
        for param in k.paramMap.values():
            if param.available:param.available=False;changed_k.append(k)
    frames=[]
    for key,items in (('kitchenware:',changed_k),('recipe_note:',changed_notes),('gudetama:',changed_roles)):
        if items:frames.append(c.ObjArray([c.String(key),c.ObjArray(items)]))
    return frames


def qualify(engine,p,db,d,rid,gid,target,now):
    rd=d.recipeNoteMap.get(rid)
    if not rd or not rd.eventId:return engine.rules.qualify(p,d,rid,gid,target)
    spec=profile(d,rd.eventId)
    if not spec or rd not in spec[4]:raise ValueError('event recipe not restored')
    cycle(db,spec[0].id,now,live=True)
    gd=d.gudetamaMap.get(gid)
    if p.noticeFlagData.tutorialProgress<7 or not gd or gd.targetType!=-1 or not gameplay.null(gd.requiredGudetamas):
        raise ValueError('event character condition unsupported')
    return engine.rules.qualify(p,d,rid,gid,target,allow_event=True)


def bind_run(db,d,rid,run_id,now):
    rd=d.recipeNoteMap[rid]
    if not rd.eventId:return
    spec=profile(d,rd.eventId)
    row=cycle(db,spec[0].id,now,live=True)
    db.execute('INSERT OR IGNORE INTO local_event_cooking_runs(run_id,cycle_id) VALUES(?,?)',(run_id,row[0]))


def finish_bonus(p,db,run_id,now):
    bound=db.execute('SELECT cycle_id,hurry_item,bonus_paid FROM local_event_cooking_runs WHERE run_id=?',(run_id,)).fetchone()
    if not bound or bound[2]:return 0,0
    extra_character=1 if bound[1]==62 else 0
    extra_points=0
    if bound[1]==63:
        row=db.execute('SELECT cycle_id,event_id,deadline_unix,definition,settled_unix FROM local_event_cycles WHERE cycle_id=?',(bound[0],)).fetchone()
        if row[2]>now and row[4] is None:
            old=db.execute('SELECT points FROM local_event_scores WHERE cycle_id=? AND uid=?',(row[0],p.uid)).fetchone()
            points=(old[0] if old else 0)+20
            total=db.execute('SELECT coalesce(sum(points),0) FROM local_event_scores WHERE cycle_id=?',(row[0],)).fetchone()[0]+20
            if max(points,total)>2147483647:raise ValueError('event bonus point overflow')
            index=content_index(p,db,row)
            db.execute('INSERT INTO local_event_scores(cycle_id,uid,points,content_index) VALUES(?,?,?,?) ON CONFLICT(cycle_id,uid) DO UPDATE SET points=excluded.points',(row[0],p.uid,points,index))
            thresholds(db,row,now);extra_points=20
    db.execute('UPDATE local_event_cooking_runs SET bonus_paid=1 WHERE run_id=?',(run_id,))
    return extra_character,extra_points


def info(p,db,row,now):
    rank,tables,rewards=decode(row[3]).value
    index=content_index(p,db,row)
    scores,ranks=standings(db,row[0],index);points=dict(scores).get(p.uid,0)
    records=[]
    for uid,value in scores[:100]:
        player=decode(db.execute('SELECT player FROM accounts WHERE uid=?',(uid,)).fetchone()[0])
        records.append(c.RankingRecord(point=value,encodeUid=player.encodedUid,playerName=player.playerName,
            avatar=player.avatar,snsType=player.snsInterlockType,snsProfileImage=c.Null()))
    return c.RankingInfo(contentIndex=index,type=5,contentTitle=rank.title,argi=0,
        showOnly=now>=row[2],guild=False,desc='LOCAL delivery event',myPoint=points,myRoughPlace=ranks.get(p.uid,0),
        topRecords=c.ObjArray(records),rewardId=rewards.id,rewardPlaceAndPoint=c.ObjArray([]),
        topRecordSizeMax=100,totalPoint=sum(value for uid,value in scores))


def process(accounts,packet,session,d,*,request_fingerprint):
    from . import events
    if not session.initialized or packet.type not in TYPES or any(not gameplay.null(x) for x in (packet.payloadObj0,packet.payloadObj1)):
        raise ValueError('invalid ranking request')
    typ=packet.type
    if typ==ENTER:
        if not gameplay.null(packet.payloadInt):raise ValueError('ranking entry has no integers')
        args=[]
    else:
        if not isinstance(packet.payloadInt,c.IntArray):raise ValueError('ranking IDs required')
        args=packet.payloadInt.value
        if len(args)!=(3 if typ==DELIVER else 1) and typ!=INFO:raise ValueError('invalid ranking arguments')
        if typ==INFO and (not args or len(args)>66 or len(set(args))!=len(args)):raise ValueError('distinct ranking IDs required')
    token=request_token(session,request_fingerprint)
    def operation(p,db):
        if p.noticeFlagData.tutorialProgress<7:raise ValueError('complete tutorial before ranking')
        extra=gameplay.settle_touch(p,db,packet.payloadExtra,d)
        extra.extend(sync(p,db,d))
        now=int(time.time())
        if typ==INFO:
            result=c.IntHashMap({rid:c.ObjArray([info(p,db,cycle(db,rid,now),now)]) for rid in args})
        elif typ==ENTER:
            db.execute('UPDATE player_state SET scene=150 WHERE uid=?',(p.uid,))
            result=c.ObjArray([])
        else:
            old=db.execute('SELECT inventory,result FROM local_event_deliveries WHERE uid=? AND request_id=?',(p.uid,token)).fetchone()
            if old:
                return decode(old[1]),c.ObjArray([]) # Never consume or award again.
            row=cycle(db,args[0],now,live=True)
            rank,tables,rewards=decode(row[3]).value
            index=content_index(p,db,row)
            table=tables.value[rank.content.value[index].deliverTableId]
            selected={}
            if typ==DELIVER:
                gid,quantity=args[1:]
                if quantity<=0 or quantity>32767:raise ValueError('positive delivery quantity required')
                selected[gid]=quantity
            else:
                selected={int(gid):p.gudetamaMap[int(gid)].num for gid in table.gudePointMap if int(gid) in p.gudetamaMap and p.gudetamaMap[int(gid)].num>0}
            if not selected:raise ValueError('no characters to deliver')
            added=0
            for gid,quantity in selected.items():
                values=table.gudePointMap.get(gid)
                owned=p.gudetamaMap.get(gid)
                if not values or not owned or owned.num<quantity or values.value[0]<=0:raise ValueError('ineligible delivery or insufficient inventory')
                added+=quantity*values.value[0]
            previous=db.execute('SELECT points FROM local_event_scores WHERE cycle_id=? AND uid=?',(row[0],p.uid)).fetchone()
            points=(previous[0] if previous else 0)+added
            total=db.execute('SELECT coalesce(sum(points),0) FROM local_event_scores WHERE cycle_id=? AND content_index=?',(row[0],index)).fetchone()[0]+added
            if max(points,total)>2147483647:raise ValueError('ranking point overflow')
            for gid,quantity in selected.items():p.gudetamaMap[gid].num-=quantity
            db.execute('INSERT INTO local_event_scores(cycle_id,uid,points,content_index) VALUES(?,?,?,?) ON CONFLICT(cycle_id,uid) DO UPDATE SET points=excluded.points',(row[0],p.uid,points,index))
            thresholds(db,row,now)
            scores,ranks=standings(db,row[0],index)
            result=c.IntArray([points,ranks[p.uid],total])
            db.execute('INSERT INTO local_event_deliveries VALUES(?,?,?,?,?)',(p.uid,token,row[0],encode(c.IntHashMap({gid:c.Int(q) for gid,q in selected.items()})),encode(result)))
            extra.append(c.ObjArray([c.String('gudetama:'),c.ObjArray([p.gudetamaMap[gid] for gid in selected])]))
        extra.extend([events.extra(db,d,include_closed=typ in (INFO,ENTER)),c.String(f'prs:{len(missions.pending(p,db))},0')])
        db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))
        extras=c.ObjArray(extra)
        encode(result);encode(extras)
        return result,extras
    answer=accounts.transact(session.uiid,operation)
    LOG.info('local_event_committed type=%s ranking=%s',typ,args[0] if args else None)
    return answer
