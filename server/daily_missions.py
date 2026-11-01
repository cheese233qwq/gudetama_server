"""Five archived daily layouts, Wiki goals; reset at the server's local midnight."""
import time
from datetime import date,datetime,timedelta
from .library import c
from .protocol import encode

SPECS=((1001,136,3,'gude.make.total',(0,0,5000)),
       (1002,4104,100,'gude.touch.num',(0,0,5000)),
       (1003,4104,5,'gude.touch.item.num',(0,0,10000)),
       (1004,8200,1,'cup.make.total',(0,0,10000)),
       (1006,64,3,'challenge.daily.clear',(1,0,1)))


def day_window(now=None):
    """Use the host's local calendar, including its daylight-saving transitions."""
    now=int(time.time()) if now is None else now
    today=datetime.fromtimestamp(now).date()
    start=int(datetime.combine(today,datetime.min.time()).timestamp())
    deadline=int(datetime.combine(today+timedelta(days=1),datetime.min.time()).timestamp())
    return (today-date(1970,1,1)).days,start,deadline


def sync(p,db,d,*,now=None):
    now=int(time.time()) if now is None else int(now)
    day,start,deadline=day_window(now)
    first_key=1000000+day*8
    counts=[db.execute("SELECT count(*) FROM cooking_runs WHERE uid=? AND status='claimed' AND claimed_unix>=?",(p.uid,start)).fetchone()[0],0,0,0,0]
    for text, in db.execute('SELECT request FROM touch_receipts WHERE uid=? AND created_unix>=?',(p.uid,start)):
        counts[1]+=int(text.split(':',1)[1].split('-',1)[0].split(',')[0])
        counts[2]+=sum(int(x) for x in text.split(':',1)[1].split('-',1)[0].split(',')[2:8])
    # Dropped items / hidden objects are deliberately not inferred from GP or voices.
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='local_gacha_draws'").fetchone():
        counts[3]=db.execute("SELECT count(*) FROM local_gacha_draws WHERE uid=? AND purpose IN ('cup-open','cup-purchase') AND created_unix>=?",(p.uid,start)).fetchone()[0]
    counts[4]=db.execute('SELECT count(*) FROM normal_mission_presents WHERE uid=? AND mission_id BETWEEN ? AND ?',(p.uid,first_key,first_key+3)).fetchone()[0]
    rows=[]
    for i,(ident,counter,goal,title,reward) in enumerate(SPECS):
        md=d.missionMap[ident]
        if md.counterType!=counter or md.eventId:raise ValueError('daily mission archive mismatch')
        param=c.MissionParam(number=i+1,type=1,category=0,guide=0,goalValue=goal,finishSecs=-1,
            targetDescKey='',titleKey='mission.title.'+title,nextTitleKey='',titleParam=c.Null(),
            rewards=c.ObjArray([c.ItemParam(kind=reward[0],id=reward[1],num=reward[2])]),counterType=counter)
        key=first_key+i;current=min(32767,counts[i])
        old=db.execute('SELECT mission_key,current_value FROM normal_mission_progress WHERE uid=? AND mission_id=?',(p.uid,ident)).fetchone()
        if old and old[0]==key:current=max(current,old[1])
        db.execute('''INSERT INTO normal_mission_progress VALUES(?,?,?,?,?,?,?) ON CONFLICT(uid,mission_id)
            DO UPDATE SET mission_key=excluded.mission_key,param=excluded.param,current_value=excluded.current_value,
            updated_unix=excluded.updated_unix,policy=excluded.policy''',(p.uid,ident,key,encode(param),current,now,'local-daily-v1'))
        rows.append(c.MissionData(key=key,param=param,currentValue=current,id=ident))
    return rows,deadline-now
