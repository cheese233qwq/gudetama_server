"""Non-official isolated gacha policy using archived costs, pools and wire types.

Unlock thresholds / duplicate conversion / resets are not recovered algorithms.
See docs/local_gacha.md. Archived-film cup shortening only; no ad SDK, billing,
once-more or production connections.
"""
import logging
import secrets
import time
import uuid
from .library import c
from .player import blank
from .protocol import encode
from .state import request_token
from . import gameplay, tutorial, local_voices, gacha_settings

LOG = logging.getLogger('gudetama.local')
ENTER, LIST, PLAY, FREE = 143,167772315,167772316,167772317
STAMP = 167772409
COOK, SHORT, DRAW, GUIDE, PLACE = 16777217,16777218,16777219,16777220,1
POOLS = (1,3)
CUPS = (1,2,3,4,5)
TYPES = {ENTER,LIST,PLAY,FREE,STAMP,COOK,SHORT,DRAW,GUIDE,PLACE}


class Engine:
    def __init__(self):
        self.clock = time.time
        self.random_below = secrets.randbelow

    def sync(self,p,db,d):
        if not tutorial.enabled(db) or p.noticeFlagData.tutorialProgress < 7:return
        db.execute('''CREATE TABLE IF NOT EXISTS local_gacha_visits(
            uid INTEGER PRIMARY KEY REFERENCES accounts(uid),token TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS local_gacha_draws(
            run_id TEXT PRIMARY KEY,uid INTEGER NOT NULL REFERENCES accounts(uid),
            boundary TEXT NOT NULL,purpose TEXT NOT NULL,result BLOB NOT NULL,
            created_unix INTEGER NOT NULL,UNIQUE(uid,boundary,purpose))''')
        db.execute('''CREATE TABLE IF NOT EXISTS local_gacha_days(
            uid INTEGER NOT NULL REFERENCES accounts(uid),pool_id INTEGER NOT NULL,
            day INTEGER NOT NULL,PRIMARY KEY(uid,pool_id))''')
        db.execute('''CREATE TABLE IF NOT EXISTS local_cup_runs(
            run_id TEXT PRIMARY KEY,uid INTEGER NOT NULL REFERENCES accounts(uid),
            slot INTEGER NOT NULL CHECK(slot BETWEEN 0 AND 3),cup_id INTEGER NOT NULL,
            deadline INTEGER,claimed_unix INTEGER,UNIQUE(uid,slot,run_id))''')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS local_cup_active_slot ON local_cup_runs(uid,slot) WHERE claimed_unix IS NULL')
        db.execute('CREATE INDEX IF NOT EXISTS cup_active_by_uid ON local_cup_runs(uid) WHERE claimed_unix IS NULL')
        features = {x.value if isinstance(x,c.Int) else x for x in p.features.value}
        if not {10,15} <= features:
            db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',
                (p.uid,'local-gacha-unlock-v1',encode(p),int(self.clock())))
            p.features = c.IntArray(sorted(features|{10,15}))
        for ident in gacha_settings.active(db):
            definition = d.gachaMap[ident]
            user = p.gachaMap.get(ident)
            if user is None:
                user = c.UserGachaData(id=ident,playCount=0,
                    prices=c.ObjArray([c.UserGachaPriceData(dailyPlayCount=0) for _ in definition.prices.value]),
                    onceMorePlayCount=0,freePlayCount=0)
                p.gachaMap[ident] = user
            day = (int(self.clock())+p.timeZoneOffset//1000)//86400
            old = db.execute('SELECT day FROM local_gacha_days WHERE uid=? AND pool_id=?',(p.uid,ident)).fetchone()
            if old and day > old[0]:
                user.freePlayCount=0
                for price in user.prices.value:price.dailyPlayCount=0
            if not old or day > old[0]:
                db.execute('INSERT OR REPLACE INTO local_gacha_days VALUES(?,?,?)',(p.uid,ident,day))
        self.project(p,db)

    def project(self,p,db):
        active = db.execute('SELECT slot,cup_id,deadline FROM local_cup_runs WHERE uid=? AND claimed_unix IS NULL AND deadline IS NOT NULL',
                            (p.uid,)).fetchall()
        if len(active)>1:raise ValueError('multiple active cup timers')
        if active:
            slot,cup,deadline=active[0]
            if p.cupGachaData.cupGachaIds.value[slot] != cup:raise ValueError('cup timer and slot disagree')
            p.cupGachaData.cookIndex=slot
            p.cupGachaData.restSec=max(0,deadline-int(self.clock()))
        else:
            p.cupGachaData.cookIndex=-1
            p.cupGachaData.restSec=0

    def choose(self,items,weights):
        if not weights:weights=[1]*len(items)
        if not items or len(items)!=len(weights) or any(type(w) is not int or w<0 for w in weights):
            raise ValueError('invalid archived lottery pool')
        # Only genuinely missing/zero weights use the requested even fallback.
        if not sum(weights):weights=[1]*len(items)
        pick=self.random_below(sum(weights))
        for item,weight in zip(items,weights):
            if pick<weight:return item
            pick-=weight
        raise ValueError('invalid server lottery random result')

    def award(self,p,d,item):
        if item.num<=0:raise ValueError('invalid lottery reward quantity')
        if item.kind in (6,7):
            if item.id not in d.gudetamaMap:raise ValueError('unknown lottery character')
            owned=p.gudetamaMap.get(item.id)
            if owned is None:
                owned=blank(c.GudetamaData,id=item.id,available=True,unlocked=True)
                p.gudetamaMap[item.id]=owned
            owned.available=owned.unlocked=True
            if item.kind==7:
                if owned.count+item.num>999 or owned.num+item.num>32767:raise ValueError('lottery character inventory full')
                owned.count+=item.num;owned.num+=item.num
                local_voices.unlock_first(p,d,item.id)
            # Kind6 = recipe only, never invent an obtained character count.
            p.rank=max(p.rank,1,sum(g.count>0 or g.num>0 for g in p.gudetamaMap.values()))
            return owned
        if item.kind==8:
            if item.id not in d.usefulMap:raise ValueError('unknown lottery useful')
            owned=p.usefulMap.get(item.id)
            if owned is None:
                owned=c.UsefulData(id=item.id,num=0,available=False,nextAvailablePurchaseSec=0)
                p.usefulMap[item.id]=owned
            if owned.num+item.num>d.usefulMap[item.id].possessionLimit:raise ValueError('lottery useful inventory full')
            owned.num+=item.num
            return item  # UserDataWrapper.addUseful consumes an ItemParam delta.
        if item.kind==11:
            if item.id not in d.stampMap:raise ValueError('unknown lottery stamp')
            owned=p.stampMap.get(item.id)
            if owned is None:
                owned=c.StampData(id=item.id,num=0,available=False)
                p.stampMap[item.id]=owned
            if owned.num+item.num>99999:raise ValueError('lottery stamp inventory full')
            owned.num+=item.num
            return item
        if item.kind==12:
            if item.id not in d.avatarMap:raise ValueError('unknown lottery avatar')
            owned=p.avatarMap.get(item.id)
            if owned is None:
                owned=c.AvatarData(id=item.id,acquired=True,available=False)
                p.avatarMap[item.id]=owned
            owned.acquired=True
            return owned  # Local duplicate policy: retain ownership, no conversion.
        if item.kind==9:
            if item.id not in d.decorationMap:raise ValueError('unknown lottery decoration')
            owned=p.decorationMap.get(item.id)
            if owned is None:
                owned=c.DecorationData(id=item.id,acquired=True,available=False)
                p.decorationMap[item.id]=owned
            owned.acquired=True
            return owned
        raise ValueError('unsupported lottery reward kind')

    def debit(self,p,item):
        # Only earned/free balances: this implementation never validates cash.
        if item.kind in (0,1):
            field='freeMoney' if item.kind==0 else 'freeMetal'
            if item.num<0 or getattr(p,field)<item.num:raise ValueError('insufficient free lottery currency')
            setattr(p,field,getattr(p,field)-item.num)
        elif item.kind in (8,11):
            owned=(p.usefulMap if item.kind==8 else p.stampMap).get(item.id)
            if item.num<0 or owned is None or owned.num<item.num:raise ValueError('insufficient lottery tickets')
            owned.num-=item.num
        else:raise ValueError('unsupported lottery payment')

    def cup_result(self,p,d,ident):
        definition=d.cupGachaMap[ident]
        item=self.choose(definition.prizes.value,getattr(definition.oddses,'value',None))
        result=c.GetItemResult(item=item,param=self.award(p,d,item),toMail=False)
        return c.CupGachaResult(id=ident,results=[result])

    def process(self,accounts,packet,session,d,*,request_fingerprint=None):
        if not session.initialized or any(not gameplay.null(x) for x in (packet.payloadObj0,packet.payloadObj1)):
            raise ValueError('invalid local lottery request')
        typ=packet.type
        purchase=typ==50331664
        lengths={PLAY:3,FREE:1,COOK:1,DRAW:1,PLACE:1,50331664:3}
        ints=gameplay.integers(packet.payloadInt,lengths[typ]) if typ in lengths else []
        if typ==STAMP:
            if not isinstance(packet.payloadInt,c.IntArray):raise ValueError('stamp payment integers required')
            ints=gameplay.integers(packet.payloadInt,len(packet.payloadInt.value))
            if not 4<=len(ints)<=102 or len(ints)%2:raise ValueError('invalid stamp payment pairs')
        elif typ not in lengths and not gameplay.null(packet.payloadInt):raise ValueError('lottery query has no integer payload')
        def operation(p,db):
            if not tutorial.enabled(db) or p.noticeFlagData.tutorialProgress<7:raise ValueError('lottery requires isolated completed tutorial account')
            extra=gameplay.settle_touch(p,db,packet.payloadExtra,d)
            self.sync(p,db,d)
            pools=gacha_settings.active(db)
            if typ in (ENTER,LIST):
                db.execute('INSERT OR REPLACE INTO local_gacha_visits VALUES(?,?)',(p.uid,str(uuid.uuid4())))
                db.execute('UPDATE player_state SET scene=143 WHERE uid=?',(p.uid,))
                result=c.ObjArray([]) if typ==ENTER else c.ObjArray([
                    c.ObjArray([c.GachaData(id=i,existsPickup=any(x.pickupFlag for x in d.gachaMap[i].screeningItems.value)) for i in pools]),
                    c.ObjArray([p.gachaMap[i] for i in pools]),c.IntArray([0])])
            elif typ in (PLAY,FREE,STAMP):
                ident=ints[0]
                if ident not in pools:raise ValueError('unsupported local lottery pool')
                definition,user=d.gachaMap[ident],p.gachaMap[ident]
                index=ints[1] if typ in (PLAY,STAMP) else 0
                if not 0<=index<len(definition.prices.value):raise ValueError('invalid lottery price index')
                # Fresh encrypted requests are separate draws, even within one visit.
                # Persist the session-scoped wire fingerprint, not the 8-bit sequence.
                purpose=f'normal:{ident}:{typ}:{index}'
                if not db.execute('SELECT 1 FROM local_gacha_visits WHERE uid=?',(p.uid,)).fetchone():
                    raise ValueError('enter lottery before drawing')
                token=request_token(session,request_fingerprint)
                if db.execute('SELECT 1 FROM local_gacha_draws WHERE uid=? AND boundary=? AND purpose=?',
                              (p.uid,token,purpose)).fetchone():
                    raise ValueError('lottery request already processed')
                price=definition.prices.value[index]
                use=c.Null()
                count=definition.numFree if typ==FREE else price.num
                if typ==FREE:
                    if not count or user.freePlayCount>=count:raise ValueError('free lottery already used today')
                    count=1;user.freePlayCount+=1
                elif typ==STAMP:
                    payment=next((x for x in price.prices.value if x.kind==11),None)
                    pairs=list(zip(ints[2::2],ints[3::2]))
                    if payment is None or payment.num<=0 or len({i for i,n in pairs})!=len(pairs):
                        raise ValueError('invalid stamp payment option')
                    for ident_stamp,num in pairs:
                        spec=d.stampMap.get(ident_stamp)
                        if spec is None or spec.rare not in (1,2) or num<=0:
                            raise ValueError('eligible rare stamps required')
                    total=sum(n for i,n in pairs)
                    if total%payment.num or not 1<=total//payment.num<=10:
                        raise ValueError('invalid stamp payment quantity')
                    batches=total//payment.num
                    if price.numDaily>0 and user.prices.value[index].dailyPlayCount+batches>price.numDaily:
                        raise ValueError('lottery daily limit reached')
                    for ident_stamp,num in pairs:self.debit(p,c.ItemParam(kind=11,id=ident_stamp,num=num))
                    user.prices.value[index].dailyPlayCount+=batches
                    count=price.num*batches
                    # GachaScene_Gudetama.as:740-747 consumes submitted pairs;
                    # returning a useItem too would debit the client twice.
                else:
                    if ints[2] not in (0,1):raise ValueError('invalid lottery batch flag')
                    options=price.prices.value
                    def affordable(x):
                        if x.kind==0:return p.freeMoney>=x.num
                        if x.kind==1:return p.freeMetal>=x.num
                        inventory=p.usefulMap if x.kind==8 else {}
                        return inventory.get(x.id) and inventory[x.id].num>=x.num
                    choice=next((x for x in options if affordable(x)),None)
                    if choice is None:raise ValueError('insufficient free lottery currency/tickets')
                    daily=user.prices.value[index].dailyPlayCount
                    batches=1
                    if ints[2]:
                        if choice.kind in (8,11):
                            inventory=p.usefulMap if choice.kind==8 else p.stampMap
                            batches=min(10,inventory[choice.id].num//choice.num)
                        elif choice.kind==0 and price.numDaily>0:batches=min(price.numDaily-daily,p.freeMoney//choice.num)
                        else:raise ValueError('unsupported lottery batch payment')
                    if batches<1 or price.numDaily>0 and daily+batches>price.numDaily:raise ValueError('lottery daily limit reached')
                    use=c.ItemParam(kind=choice.kind,id=choice.id,num=choice.num*batches)
                    self.debit(p,use)
                    user.prices.value[index].dailyPlayCount+=batches
                    count*=batches
                if not 1<=count<=11:raise ValueError('lottery draw count out of range')
                pool=definition.screeningItems.value
                from . import gacha_policy
                items,params,converted,rarities,compensation=gacha_policy.draw(self,p,db,d,ident,pool,count)
                if compensation or isinstance(use,c.ItemParam) and use.kind==0:
                    # Extras arrive before the primary callback, which still
                    # debits useItem. Unique-reward callbacks do not credit GP.
                    extra=[x for x in extra if not isinstance(x,c.String) or not x.value.startswith('touch_u:')]
                    extra.append(c.String(f'touch_u:{p.freeMoney+(use.num if isinstance(use,c.ItemParam) and use.kind==0 else 0)}'))
                user.playCount+=count
                result=c.GachaResult(userGachaData=user,items=c.ObjArray(items),params=c.ObjArray(params),
                    convertedItems=c.ObjArray(converted),
                    rarities=c.IntArray(rarities),
                    worthFlags=c.IntArray([0]*count),onceMore=False,useItem=use)
                db.execute('INSERT INTO local_gacha_draws VALUES(?,?,?,?,?,?)',
                    (str(uuid.uuid4()),p.uid,token,purpose,encode(result),int(self.clock())))
            elif typ==GUIDE:
                if p.noticeFlagData.noticeFlags.value[27]&15!=1:raise ValueError('cup gift requires active cup guide')
                receipt='local-cup-guide-gift-v1'
                if db.execute('SELECT 1 FROM player_migrations WHERE uid=? AND name=?',(p.uid,receipt)).fetchone():result=c.Null()
                else:
                    slots=p.cupGachaData.cupGachaIds.value
                    if 0 not in slots or 1001 not in d.cupGachaMap:raise ValueError('no empty cup slot or guide cup definition')
                    slot=slots.index(0)
                    db.execute('INSERT INTO player_migrations VALUES(?,?,?,?)',(p.uid,receipt,encode(p),int(self.clock())))
                    slots[slot]=1001
                    run=str(uuid.uuid4())
                    db.execute('INSERT INTO local_cup_runs VALUES(?,?,?,?,NULL,NULL)',(run,p.uid,slot,1001))
                    result=c.IntArray([slot,1001])
                    db.execute('INSERT INTO local_gacha_draws VALUES(?,?,?,?,?,?)',
                        (str(uuid.uuid4()),p.uid,run,'cup-guide',encode(result),int(self.clock())))
            elif typ==SHORT:
                # CupGachaSlotDialog sends no slot and expects an Int restSec.
                # Its button uses the archived per-cup limit, independent of GPS.
                from .home_rewards import consume_video
                token=request_token(session,request_fingerprint)
                if db.execute("SELECT 1 FROM local_gacha_draws WHERE uid=? AND boundary=? AND purpose='cup-short'",
                              (p.uid,token)).fetchone():
                    raise ValueError('cup shortening request already processed')
                slot=p.cupGachaData.cookIndex
                row=db.execute('SELECT run_id,cup_id,deadline FROM local_cup_runs WHERE uid=? AND slot=? AND claimed_unix IS NULL',
                               (p.uid,slot)).fetchall()
                now=int(self.clock())
                if len(row)!=1 or row[0][2] is None or row[0][2]<=now:
                    raise ValueError('cup shortening requires an active unfinished cup')
                run,ident,deadline=row[0]
                if not 0<=slot<4 or p.cupGachaData.cupGachaIds.value[slot]!=ident:
                    raise ValueError('cup slot mismatch')
                limit,minutes=d.rule.cupGachaShortNumByAd,d.rule.cupGachaShortMinByAd
                if not 0<limit<=127 or minutes<=0:raise ValueError('invalid archived cup shortening rule')
                if not 0<=p.cupGachaData.showAdNum<limit:raise ValueError('cup film shortening limit reached')
                consume_video(db,p.uid,now)
                db.execute('UPDATE local_cup_runs SET deadline=? WHERE run_id=?',(max(now,deadline-minutes*60),run))
                p.cupGachaData.showAdNum+=1
                self.project(p,db)
                result=c.Int(p.cupGachaData.restSec)
                db.execute('INSERT INTO local_gacha_draws VALUES(?,?,?,?,?,?)',
                           (str(uuid.uuid4()),p.uid,token,'cup-short',encode(result),now))
            elif typ in (COOK,DRAW):
                slot=ints[0]
                if not 0<=slot<4:raise ValueError('invalid cup slot')
                row=db.execute('SELECT run_id,cup_id,deadline FROM local_cup_runs WHERE uid=? AND slot=? AND claimed_unix IS NULL',(p.uid,slot)).fetchall()
                if len(row)!=1:raise ValueError('unknown or already opened cup')
                run,ident,deadline=row[0]
                if p.cupGachaData.cupGachaIds.value[slot]!=ident:raise ValueError('cup slot mismatch')
                if typ==COOK:
                    if p.cupGachaData.cookIndex not in (-1,slot):raise ValueError('another cup is cooking')
                    if deadline is None:
                        # The original guide sets its client timer to zero at action0
                        # (CupGachaSlotDialog:463-473). Local server mirrors this
                        # for the ONE receipted tutorial gift, never arbitrary cups.
                        guide_gift=db.execute('SELECT 1 FROM local_gacha_draws WHERE uid=? AND boundary=? AND purpose=?',(p.uid,run,'cup-guide')).fetchone()
                        instant=ident==1001 and guide_gift and p.noticeFlagData.noticeFlags.value[27]&15==1
                        deadline=int(self.clock())+(0 if instant else d.cupGachaMap[ident].cookMin*60)
                        db.execute('UPDATE local_cup_runs SET deadline=? WHERE run_id=?',(deadline,run))
                    self.project(p,db)
                    result=c.Int(p.cupGachaData.restSec)
                else:
                    # Early opening fee mirrors the UI, using the shortened deadline.
                    remain=max(0,(deadline if deadline is not None else int(self.clock())+d.cupGachaMap[ident].cookMin*60)-int(self.clock()))
                    tier=d.rule.cupGachaOpenMinPerTier*60
                    if tier<=0:raise ValueError('invalid cup early-open tier')
                    cost=((remain+tier-1)//tier)*d.rule.cupGachaOpenMetalPerTier
                    self.debit(p,c.ItemParam(kind=1,id=0,num=cost))
                    result=c.ObjArray([self.cup_result(p,d,ident),c.Int(cost)])
                    db.execute('INSERT INTO local_gacha_draws VALUES(?,?,?,?,?,?)',
                        (str(uuid.uuid4()),p.uid,run,'cup-open',encode(result),int(self.clock())))
                    db.execute('UPDATE local_cup_runs SET claimed_unix=? WHERE run_id=?',(int(self.clock()),run))
                    p.cupGachaData.cupGachaIds.value[slot]=0
                    p.cupGachaData.showAdNum=0
                    self.project(p,db)
            elif purchase:
                ident,kind,quantity=ints
                if kind!=19 or ident not in CUPS or quantity!=1:raise ValueError('only one supported ready cup per purchase')
                if not db.execute('SELECT 1 FROM shop_visits WHERE uid=?',(p.uid,)).fetchone():
                    raise ValueError('enter shop before purchasing cups')
                token=request_token(session,request_fingerprint)
                if db.execute("SELECT 1 FROM local_gacha_draws WHERE uid=? AND boundary=? AND purpose='cup-purchase'",
                              (p.uid,token)).fetchone():
                    raise ValueError('cup purchase request already processed')
                definition=d.cupGachaMap[ident]
                if definition.cookMin or not isinstance(definition.price,c.ItemParam) or definition.conditionDesc:
                    raise ValueError('cup purchase conditions UNKNOWN')
                self.debit(p,definition.price)
                result=c.ObjArray([definition.price,c.ObjArray([self.cup_result(p,d,ident)])])
                db.execute('INSERT INTO local_gacha_draws VALUES(?,?,?,?,?,?)',
                    (str(uuid.uuid4()),p.uid,token,'cup-purchase',encode(result),int(self.clock())))
            elif typ==PLACE:
                owned=p.gudetamaMap.get(ints[0])
                if not owned or owned.count<=0 or ints[0] not in d.gudetamaMap or not d.gudetamaMap[ints[0]].isCup:
                    raise ValueError('cup placement requires an obtained cup character')
                p.placedGudetamaId=ints[0]
                result=c.Null()
            else:raise ValueError('unsupported lottery request')
            db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))
            # Primary callbacks already apply awards/payments; no repeated deltas.
            callback_cost=(use.num if typ in (PLAY,FREE,STAMP) and isinstance(use,c.ItemParam) and use.kind==0 else 0)
            extra=[c.String(f'touch_u:{p.freeMoney+callback_cost}') if isinstance(x,c.String) and x.value.startswith('touch_u:') else x for x in extra]
            extra.extend([local_voices.helper_extra(p,d)])
            from . import missions
            extra.extend(missions.extras(p,db,d))
            result,extra=result,c.ObjArray(extra)
            encode(result);encode(extra)
            LOG.info('local_lottery_prepared uid=%s type=%s',p.uid,typ)
            return result,extra
        return accounts.transact(session.uiid,operation)
