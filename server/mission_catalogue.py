"""Normal challenge catalogue. Goals/rewards: Wiki; IDs/types: GameDef6045.

Counter interpretation and availability are explicit local compatibility rules.
"""
from collections import Counter
from .library import c
from .protocol import decode

SOURCE='https://gudetama-tap.fandom.com/wiki/Challenges#Normal'
TARGETS={107:22,108:100,131:185,132:191,133:331,134:383,135:485,136:372,
         137:678,138:400,139:402,140:959,141:391,142:817,143:821,144:1063}


def catalogue(d):
    goals={}
    def group(start,values,kind,title,args=None):
        for offset,goal in enumerate(values):
            n=start+offset
            goals[n]=(goal,kind,title,args[offset] if args else None)
    group(1,[3,10,20,40,60,80,100,120,140,160,180,200,250,300,350,400,450,500,550,600],'collect','rank')
    group(21,[1,2,3,5,7,10,15,20,*range(30,101,10),*range(120,401,20),*range(450,1201,50)],'voice1','voice.num')
    group(68,[5,25,50],'cleared','challenge.clear')
    group(71,[2,3,4,5,6,7,15,30,50],'days','play.num')
    group(80,[3,10,50,3,10,3,10,3,10,3,10,3,10,3,10],'category','cooking.category.num',[0,0,0,1,1,5,5,6,6,7,7,9,9,10,10])
    group(95,[1,3,5,10,15,20,30,50],'gifts','present.num')
    group(103,[30,50,100,200],'cooked','gude.make.total')
    for n,gid in TARGETS.items():goals[n]=(1,'target','gude.target.make',gid)
    group(109,[2,10,30],'failures','cooking.failure')
    group(112,[10,25,50],'hidden','hide.gude')
    group(115,[1]*13,'item','use.useful',[11,12,13,31,32,33,21,22,23,42,43,1,2])
    group(128,[30,35,40],'collect','rank')
    group(145,[1,2,3],'cup','cup.make.total')
    group(148,[1,3,5,10],'cup_unique','cup.make')
    group(152,[*range(1,11),15,20,*range(30,601,10)],'voice2','voice_rare2.num')
    rewards={1:(0,0,5000),2:(8,11,3),3:(13,29,1),4:(8,44,1),5:(8,12,3),6:(8,13,1),7:(13,35,1),8:(1,0,3),
        9:(8,43,1),10:(8,22,3),11:(8,23,1),12:(13,48,1),13:(1,0,1),15:(1,0,1),17:(1,0,1),19:(1,0,1),
        21:(8,11,3),22:(8,31,3),23:(8,2,1),24:(8,11,3),25:(8,31,3),26:(13,30,1),27:(8,21,3),28:(8,2,1),
        29:(8,42,3),30:(8,12,3),31:(8,22,3),32:(8,32,3),33:(8,13,2),34:(8,33,2),35:(8,23,3),36:(13,31,1),
        37:(8,14,1),38:(8,42,1),39:(8,33,1),40:(8,23,1),41:(1,0,3),42:(8,2,1),43:(1,0,1),44:(1,0,1),45:(1,0,1),
        46:(13,49,1),47:(8,2,1),48:(1,0,1),49:(1,0,1),50:(1,0,1),51:(13,50,1),
        68:(8,21,3),69:(1,0,5),70:(11,34,1),71:(1,0,5),72:(8,11,3),73:(8,31,3),74:(8,21,3),75:(8,2,1),
        76:(12,17,1),77:(11,38,1),78:(1,0,10),79:(8,1,5),80:(8,1,2),81:(8,42,1),82:(8,14,1),83:(8,2,1),
        84:(8,12,1),85:(8,11,3),86:(8,22,1),87:(8,21,3),88:(8,12,1),89:(8,31,3),90:(8,12,1),91:(8,11,3),
        92:(8,22,1),93:(8,21,3),94:(8,32,1),95:(1,0,2),96:(1,0,2),97:(1,0,2),98:(8,21,3),99:(8,11,3),
        100:(8,31,3),101:(8,32,1),102:(13,36,1),103:(8,12,1),104:(8,2,2),105:(1,0,3),106:(1,0,3),107:(8,31,3),
        108:(12,18,1),109:(0,0,6000),110:(8,31,3),111:(8,31,3),112:(8,22,1),113:(1,0,3),114:(1,0,3),
        146:(1,0,1),147:(1,0,1),148:(19,1001,1),149:(8,21,3),150:(8,32,1),151:(8,13,1),
        152:(0,0,300000),153:(0,0,500000),154:(19,1,1),155:(0,0,800000),156:(8,33,10),157:(0,0,1000000),
        158:(0,0,1500000),159:(8,33,10),160:(0,0,2000000),161:(19,3,1),162:(8,13,3),163:(19,7,1),164:(8,33,3),
        165:(8,23,3),166:(19,4,1),167:(8,13,3),168:(19,6,1),169:(8,33,1),170:(8,23,3)}
    for n in range(115,128):rewards[n]=(0,0,1000*(1+(n-115)%3) if n<124 else (2000 if n==125 else 1000))
    for n in range(52,68):
        if n%4==0:rewards[n]=(8,2,1)
        elif n not in (55,59,63,67):rewards[n]=(1,0,1)
    rewards.update({14:(12,43,1),16:(12,42,1),18:(12,40,1),20:(12,41,1),
                    55:(13,181,1),59:(13,182,1),63:(13,194,1),67:(13,193,1),145:(13,102,1)})
    # Exact archive condition-map mission IDs determine equipment rewards.
    for kid,condition in d.kitchenwareConditionMap.items():
        md=d.missionMap[condition.value[1]]
        rewards[md.number]=(4,kid,1)
    special_cups={171:10,174:11,177:12,180:9,183:16,186:14,189:19,192:20,
                  195:15,198:17,201:18,204:13,207:11,210:12,213:9,216:16,219:14}
    for n in range(171,222):rewards[n]=(19,special_cups[n],1) if n in special_cups else (1,0,1)
    result=[]
    maps={4:d.kitchenwareMap,8:d.usefulMap,11:d.stampMap,12:d.avatarMap,13:d.commentMap,19:d.cupGachaMap}
    for md in sorted(d.missionMap.values(),key=lambda m:m.number):
        if md.eventId or md.number<=0:continue
        goal,kind,title,arg=goals[md.number]
        reward=rewards[md.number]
        if reward[0] in maps and reward[1] not in maps[reward[0]]:raise ValueError('missing challenge reward ID')
        title='mission.title.'+title
        if title not in d.dict.uitext:raise ValueError('missing challenge title')
        result.append(dict(id=md.id,number=md.number,goal=goal,kind=kind,title=title,arg=arg,reward=reward,
                           counter=md.counterType))
    return result


def counters(p,db,d):
    cooked=db.execute("SELECT result_id,result_type FROM cooking_runs WHERE uid=? AND status='claimed'",(p.uid,)).fetchall()
    targets=Counter(r[0] for r in cooked)
    categories=Counter(d.gudetamaMap[r[0]].category for r in cooked)
    used=Counter()
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='cooking_item_selections'").fetchone():
        for row in db.execute('SELECT s.items FROM cooking_item_selections s JOIN cooking_runs r ON r.run_id=s.run_id WHERE r.uid=? AND s.consumed_unix IS NOT NULL',(p.uid,)):
            used.update(decode(row[0]).value)
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='local_home_item_receipts'").fetchone():
        used.update(r[0] for r in db.execute('SELECT item_id FROM local_home_item_receipts WHERE uid=?',(p.uid,)))
    db.execute('''CREATE TABLE IF NOT EXISTS local_login_days(uid INTEGER NOT NULL REFERENCES accounts(uid),day INTEGER NOT NULL,PRIMARY KEY(uid,day))''')
    cup_count=0
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='local_gacha_draws'").fetchone():
        cup_count=db.execute("SELECT count(*) FROM local_gacha_draws WHERE uid=? AND purpose IN ('cup-open','cup-purchase')",(p.uid,)).fetchone()[0]
    return dict(collect=sum(g.count>0 or g.num>0 for g in p.gudetamaMap.values()),
        voice1=sum(g.count>0 and bool(g.unlockedVoiceIndex&1) for g in p.gudetamaMap.values()),
        voice2=sum(g.count>0 and bool(g.unlockedVoiceIndex&2) for g in p.gudetamaMap.values()),
        cleared=db.execute('SELECT count(*) FROM normal_mission_presents WHERE uid=? AND mission_id BETWEEN 1 AND 999',(p.uid,)).fetchone()[0],
        days=db.execute('SELECT count(*) FROM local_login_days WHERE uid=?',(p.uid,)).fetchone()[0],
        cooked=len(cooked),failures=sum(r[1]==2 for r in cooked),category=categories,target=targets,item=used,
        cup=cup_count,cup_unique=sum(g.count>0 and d.gudetamaMap[i].isCup for i,g in p.gudetamaMap.items()),
        gifts=(db.execute('SELECT count(*) FROM local_friend_actions WHERE uid=? AND kind IN (168,221,241)',(p.uid,)).fetchone()[0]
               if db.execute("SELECT 1 FROM sqlite_master WHERE name='local_friend_actions'").fetchone() else 0),
        hidden=(db.execute('SELECT count(*) FROM local_hidden_runs WHERE uid=? AND claimed_unix IS NOT NULL',(p.uid,)).fetchone()[0]
                if db.execute("SELECT 1 FROM sqlite_master WHERE name='local_hidden_runs'").fetchone() else 0))


def title_param(spec):
    kind,arg=spec['kind'],spec['arg']
    if kind=='category':return c.ObjArray([c.String('CookingCategory'),c.String(f'gudetama.category.{arg}')])
    if kind=='item':return c.ObjArray([c.String('UseUsefulItem'),c.Int(arg)])
    if kind=='target':return c.ObjArray([c.String('GudetamaTarget'),c.Int(arg)])
    return c.Null()
