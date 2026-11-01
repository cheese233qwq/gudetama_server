"""Local timed GP/probability buffs using original 189/ability:/touch_info:.

Pin one random configured bonus per use instead of trusting client randomness.
Heaven/voice probabilities are implemented separately in home_events.
"""
import secrets
import time
from .library import c
from .protocol import encode, decode
from .state import request_token
from . import gameplay

USE = 189
SUPPORTED = frozenset((1, 2, 42, 43, 44, 45))


def ensure(db):
    db.execute('''CREATE TABLE IF NOT EXISTS local_home_buffs(
        uid INTEGER PRIMARY KEY REFERENCES accounts(uid), item_id INTEGER NOT NULL,
        bonus INTEGER NOT NULL, deadline_unix INTEGER NOT NULL, pending_closed INTEGER NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS local_home_item_receipts(
        uid INTEGER NOT NULL REFERENCES accounts(uid), request_id TEXT NOT NULL,
        item_id INTEGER NOT NULL, result BLOB NOT NULL, extras BLOB NOT NULL,
        PRIMARY KEY(uid,request_id))''')


def row(db, uid):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='local_home_buffs'").fetchone():
        return None
    return db.execute('SELECT item_id,bonus,deadline_unix,pending_closed FROM local_home_buffs WHERE uid=?', (uid,)).fetchone()


def bonus_credit(p, db, counts, bonus):
    if not bonus:
        return 0
    buff = row(db, p.uid)
    if (p.noticeFlagData.tutorialProgress < 7 or not buff or buff[3]
            or bonus != counts[0] * buff[1]):
        raise ValueError('unissued or invalid item touch bonus')
    return bonus


def synchronize(p, db, definition, now=None):
    buff = row(db, p.uid)
    if not buff:
        return []
    now = int(time.time()) if now is None else now
    alive = now < buff[2]
    p.userAbilities = c.ObjArray([a for a in p.userAbilities.value if a.ability.type != 257])
    if alive:
        a = definition.usefulMap[buff[0]].abilities.value[0]
        p.userAbilities.value.append(c.UserAbilityData(ability=a, restTimeSecs=buff[2]-now))
    # Only the ordinary-touch bonus changes. Preserve tutorial/voice parameters.
    values = [buff[1], buff[1]] if alive else []
    changed = p.touchInfo.bonusRange.value != values
    p.touchInfo.bonusRange = c.IntArray(values)
    frames = [c.ObjArray([c.String('ability:'), p.userAbilities])]
    # Do not re-arm outstanding voice/heaven events on every request.
    if changed:
        from . import home_events
        home_events.issue(p,db,definition,refresh=True)
        frames.append(c.ObjArray([c.String('touch_info:'), p.touchInfo]))
    return frames


def close_pending(p, db, extras, now=None):
    buff = row(db, p.uid)
    now = int(time.time()) if now is None else now
    if buff and now >= buff[2] and isinstance(extras, c.ObjArray):
        # Local late-batch policy: one final pending batch may arrive after the
        # deadline (offline/relogin). Receipts still prevent repeat settlement.
        if any(isinstance(x,c.String) and x.value.startswith('send_touch:') for x in extras.value):
            db.execute('UPDATE local_home_buffs SET pending_closed=1 WHERE uid=?', (p.uid,))


def process(accounts, packet, session, definition, *, request_fingerprint):
    if not session.initialized or packet.type != USE or any(not gameplay.null(x) for x in (packet.payloadObj0,packet.payloadObj1)):
        raise ValueError('invalid home item payload')
    ident = gameplay.integers(packet.payloadInt, 1)[0]
    if ident not in SUPPORTED:
        raise ValueError('home item ability not restored; inventory unchanged')
    token = request_token(session, request_fingerprint)
    def operation(p, db):
        ensure(db)
        old = db.execute('SELECT item_id,result,extras FROM local_home_item_receipts WHERE uid=? AND request_id=?',(p.uid,token)).fetchone()
        if old:
            if old[0] != ident:
                raise ValueError('home item receipt reused')
            return decode(old[1]), decode(old[2])
        if p.noticeFlagData.tutorialProgress < 7:
            raise ValueError('complete tutorial before using home items')
        extra = gameplay.settle_touch(p,db,packet.payloadExtra,definition)
        useful = definition.usefulMap[ident]
        owned = p.usefulMap.get(ident)
        if not owned or owned.num < 1 or useful.event or useful.eventId or useful.privately or not useful.usable & 1:
            raise ValueError('home item unavailable or insufficient inventory')
        abilities = useful.abilities.value
        if ident in (1,2):
            from . import home_events
            if len(abilities)!=1 or abilities[0].type!={1:256,2:261}[ident] or abilities[0].secs<=0:
                raise ValueError('invalid probability item ability')
            home_events.ensure(db)
            now=int(time.time())
            previous=db.execute('SELECT deadline_unix FROM local_probability_buffs WHERE uid=? AND item_id=?',(p.uid,ident)).fetchone()
            if previous and previous[0]>now:raise ValueError('probability item already active')
            owned.num-=1
            db.execute('INSERT OR REPLACE INTO local_probability_buffs VALUES(?,?,?)',(p.uid,ident,now+abilities[0].secs))
            home_events.buffs(p,db,definition,now)
            extra.extend(home_events.issue(p,db,definition,refresh=True))
            extra.extend([c.ObjArray([c.String('ability:'),p.userAbilities]),
                c.ObjArray([c.String('useful:'),c.UsefulInfo(updateUsefuls=c.ObjArray([owned]),removeUsefulIds=c.IntArray([]))])])
            result,extras=c.ObjArray([]),c.ObjArray(extra)
            raw_result,raw_extras=encode(result),encode(extras)
            db.execute('INSERT INTO local_home_item_receipts VALUES(?,?,?,?,?)',(p.uid,token,ident,raw_result,raw_extras))
            db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))
            return result,extras
        if len(abilities) != 1 or abilities[0].type != 257 or not isinstance(abilities[0].values,c.IntArray) or len(abilities[0].values.value)!=2 or abilities[0].secs<=0:
            raise ValueError('unsupported configured item ability')
        lo, hi = sorted(abilities[0].values.value)
        if not 0 < lo <= hi <= 100:
            raise ValueError('invalid touch bonus configuration')
        now = int(time.time())
        previous = row(db,p.uid)
        if previous and now < previous[2]:
            raise ValueError('a GP bomb is already active; wait until it expires')
        bonus = lo + secrets.randbelow(hi-lo+1)
        owned.num -= 1
        db.execute('INSERT OR REPLACE INTO local_home_buffs VALUES(?,?,?,?,0)',(p.uid,ident,bonus,now+abilities[0].secs))
        extra = [x for x in extra if not (isinstance(x,c.ObjArray) and isinstance(x.value[0],c.String) and x.value[0].value in ('ability:','touch_info:'))]
        extra.extend(synchronize(p,db,definition,now))
        # UsefulDetailDialog consumes one locally before applying extras.
        extra.append(c.ObjArray([c.String('useful:'),c.UsefulInfo(updateUsefuls=c.ObjArray([owned]),removeUsefulIds=c.IntArray([]))]))
        result, extras = c.ObjArray([]), c.ObjArray(extra)
        raw_result, raw_extras = encode(result), encode(extras)
        db.execute('INSERT INTO local_home_item_receipts VALUES(?,?,?,?,?)',(p.uid,token,ident,raw_result,raw_extras))
        db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))
        return result, extras
    return accounts.transact(session.uiid,operation)
