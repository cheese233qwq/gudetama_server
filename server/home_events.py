"""Local touch-event scheduler. Probabilities are local, wire layouts original."""
import re
import logging
import secrets
import time
from .library import c
from .protocol import encode, decode
from . import gameplay, tutorial, local_voices

random_below = secrets.randbelow
LOG=logging.getLogger('gudetama.local')


def ensure(db):
    tutorial.schema(db)
    db.execute('''CREATE TABLE IF NOT EXISTS local_touch_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,uid INTEGER NOT NULL REFERENCES accounts(uid),
        event BLOB NOT NULL,kind TEXT NOT NULL,budget INTEGER NOT NULL,used INTEGER NOT NULL DEFAULT 0,
        received INTEGER NOT NULL DEFAULT 0,created_unix INTEGER NOT NULL,gudetama_id INTEGER NOT NULL)''')
    db.execute('CREATE INDEX IF NOT EXISTS touch_event_player ON local_touch_events(uid,id)')
    db.execute('''CREATE TABLE IF NOT EXISTS local_probability_buffs(
        uid INTEGER NOT NULL REFERENCES accounts(uid),item_id INTEGER NOT NULL,
        deadline_unix INTEGER NOT NULL,PRIMARY KEY(uid,item_id))''')


def buffs(p,db,d,now=None):
    ensure(db)
    now=int(time.time()) if now is None else now
    p.userAbilities=c.ObjArray([a for a in p.userAbilities.value if a.ability.type not in (256,261)])
    active={i:deadline for i,deadline in db.execute('SELECT item_id,deadline_unix FROM local_probability_buffs WHERE uid=? AND deadline_unix>?',(p.uid,now))}
    for i,deadline in active.items():
        p.userAbilities.value.append(c.UserAbilityData(ability=d.usefulMap[i].abilities.value[0],restTimeSecs=deadline-now))
    return active


def issue(p,db,d,*,refresh=False):
    if p.noticeFlagData.tutorialProgress<7:return []
    ensure(db)
    now=int(time.time())
    active=buffs(p,db,d,now)
    last=db.execute('SELECT id,event,used,received,created_unix FROM local_touch_events WHERE uid=? ORDER BY id DESC LIMIT 1',(p.uid,)).fetchone()
    if last and (not refresh or (not last[2] and not last[3])):
        # Ordinary responses never reset the client's event cursor.
        return []
    # Local checkpoint probabilities: heaven 2%, boosted to archived 95%;
    # otherwise rare voice 5%, boosted by archived factor10 to 50%.
    heaven_chance=d.usefulMap[1].abilities.value[0].values.value[0] if 1 in active else 2
    outstanding=db.execute("SELECT count(*) FROM local_touch_events WHERE uid=? AND kind='heaven' AND used<budget",(p.uid,)).fetchone()[0]
    heaven=random_below(100)<heaven_chance and outstanding<4
    rare_chance=min(100,5*(d.usefulMap[2].abilities.value[0].values.value[0] if 2 in active else 1))
    ladle=p.utensilMap.get(6)
    rare=not heaven and ladle and ladle.acquired and local_voices.eligible(p,d,p.placedGudetamaId,1) and random_below(100)<rare_chance
    from .restoration import policy
    drop=not heaven and not rare and random_below(100)<policy()['drop_percent']
    index=2+random_below(6) if drop else 0
    event=c.TouchEventParam(touchNum=3+random_below(10),event=2048 if heaven else 256,
                           voice=0 if heaven or not rare else -2,paramByte=20 if heaven else 0)
    if drop:event.event=512|index
    db.execute('INSERT INTO local_touch_events(uid,event,kind,budget,created_unix,gudetama_id) VALUES(?,?,?,?,?,?)',
               (p.uid,encode(event),'heaven' if heaven else f'drop{index}' if drop else 'voice',20 if heaven else 1,now,p.placedGudetamaId))
    p.touchInfo=c.TouchInfo(params=c.ObjArray([event]),bonusRange=p.touchInfo.bonusRange)
    LOG.info('local_touch_event_issued uid=%s kind=%s touch=%s voice=%s budget=%s',p.uid,'heaven' if heaven else f'drop{index}' if drop else 'voice',event.touchNum,event.voice,event.paramByte if heaven else 1)
    return [c.ObjArray([c.String('touch_info:'),p.touchInfo]),c.ObjArray([c.String('ability:'),p.userAbilities])]


def consume(db,uid,kind,num):
    if not num:return
    rows=db.execute('SELECT id,budget-used FROM local_touch_events WHERE uid=? AND kind=? AND used<budget AND ((kind!=\'heaven\' AND kind NOT LIKE \'drop%\') OR received=1) ORDER BY id',(uid,kind)).fetchall()
    missing=max(0,num-sum(r[1] for r in rows))
    if missing:
        old=db.execute('SELECT budget-used,received FROM tutorial_events WHERE uid=? AND kind=?',(uid,kind)).fetchone()
        if not old or old[0]<missing or kind=='heaven' and not old[1]:raise ValueError('unissued or excessive random touch reward')
        db.execute('UPDATE tutorial_events SET used=used+? WHERE uid=? AND kind=?',(missing,uid,kind))
        num-=missing
    for ident,remaining in rows:
        take=min(num,remaining)
        db.execute('UPDATE local_touch_events SET used=used+? WHERE id=?',(take,ident))
        num-=take
        if not num:break


def settle(p,db,extras,d):
    if gameplay.null(extras) or isinstance(extras,c.ObjArray) and not extras.value:return []
    ensure(db)
    # Preserve already-issued tutorial rewards when upgrading an old account.
    if not db.execute('SELECT 1 FROM local_touch_events WHERE uid=?',(p.uid,)).fetchone():
        return tutorial.settle_touch(p,db,extras,d)
    if not isinstance(extras,c.ObjArray) or any(not isinstance(x,c.String) for x in extras.value):raise ValueError('invalid touch extras')
    texts=[x.value for x in extras.value]
    touches=[x for x in texts if x.startswith('send_touch:')]
    heavens=[x for x in texts if x.startswith('send_heaven:')]
    drops=[x for x in texts if x.startswith('send_drop:')]
    if len(touches)>1 or len(heavens)>1 or len(drops)>1 or len(texts)!=len(touches)+len(heavens)+len(drops):raise ValueError('unsupported touch extras')
    if drops:
        matches=[r for r in db.execute("SELECT id,event FROM local_touch_events WHERE uid=? AND kind LIKE 'drop%' ORDER BY id DESC",(p.uid,)) if 'send_drop:'+tutorial.event_string(decode(r[1]))==drops[0]]
        if not matches:raise ValueError('drop event was not issued')
        db.execute('UPDATE local_touch_events SET received=1 WHERE id=?',(matches[0][0],))
    # Acknowledgement is keyed by the exact issued original event, never by a
    # client-supplied count or reward. Repeated ACK cannot enlarge its budget.
    if heavens:
        matches=[r for r in db.execute("SELECT id,event,received FROM local_touch_events WHERE uid=? AND kind='heaven' ORDER BY id DESC",(p.uid,)) if 'send_heaven:'+tutorial.event_string(decode(r[1]))==heavens[0]]
        if matches:
            db.execute('UPDATE local_touch_events SET received=1 WHERE id=?',(matches[0][0],))
        else:
            old=db.execute("SELECT event FROM tutorial_events WHERE uid=? AND kind='heaven'",(p.uid,)).fetchone()
            if not old or 'send_heaven:'+tutorial.event_string(decode(old[0]))!=heavens[0]:raise ValueError('heaven event was not issued')
            db.execute("UPDATE tutorial_events SET received=1 WHERE uid=? AND kind='heaven'",(p.uid,))
    if not touches:return []
    text=touches[0]
    match=re.fullmatch(r'send_touch:([0-9]+(?:,[0-9]+)*)-([0-9]+)-([0-9]+)-([01])',text)
    if not match:raise ValueError('invalid touch batch')
    counts=[int(x) for x in match[1].split(',')]
    counts += [0]*(9-len(counts))
    if len(counts)!=9 or not sum(counts) or max(counts)>2147483647:raise ValueError('unsupported touch counts')
    baseline=int(match[3])
    old=db.execute('SELECT request FROM touch_receipts WHERE uid=? AND baseline=?',(p.uid,baseline)).fetchone()
    if old:
        if old[0]!=text:raise ValueError('touch baseline already used')
    else:
        if baseline!=p.sendTouchCount:raise ValueError('stale/future touch baseline')
        consume(db,p.uid,'voice',counts[1]);consume(db,p.uid,'heaven',counts[8])
        for i in range(2,8):consume(db,p.uid,f'drop{i}',counts[i])
        from . import home_items
        bonus=home_items.bonus_credit(p,db,counts,int(match[2]))
        reward=(sum(n*w for n,w in zip(counts,d.rule.touchRewards.value))+bonus*d.rule.touchRewards.value[0])*p.rank
        if p.freeMoney+p.chargeMoney+reward>gameplay.MONEY_MAX or baseline+sum(counts)>2147483647:raise ValueError('touch reward overflow')
        p.freeMoney+=reward;p.sendTouchCount+=sum(counts)
        db.execute('INSERT INTO touch_receipts VALUES(?,?,?,?,?)',(p.uid,baseline,text,reward,int(time.time())))
        db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))
    return [c.String(f'touch_u:{p.freeMoney}'),c.String(f'touch_count:{p.sendTouchCount}')]
