"""Local hidden encounters and archived-film rewards; not real ad validation."""
import secrets
import time
from .library import c
from .protocol import encode
from .state import request_token
from . import gameplay,restoration

HIDDEN,VIDEO,RATE,STARTED=16777447,16777428,238,237
TYPES={HIDDEN,VIDEO,RATE,STARTED}
RATES='PromotionVideo:101,Maio:0,Tapjoy:0,Nend:0,UnityAds:0,IronSource:0,Chartboost:0,AdMob:0'


def ensure(db):
    db.execute('''CREATE TABLE IF NOT EXISTS local_hidden_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER NOT NULL,hidden_id INTEGER NOT NULL,issued_unix INTEGER NOT NULL,claimed_unix INTEGER)''')
    db.execute('CREATE UNIQUE INDEX IF NOT EXISTS hidden_active ON local_hidden_runs(uid) WHERE claimed_unix IS NULL')
    db.execute('CREATE TABLE IF NOT EXISTS local_video_days(uid INTEGER NOT NULL,day INTEGER NOT NULL,count INTEGER NOT NULL,deadline INTEGER NOT NULL,PRIMARY KEY(uid,day))')
    db.execute('CREATE TABLE IF NOT EXISTS local_video_starts(uid INTEGER PRIMARY KEY,request_id TEXT NOT NULL,started INTEGER NOT NULL,used INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS local_home_reward_receipts(uid INTEGER NOT NULL,request_id TEXT NOT NULL,result BLOB NOT NULL,PRIMARY KEY(uid,request_id))')


def video_state(db,p,now):
    ensure(db)
    day=(now+p.timeZoneOffset//1000)//86400
    row=db.execute('SELECT count,deadline FROM local_video_days WHERE uid=? AND day=?',(p.uid,day)).fetchone()
    p.numAcquiredVideoAdReward=row[0] if row else 0
    count=row[0] if row else 0
    # The client permits the remaining films consecutively. A legacy per-film
    # deadline must not block the next STARTED request. Only an exhausted batch
    # waits for the existing local daily reset (not the official 8h schedule).
    remaining=max(0,(day+1)*86400-p.timeZoneOffset//1000-now) if count>=5 else 0
    return day,count,remaining


def consume_video(db,uid,now):
    ensure(db)
    row=db.execute('SELECT started,used FROM local_video_starts WHERE uid=?',(uid,)).fetchone()
    if not row or row[1] or not restoration.policy()['video_minimum_seconds']<=now-row[0]<=3600:
        raise ValueError('local archived film must be started and completed before reward')
    db.execute('UPDATE local_video_starts SET used=1 WHERE uid=?',(uid,))


def sync(p,db,d):
    if p.noticeFlagData.tutorialProgress<7:return []
    ensure(db);now=int(time.time());_,count,remaining=video_state(db,p,now)
    row=db.execute('SELECT hidden_id FROM local_hidden_runs WHERE uid=? AND claimed_unix IS NULL',(p.uid,)).fetchone()
    if row is None and p.rank>=4:
        last=db.execute('SELECT max(claimed_unix) FROM local_hidden_runs WHERE uid=?',(p.uid,)).fetchone()[0]
        if last is None or now-last>=restoration.policy()['hidden_cooldown_seconds']:
            ids=sorted(d.hideGudeMap)
            ident=ids[secrets.randbelow(len(ids))]
            db.execute('INSERT INTO local_hidden_runs(uid,hidden_id,issued_unix) VALUES(?,?,?)',(p.uid,ident,now))
            row=(ident,)
    return [c.String(f'hidegude:{row[0] if row else 0}'),c.String(f'video_ad_reward:{count},{remaining}'),
            c.String('videoads:'+RATES),c.String('priorityvideoads:PromotionVideo')]


def process(accounts,packet,session,d,*,request_fingerprint):
    if not session.initialized or any(not gameplay.null(x) for x in (packet.payloadObj0,packet.payloadObj1)):
        raise ValueError('invalid home reward payload')
    typ=packet.type
    args=gameplay.integers(packet.payloadInt,1) if typ==STARTED else []
    if typ!=STARTED and not gameplay.null(packet.payloadInt):raise ValueError('reward request takes no integers')
    token=request_token(session,request_fingerprint)
    def operation(p,db):
        if p.noticeFlagData.tutorialProgress<7:raise ValueError('finish tutorial first')
        ensure(db)
        if typ!=RATE and db.execute('SELECT 1 FROM local_home_reward_receipts WHERE uid=? AND request_id=?',(p.uid,token)).fetchone():raise ValueError('home reward request already processed')
        extra=gameplay.settle_touch(p,db,packet.payloadExtra,d)
        now=int(time.time())
        if typ==RATE:result=c.String(RATES)
        elif typ==STARTED:
            if args[0] not in (6,262):raise ValueError('only local archived promotion film is enabled')
            # GENERAL_STARTED_VIDEO carries only provider/priority, not purpose.
            # Cup shortening and friend gifts share it with GPS. Enforce each
            # feature's allowance when consuming, never at the common start.
            pending=db.execute('SELECT started,used FROM local_video_starts WHERE uid=?',(p.uid,)).fetchone()
            if pending and not pending[1] and now-pending[0]<restoration.policy()['video_minimum_seconds']:
                raise ValueError('local film just started; wait before retrying')
            db.execute('INSERT INTO local_video_starts VALUES(?,?,?,0) ON CONFLICT(uid) DO UPDATE SET request_id=excluded.request_id,started=excluded.started,used=0',(p.uid,token,now))
            result=c.Null()
        elif typ==VIDEO:
            day,count,remaining=video_state(db,p,now)
            if count>=len(d.videoAdReward.items.value):raise ValueError('local film rewards exhausted; wait for the next daily reset')
            consume_video(db,p.uid,now)
            item=d.videoAdReward.items.value[count]
            param=restoration.award(p,d,item)
            cooldown=max(0,(day+1)*86400-p.timeZoneOffset//1000-now) if count+1>=len(d.videoAdReward.items.value) else 0
            db.execute('INSERT INTO local_video_days VALUES(?,?,?,?) ON CONFLICT(uid,day) DO UPDATE SET count=excluded.count,deadline=excluded.deadline',(p.uid,day,count+1,now+cooldown))
            p.numAcquiredVideoAdReward=count+1
            result=c.ObjArray([c.ObjArray([item]),c.ObjArray([param]),c.IntArray([count+1,cooldown])])
        elif typ==HIDDEN:
            row=db.execute('SELECT id FROM local_hidden_runs WHERE uid=? AND claimed_unix IS NULL',(p.uid,)).fetchone()
            if not row:raise ValueError('no issued hidden character to collect')
            item=c.ItemParam(kind=0,id=0,num=max(1,p.rank)*restoration.policy()['hidden_gp_per_level'])
            param=restoration.award(p,d,item)
            db.execute('UPDATE local_hidden_runs SET claimed_unix=? WHERE id=?',(now,row[0]))
            result=c.GetItemResult(item=item,param=param,toMail=False)
        if typ!=RATE:db.execute('INSERT INTO local_home_reward_receipts VALUES(?,?,?)',(p.uid,token,encode(result)))
        if typ==HIDDEN:extra.append(c.String('hidegude:0'))
        out=c.ObjArray(extra);encode(result);encode(out)
        return result,out
    return accounts.transact(session.uiid,operation)
