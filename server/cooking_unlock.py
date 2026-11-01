"""Original 134217925 layout; local atomic material-unlock implementation.

CookingScene.as:3733-3752 receives GudetamaData and consumes requiredGudetamas
once in its callback. Materials unlock a recipe character, not each cooking run.
"""
import time
from collections import Counter
from . import gameplay
from .protocol import encode


def unlock(p, db, d, engine, gid):
    if p.noticeFlagData.tutorialProgress < 7:
        raise ValueError('finish tutorial before material unlock')
    if gid not in engine.rules.settings['gudetama_ids']:
        raise ValueError('outside configured character policy')
    eligible = any(rid in engine.rules.settings['recipe_ids'] and not rd.eventId
                   and gid in rd.defaults.value + rd.appends.value
                   and (note := p.recipeNoteMap.get(rid)) and note.purchased and note.available
                   and (k := p.kitchenwareMap.get(d.kitchenwareMap[rd.kitchenwareId].type))
                   and (part := k.paramMap.get(rd.kitchenwareId)) and part.available
                   for rid, rd in d.recipeNoteMap.items())
    if not eligible:raise ValueError('character recipe/kitchen not owned')
    engine.enable_candidates(p,db,d)
    gd, role = d.gudetamaMap.get(gid), p.gudetamaMap.get(gid)
    if not gd or not role or not role.available:raise ValueError('character prerequisite not met')
    if role.unlocked:raise ValueError('character already unlocked; materials not consumed')
    if gameplay.null(gd.requiredGudetamas) or not gd.requiredGudetamas.value:
        raise ValueError('no material unlock configured')
    costs = Counter()
    for item in gd.requiredGudetamas.value:
        if item.kind != 7 or item.id not in d.gudetamaMap or item.num <= 0:
            raise ValueError('unsupported unlock material')
        costs[item.id] += item.num
    if any(i not in p.gudetamaMap or p.gudetamaMap[i].count < n for i,n in costs.items()):
        raise ValueError('insufficient recipe materials')
    db.execute('CREATE TABLE IF NOT EXISTS cooking_unlock_receipts(uid INTEGER NOT NULL,gudetama_id INTEGER NOT NULL,materials BLOB NOT NULL,created_unix INTEGER NOT NULL,PRIMARY KEY(uid,gudetama_id))')
    db.execute('INSERT INTO cooking_unlock_receipts VALUES(?,?,?,?)',
               (p.uid,gid,encode(gd.requiredGudetamas),int(time.time())))
    for i,n in costs.items():p.gudetamaMap[i].count -= n
    role.unlocked = True
    return role
