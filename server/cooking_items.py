"""Original item wire flow, local adoption of the client's roulette modifiers.

Selection is free; consume at COMPLETE. Official server algorithms UNKNOWN.
"""
import math
from .library import c
from .protocol import encode, decode
from . import gameplay,roulette_layout

SELECT = 134217924
SUPPORTED = frozenset((11,12,13,14,21,22,23,24,31,32,33))


def ensure(db):
    db.execute('''CREATE TABLE IF NOT EXISTS cooking_item_selections(
        run_id TEXT PRIMARY KEY REFERENCES cooking_runs(run_id),
        items BLOB NOT NULL,consumed_unix INTEGER)''')


def selected(db,run):
    ensure(db)
    row=db.execute('SELECT items FROM cooking_item_selections WHERE run_id=?',(run,)).fetchone()
    return decode(row[0]).value if row else []


def validate(p,d,r,ids):
    if len(ids)>len(SUPPORTED) or len(set(ids))!=len(ids):raise ValueError('duplicate/too many cooking items')
    assist=p.kitchenwareMap[r['kitchen_type']].assistUsefulIds
    unique={a.type for ident in ([] if gameplay.null(assist) else assist.value)
            for a in d.usefulMap[ident].assistAbilities.value if a.type&512}
    for ident in ids:
        u=d.usefulMap.get(ident)
        owned=p.usefulMap.get(ident)
        # kitchenwareTypes belongs to the hurry-item filters in
        # UserDataWrapper.as:1024-1135, not CookingUsefulDialog's selection.
        if (ident not in SUPPORTED or not u or not u.usable&2 or u.event or u.eventId or u.privately
                or not owned or owned.num<1):
            raise ValueError('unavailable/ineligible cooking item')
        for a in u.abilities.value:
            if a.type not in (2,515,516) or a.secs!=0 or not isinstance(a.values,c.IntArray) or len(a.values.value)!=1 or a.values.value[0]<=0:
                raise ValueError('unknown cooking item ability')
            if a.type&512:unique.add(a.type)
            if a.type==516 and not any(x.type==1 for x in d.gudetamaMap[r['gudetama_id']].roulettes.value):
                raise ValueError('character has no happening segment')
    if len(unique)>1:raise ValueError('success and happening modifiers are mutually exclusive')


def select(p,db,d,r,packet):
    if r['status']!='roulette':raise ValueError('select cooking items before spinning')
    if not isinstance(packet.payloadInt,c.IntArray):raise ValueError('cooking item IDs required')
    ids=gameplay.integers(packet.payloadInt,len(packet.payloadInt.value))
    validate(p,d,r,ids)
    db.execute('INSERT OR REPLACE INTO cooking_item_selections VALUES(?,?,NULL)',(r['run_id'],encode(c.IntArray(ids))))
    return c.ObjArray([])  # RouletteDialog ignores response entries.


def weights(parts,ids,d,assist_ids=()):
    """RouletteDialog.as:452-561, unrotated; speed stays client-side.

    Adopt the display formula as a LOCAL settlement rule. Failure segments
    donate first, then opposite outcome; ascending size/start distribution.
    """
    result=[list(x) for x in parts]
    for ability,target,opposite in ((515,0,1),(516,1,0)):
        amount=sum(a.values.value[0] for ident in ids for a in d.usefulMap[ident].abilities.value if a.type==ability)
        amount+=sum(a.values.value[0] for ident in assist_ids for a in d.usefulMap[ident].assistAbilities.value if a.type==ability)
        remaining=amount
        order=sorted(range(len(result)),key=lambda i:(result[i][1],i))
        for donor in (2,opposite):
            eligible=[i for i in order if result[i][0]==donor]
            for pos,i in enumerate(eligible):
                take=min(remaining,result[i][1],math.ceil(remaining/(len(eligible)-pos)))
                result[i][1]-=take;remaining-=take
        moved=amount-remaining
        if moved:
            eligible=[i for i in order if result[i][0]==target]
            if not eligible:
                result.append([target,0]);eligible=[len(result)-1]
            for pos,i in enumerate(eligible):
                add=min(moved,math.ceil(moved/(len(eligible)-pos)))
                result[i][1]+=add;moved-=add
    return [(t,w) for t,w in result]


def consume(p,db,d,r,rules,now):
    ids=selected(db,r['run_id'])
    if ids:
        validate(p,d,r,ids)
        changed=db.execute('UPDATE cooking_item_selections SET consumed_unix=? WHERE run_id=? AND consumed_unix IS NULL',
                           (now,r['run_id']))
        if changed.rowcount!=1:raise ValueError('cooking items already consumed')
        for ident in ids:p.usefulMap[ident].num-=1
    gd,rd=d.gudetamaMap[r['gudetama_id']],d.recipeNoteMap[r['recipe_id']]
    limit=0
    assist=p.kitchenwareMap[r['kitchen_type']].assistUsefulIds
    base=roulette_layout.saved(db,r['run_id'],rules.candidates(d,rd,gd))
    for typ,weight in weights(base,ids,d,() if gameplay.null(assist) else assist.value):
        limit+=weight
        if r['percent']<limit:
            if typ!=r['result_type']:
                choices=[gd.id] if typ==0 else rd.happeningIds.value if typ==1 else rd.failureIds.value
                if not choices:raise ValueError('modified outcome has no configured candidates')
                ident=choices[rules.random_below(len(choices))]
                db.execute('UPDATE cooking_runs SET result_type=?,result_id=?,reward=? WHERE run_id=?',
                           (typ,ident,d.gudetamaMap[ident].reward,r['run_id']))
            return
    raise ValueError('invalid modified roulette percent')


def inventory_extra(p,db,run):
    ids=selected(db,run)
    return [c.ObjArray([c.String('useful:'),c.UsefulInfo(
        updateUsefuls=c.ObjArray([p.usefulMap[i] for i in ids]),removeUsefulIds=c.IntArray([]))])] if ids else []
