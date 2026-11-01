"""Local operator-selected archived pools; not an official event schedule."""
import json

DEFAULT = (1, 3)


def active(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='local_gacha_settings'").fetchone():
        return DEFAULT
    row = db.execute("SELECT value FROM local_gacha_settings WHERE name='active_pools'").fetchone()
    return tuple(json.loads(row[0])) if row else DEFAULT


def select(db, definition, ids):
    if (not isinstance(ids, list) or not ids or len(ids) > len(definition.gachaMap)
            or any(type(i) is not int or i not in definition.gachaMap for i in ids)
            or len(set(ids)) != len(ids)):
        raise ValueError('select distinct archived pool IDs')
    for ident in ids:
        pool = definition.gachaMap[ident]
        if not pool.screeningItems.value or any(x.item.kind not in (6,7,8,9,11,12)
                                               for x in pool.screeningItems.value):
            raise ValueError('pool contains unsupported rewards')
    db.execute('CREATE TABLE IF NOT EXISTS local_gacha_settings(name TEXT PRIMARY KEY,value TEXT NOT NULL)')
    db.execute('INSERT OR REPLACE INTO local_gacha_settings VALUES(?,?)',
               ('active_pools', json.dumps(ids)))


def appearance(definition, item):
    """Local mapping only. Client wire values 0/1/2 are confirmed.

    Character stars 0..1 -> white, 2..3 -> silver, 4 -> gold.
    Stamps with rare flag 1/2 -> gold, ordinary stamps/other goods white.
    StampDef flags 1/2 mean automatic/manual rare, not silver/gold ranks.
    Official reward-to-animation classification is UNKNOWN.
    """
    if item.kind in (6,7):
        star = definition.gudetamaMap[item.id].rarity
        return 2 if star >= 4 else 1 if star >= 2 else 0
    if item.kind == 11:
        return 2 if definition.stampMap[item.id].rare in (1,2) else 0
    return 0
