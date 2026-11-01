"""Optional local pity/conversion rules; no claim of official probability recovery."""
from .library import c
from . import gacha_settings,restoration


def draw(engine,p,db,d,pool_id,pool,count):
    settings=restoration.policy()
    db.execute('CREATE TABLE IF NOT EXISTS local_gacha_pity(uid INTEGER NOT NULL,pool INTEGER NOT NULL,misses INTEGER NOT NULL,PRIMARY KEY(uid,pool))')
    row=db.execute('SELECT misses FROM local_gacha_pity WHERE uid=? AND pool=?',(p.uid,pool_id)).fetchone()
    misses=row[0] if row else 0
    items=[];params=[];converted=[];rarities=[];compensation=0
    for _ in range(count):
        choices=pool
        if settings['pity_draws'] and misses+1>=settings['pity_draws']:
            rare=[x for x in pool if x.rate>0 and gacha_settings.appearance(d,x.item)>=settings['pity_minimum_egg']]
            if rare:choices=rare # Never insert a prize outside the selected pool.
        item=engine.choose([x.item for x in choices],[x.rate for x in choices])
        rarity=gacha_settings.appearance(d,item)
        misses=0 if rarity>=settings['pity_minimum_egg'] else misses+1
        owner=(p.decorationMap.get(item.id) if item.kind==9 else p.avatarMap.get(item.id) if item.kind==12
               else p.gudetamaMap.get(item.id) if item.kind==6 else None)
        duplicate=bool(owner and (getattr(owner,'acquired',False) or item.kind==6 and owner.unlocked))
        param=engine.award(p,d,item)
        conversion=c.Null()
        if duplicate and settings['duplicate_unique_gp']:
            conversion=c.ItemParam(kind=0,id=0,num=settings['duplicate_unique_gp']*item.num)
            restoration.award(p,d,conversion);compensation+=conversion.num
        items.append(item);params.append(param);converted.append(conversion);rarities.append(rarity)
    db.execute('INSERT INTO local_gacha_pity VALUES(?,?,?) ON CONFLICT(uid,pool) DO UPDATE SET misses=excluded.misses',(p.uid,pool_id,misses))
    return items,params,converted,rarities,compensation
