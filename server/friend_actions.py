"""Transactional local friendship; original friend wire objects, no external users."""
import time
from .library import c
from .protocol import encode,decode
from .state import request_token
from . import gameplay,restoration

GIFT,FREE_GIFT,GP_GIFT,CHECK,TOUCH,ASSIST,EXTEND=168,221,241,242,228,67109034,67109036
TYPES={GIFT,FREE_GIFT,GP_GIFT,CHECK,TOUCH,ASSIST,EXTEND}


def ensure(db):
    db.execute('CREATE TABLE IF NOT EXISTS local_friend_points(a INTEGER NOT NULL,b INTEGER NOT NULL,points INTEGER NOT NULL,PRIMARY KEY(a,b),CHECK(a<b))')
    db.execute('''CREATE TABLE IF NOT EXISTS local_friend_actions(id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER NOT NULL,target INTEGER NOT NULL,kind INTEGER NOT NULL,day INTEGER NOT NULL,
        request_id TEXT NOT NULL,result BLOB NOT NULL,created_unix INTEGER NOT NULL,UNIQUE(uid,request_id))''')
    db.execute('CREATE INDEX IF NOT EXISTS friend_actions_day ON local_friend_actions(uid,target,kind,day)')
    db.execute('CREATE TABLE IF NOT EXISTS local_friend_assists(run_id TEXT NOT NULL,ability INTEGER NOT NULL,uid INTEGER NOT NULL,item_id INTEGER NOT NULL,PRIMARY KEY(run_id,ability))')
    db.execute('CREATE TABLE IF NOT EXISTS local_friend_touch(uid INTEGER NOT NULL,target INTEGER NOT NULL,day INTEGER NOT NULL,amount INTEGER NOT NULL,PRIMARY KEY(uid,target,day))')


def friendly(db,p,other,d):
    ensure(db)
    a,b=sorted((p.uid,other.uid))
    row=db.execute('SELECT points FROM local_friend_points WHERE a=? AND b=?',(a,b)).fetchone()
    points=row[0] if row else 0
    level=sum(points>=x.max for x in d.friendly.params.value)
    return c.FriendlyData(encodedUid=other.encodedUid,friendly=points,friendlyLevel=level)


def increase(db,p,q,d,amount,key):
    before=friendly(db,p,q,d)
    value=min(d.friendly.params.value[-1].max,before.friendly+amount)
    a,b=sorted((p.uid,q.uid))
    db.execute('INSERT INTO local_friend_points VALUES(?,?,?) ON CONFLICT(a,b) DO UPDATE SET points=excluded.points',(a,b,value))
    after=friendly(db,p,q,d)
    for level in range(before.friendlyLevel,after.friendlyLevel):
        for i,item in enumerate(d.friendly.params.value[level].rewards.value):
            for owner in (p,q):restoration.mail(db,owner.uid,f'friend-level:{a}:{b}:{level}:{i}',item,'なかよし報酬')
    return after,before.friendly,value-before.friendly,before.friendlyLevel


def room(db,p,q,d,engine):
    engine.project(q,db)
    day=(int(time.time())+p.timeZoneOffset//1000)//86400
    count=db.execute('SELECT count(*) FROM local_friend_actions WHERE uid=? AND kind=? AND day=?',(p.uid,ASSIST,day)).fetchone()[0]
    sent=db.execute('SELECT amount FROM local_friend_touch WHERE uid=? AND target=? AND day=?',(p.uid,q.uid,day)).fetchone()
    return c.UserRoomInfo(placedGudetamaId=q.placedGudetamaId,questionId=0,kitchenwareMap=q.kitchenwareMap,
        friendlyData=friendly(db,p,q,d),lastFriendlyLevel=0,
        friendPresentMoneyParam=c.IntArray([sent[0] if sent else 0,0,q.rank*d.rule.maxFriendPresentMoneyPerRank]),assistData=c.UserAssistData(num=count),
        decorationId=q.decorationId,homeDecoDataList=q.homeDecoDataMap.get(q.decorationId if d.rule.useHomeDecoEachType else 0,c.ObjArray([])).value)


def process(accounts,packet,session,d,engine,*,request_fingerprint):
    from . import friends
    if not session.initialized or any(not gameplay.null(x) for x in (packet.payloadObj0,packet.payloadObj1)):
        raise ValueError('invalid friend action payload')
    typ=packet.type
    args=[] if typ==EXTEND else gameplay.integers(packet.payloadInt,{CHECK:1,TOUCH:2,ASSIST:3,GIFT:3,FREE_GIFT:3,GP_GIFT:3}[typ])
    if typ==EXTEND and not gameplay.null(packet.payloadInt):raise ValueError('friend extension takes no integers')
    token=request_token(session,request_fingerprint) if typ!=CHECK else None
    def operation(p,db):
        friends.ensure(db);ensure(db)
        if not friends.eligible(p,d):raise ValueError('friends require level 10 and completed tutorial')
        extra=gameplay.settle_touch(p,db,packet.payloadExtra,d)
        now=int(time.time());day=(now+p.timeZoneOffset//1000)//86400
        if token and db.execute('SELECT 1 FROM local_friend_actions WHERE uid=? AND request_id=?',(p.uid,token)).fetchone():
            raise ValueError('friend action already processed')
        q=None
        if typ!=EXTEND:
            row=db.execute('SELECT player FROM accounts WHERE player IS NOT NULL AND uid<>?',(p.uid,)).fetchall()
            q=next((x for x in (decode(r[0]) for r in row) if x.encodedUid==args[0] and friends.eligible(x,d)),None)
            if q is None or friends.relations(db,p.uid,q.uid)[0]!=3:raise ValueError('mutual friendship required')
        if typ==EXTEND:
            index=p.numFriendsExtension
            if index>=min(d.rule.maxFriendsExtension,len(d.rule.friendsExtensionPrices.value)):raise ValueError('friend extension maximum reached')
            cost=d.rule.friendsExtensionPrices.value[index]
            if cost<0 or p.freeMoney<cost:raise ValueError('insufficient free GP')
            p.freeMoney-=cost;p.numFriendsExtension+=1
            result=c.ObjArray([])
        elif typ==CHECK:
            count=lambda kind:db.execute('SELECT count(*) FROM local_friend_actions WHERE uid=? AND target=? AND kind=? AND day=?',(p.uid,q.uid,kind,day)).fetchone()[0]
            result=c.IntArray([max(0,d.rule.friendPresentGpCountPerDay-count(GP_GIFT)),max(0,d.rule.freeFriendPresentCountPerDay-count(FREE_GIFT)),d.rule.friendPresentGpGlobalCountPerDay])
        elif typ in (GIFT,FREE_GIFT,GP_GIFT):
            gid,deliver=args[1:]
            if deliver not in (0,1):raise ValueError('invalid delivery flag')
            if deliver:raise ValueError('event delivery with gifting not restored; use normal gift')
            if gid not in d.gudetamaMap or not any(w.id==gid for w in q.wantedGudetamas.value):raise ValueError('recipient must want this character')
            owned=p.gudetamaMap.get(gid)
            if not owned or owned.count<1:raise ValueError('gift character not owned')
            if typ!=GIFT:
                limit=d.rule.freeFriendPresentCountPerDay if typ==FREE_GIFT else d.rule.friendPresentGpCountPerDay
                n=db.execute('SELECT count(*) FROM local_friend_actions WHERE uid=? AND target=? AND kind=? AND day=?',(p.uid,q.uid,typ,day)).fetchone()[0]
                if n>=limit:raise ValueError('daily friend gift limit reached')
            if typ==FREE_GIFT:
                from .home_rewards import consume_video
                consume_video(db,p.uid,now)
            else:
                field='freeMetal' if typ==GIFT else 'freeMoney'
                cost=d.rule.friendPresentCost if typ==GIFT else d.rule.friendPresentGp
                if cost<0 or getattr(p,field)<cost:raise ValueError('insufficient gift currency')
                setattr(p,field,getattr(p,field)-cost)
            owned.count-=1
            restoration.mail(db,q.uid,'friend-gift:'+token,c.ItemParam(kind=7,id=gid,num=1),'フレンドからのプレゼント',p.encodedUid)
            data,last,add,level=increase(db,p,q,d,restoration.policy()['gift_friendship'],token)
            result=c.FriendPresentResult(friendlyData=data,consumedGudetama=owned,lastFriendly=last,addFriendly=add,
                friendPresentLogDiff=c.ObjArray([]),lastFriendlyLevel=level,deliveredEventIds=c.IntArray([]))
        elif typ==TOUCH:
            amount=args[1]
            limit=q.rank*d.rule.maxFriendPresentMoneyPerRank
            old=db.execute('SELECT amount FROM local_friend_touch WHERE uid=? AND target=? AND day=?',(p.uid,q.uid,day)).fetchone()
            sent=old[0] if old else 0
            if amount<=0 or amount>limit-sent:raise ValueError('friend touch amount exceeds daily allowance')
            db.execute('INSERT INTO local_friend_touch VALUES(?,?,?,?) ON CONFLICT(uid,target,day) DO UPDATE SET amount=excluded.amount',(p.uid,q.uid,day,sent+amount))
            restoration.mail(db,q.uid,'friend-gp:'+token,c.ItemParam(kind=0,id=0,num=amount),'フレンドからのGP',p.encodedUid)
            data,last,add,level=increase(db,p,q,d,restoration.policy()['friend_touch_friendship'],token)
            result=c.ObjArray([c.IntArray([amount]),data,c.IntArray([last,add,level])])
        elif typ==ASSIST:
            kind,ident=args[1:]
            spec=d.usefulMap.get(ident);owned=p.usefulMap.get(ident)
            if not spec or gameplay.null(spec.assistAbilities) or len(spec.assistAbilities.value)!=1 or not owned or owned.num<1:raise ValueError('assist item not owned/eligible')
            ability=spec.assistAbilities.value[0]
            if ability.type not in (2,515,516):raise ValueError('unknown assist ability')
            n=db.execute('SELECT count(*) FROM local_friend_actions WHERE uid=? AND kind=? AND day=?',(p.uid,ASSIST,day)).fetchone()[0]
            if n>=d.rule.maxAssistPerDay:raise ValueError('daily assist maximum reached')
            run=db.execute("SELECT run_id,deadline_unix,gudetama_id FROM cooking_runs WHERE uid=? AND kitchen_type=? AND status='cooking'",(q.uid,kind)).fetchone()
            if not run or run[1]<=now:raise ValueError('friend kitchen is not cooking')
            kitchen=q.kitchenwareMap[kind]
            if ability.type==516 and not any(x.type==1 for x in d.gudetamaMap[run[2]].roulettes.value):raise ValueError('no happening segment to assist')
            if any(d.usefulMap[i].assistAbilities.value[0].type==ability.type or ability.type in (515,516) and d.usefulMap[i].assistAbilities.value[0].type in (515,516) for i in kitchen.assistUsefulIds.value):raise ValueError('assist ability already present')
            db.execute('INSERT INTO local_friend_assists VALUES(?,?,?,?)',(run[0],ability.type,p.uid,ident))
            owned.num-=1
            kitchen.assistUsefulIds.value.append(ident);kitchen.assistEncodedUids.value.append(p.encodedUid)
            data,last,add,level=increase(db,p,q,d,max(d.rule.friendlyValueByAssist,spec.friendlyValue),token)
            db.execute('UPDATE accounts SET player=? WHERE uid=?',(encode(q),q.uid))
            db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(q.uid,))
            result=c.FriendAssistResult(userRoomInfo=room(db,p,q,d,engine),lastFriendly=last,addFriendly=add,lastFriendlyLevel=level)
            result.userRoomInfo.assistData.num=n+1
        if token:
            db.execute('INSERT INTO local_friend_actions(uid,target,kind,day,request_id,result,created_unix) VALUES(?,?,?,?,?,?,?)',
                       (p.uid,q.uid if q else 0,typ,day,token,encode(result),now))
        # Cost callbacks already adjust client balances; do not send duplicate deltas.
        if typ in (EXTEND,GP_GIFT):extra=[x for x in extra if not isinstance(x,c.String) or not x.value.startswith('touch_u:')]
        encode(result);out=c.ObjArray(extra);encode(out)
        return result,out
    return accounts.transact(session.uiid,operation)
