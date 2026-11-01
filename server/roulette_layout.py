"""Local sector arrangement; archived outcome totals remain unchanged.

The official dynamic arrangement algorithm is unknown. Each new wheel may
split outcome areas into scattered sectors. Its exact layout is persisted so
display, item modifiers, manual stopping and settlement use the same wheel.
"""
import json


def ensure(db):
    db.execute('''CREATE TABLE IF NOT EXISTS cooking_roulette_layouts(
        run_id TEXT PRIMARY KEY REFERENCES cooking_runs(run_id),parts TEXT NOT NULL)''')


def arrange(parts,random_below):
    original=list(parts)
    totals={}
    for kind,size in original:totals[kind]=totals.get(kind,0)+size
    if len(totals)<2 or random_below(2)==0:
        return original
    rounds=2+random_below(2)
    chunks={}
    for kind,total in totals.items():
        count=min(rounds,max(1,total//5))
        remaining=total
        pieces=[]
        for slots in range(count,1,-1):
            average=remaining//slots
            low=max(5,average*2//3)
            high=min(remaining-5*(slots-1),max(low,average*4//3))
            size=low+random_below(high-low+1)
            pieces.append(size);remaining-=size
        chunks[kind]=pieces+[remaining]
    result=[]
    while chunks:
        options=[kind for kind in chunks if not result or kind!=result[-1][0]] or list(chunks)
        most=max(len(chunks[kind]) for kind in options)
        options=[kind for kind in options if len(chunks[kind])==most]
        kind=options[random_below(len(options))]
        result.append((kind,chunks[kind].pop(0)))
        if not chunks[kind]:del chunks[kind]
    return result


def create(db,run,parts,random_below,*,spread=True):
    layout=arrange(parts,random_below) if spread else list(parts)
    db.execute('INSERT INTO cooking_roulette_layouts VALUES(?,?)',
               (run,json.dumps(layout,separators=(',',':'))))
    return layout


def saved(db,run,fallback):
    row=db.execute('SELECT parts FROM cooking_roulette_layouts WHERE run_id=?',(run,)).fetchone()
    # Runs prepared by older servers retain their original sector order.
    return [tuple(x) for x in json.loads(row[0])] if row else list(fallback)
