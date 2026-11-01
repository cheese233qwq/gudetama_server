"""Local transactional acceleration using archived costs and response layouts."""
import logging
from .library import c
from .protocol import encode
from .state import request_token
from . import gameplay

METAL,ITEM,USUALLY=134217911,134217971,134217976
TYPES={METAL,ITEM,USUALLY}
LOG=logging.getLogger('gudetama.local')


def process(accounts,packet,session,d,engine,*,request_fingerprint):
    if packet.type not in TYPES or not session.initialized or any(not gameplay.null(x) for x in (packet.payloadObj0,packet.payloadObj1)):
        raise ValueError('invalid cooking acceleration payload')
    args=gameplay.integers(packet.payloadInt,3 if packet.type==USUALLY else 2)
    token=request_token(session,request_fingerprint)
    def operation(p,db):
        if p.noticeFlagData.tutorialProgress<7:raise ValueError('ordinary acceleration requires completed tutorial')
        extra=gameplay.settle_touch(p,db,packet.payloadExtra,d)
        db.execute('''CREATE TABLE IF NOT EXISTS cooking_acceleration_receipts(
            uid INTEGER NOT NULL REFERENCES accounts(uid),request_id TEXT NOT NULL,
            run_id TEXT NOT NULL REFERENCES cooking_runs(run_id),packet_type INTEGER NOT NULL,
            item_id INTEGER NOT NULL,quantity INTEGER NOT NULL,before_deadline INTEGER NOT NULL,
            after_deadline INTEGER NOT NULL,created_unix INTEGER NOT NULL,
            PRIMARY KEY(uid,request_id))''')
        if db.execute('SELECT 1 FROM cooking_acceleration_receipts WHERE uid=? AND request_id=?',(p.uid,token)).fetchone():
            raise ValueError('cooking acceleration request already processed')
        row=db.execute("SELECT run_id,deadline_unix FROM cooking_runs WHERE uid=? AND kitchen_type=? AND status='cooking'",
                       (p.uid,args[0])).fetchone()
        now=int(engine.clock())
        if not row or row[1]<=now:raise ValueError('no unfinished cooking in this kitchen')
        remaining=row[1]-now
        ident=0
        if packet.type==METAL:
            index=args[1]
            unit=d.rule.hurryUpReduceMinutesPerMetal*60
            base=d.rule.hurryUpMetalBase
        else:
            ident=args[1]
            item=d.usefulMap.get(ident)
            special=packet.type==ITEM and ident in (62,63) and args[0]==4
            if special:
                from . import event_gameplay
                bound=db.execute('SELECT cycle_id,hurry_item FROM local_event_cooking_runs WHERE run_id=?',(row[0],)).fetchone()
                if not bound or bound[1]:raise ValueError('event hurry item already selected or no event run')
                cycle=db.execute('SELECT event_id,deadline_unix,settled_unix FROM local_event_cycles WHERE cycle_id=?',(bound[0],)).fetchone()
                if not cycle or cycle[0]!=item.eventId or cycle[1]<=now or cycle[2] is not None:raise ValueError('event hurry item out of term')
                unit,base,index=remaining,1,0
                db.execute('UPDATE local_event_cooking_runs SET hurry_item=? WHERE run_id=?',(ident,row[0]))
            elif (not item or not item.usable&4 or item.event or item.eventId or item.privately
                    or not gameplay.null(item.kitchenwareTypes) and args[0] not in item.kitchenwareTypes.value):
                raise ValueError('unsupported or ineligible cooking acceleration item')
            if not special:
                minutes=d.rule.hurryUpReduceMinutesPerItem.get(ident)
                per_item=d.rule.hurryUpItemBaseMap.get(ident,c.Int(1))
                if not isinstance(minutes,c.Int) or not isinstance(per_item,c.Int):
                    raise ValueError('missing configured item acceleration rule')
                unit,base=minutes.value*60,per_item.value
                index=args[2] if packet.type==USUALLY else 0
        if unit<=0 or base<=0 or index<0 or index>=(remaining+unit-1)//unit:
            raise ValueError('invalid cooking acceleration amount')
        quantity=(index+1)*base
        if packet.type==METAL:
            if p.chargeMetal:raise ValueError('paid gold balances are not supported by local acceleration')
            if p.freeMetal<quantity:raise ValueError('insufficient free gold for cooking acceleration')
            p.freeMetal-=quantity
        else:
            owned=p.usefulMap.get(ident)
            if not owned or owned.num<quantity:raise ValueError('insufficient cooking acceleration items')
            owned.num-=quantity
        # Local saturation policy: completion uses -1, matching the existing
        # cooking engine. Absolute deadlines survive server restart.
        deadline=max(now-1,row[1]-(index+1)*unit)
        if deadline==now:deadline=now-1
        db.execute('UPDATE cooking_runs SET deadline_unix=? WHERE run_id=?',(deadline,row[0]))
        engine.project(p,db)
        result=c.ObjArray([p.kitchenwareMap[args[0]],c.IntArray([quantity]) if packet.type==METAL else owned])
        db.execute('INSERT INTO cooking_acceleration_receipts VALUES(?,?,?,?,?,?,?,?,?)',
            (p.uid,token,row[0],packet.type,ident,quantity,row[1],deadline,now))
        db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))
        extras=c.ObjArray(extra) if extra else None
        encode(result)
        if extras is not None:encode(extras)
        return result,extras
    result=accounts.transact(session.uiid,operation)
    LOG.info('cooking_acceleration_committed type=%s kitchen=%s',packet.type,args[0])
    return result
