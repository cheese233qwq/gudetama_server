"""Character prerequisites and repair of old local automatic gacha grants.

Defaults use the client's locked silhouette. Appends are gacha recipes and
must not be granted just by buying a recipe note. Dynamic counters are local
interpretations of archived Japanese condition text, not official server code.
"""
import re
import time
from .library import c
from .protocol import decode, encode


def has_table(db, name):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None


def retained(p, db):
    """Keep actual collection, paid material unlocks and ongoing cooking."""
    ids = {i for i,g in p.gudetamaMap.items() if g.count or g.num or g.unlockedVoiceIndex
           or g.alreadyChallenge or g.cookedHappening or g.cookedFailure}
    ids.add(p.placedGudetamaId)
    ids.update(row[0] for row in db.execute(
        "SELECT gudetama_id FROM cooking_runs WHERE uid=? AND status IN ('cooking','roulette','spinning','resolved')",(p.uid,)))
    if has_table(db,'cooking_unlock_receipts'):
        ids.update(row[0] for row in db.execute('SELECT gudetama_id FROM cooking_unlock_receipts WHERE uid=?',(p.uid,)))
    return ids


def repair_appends(p, db, d):
    """Remove only proven empty placeholders introduced by the old policy.

    Full prior player bytes are retained in the same transaction. Genuine
    gacha/BOX recipe awards take precedence, even with zero character count.
    Unattributed legacy records are kept instead of guessing their origin.
    """
    name = 'local-cooking-character-progression-v1'
    if db.execute('SELECT 1 FROM player_migrations WHERE uid=? AND name=?',(p.uid,name)).fetchone():
        return
    before = encode(p)
    keep = retained(p,db)
    if has_table(db,'local_gacha_draws'):
        for row in db.execute("SELECT result FROM local_gacha_draws WHERE uid=? AND purpose LIKE 'normal:%'",(p.uid,)):
            result = decode(row[0])
            if not isinstance(result,c.GachaResult):raise ValueError('unknown saved gacha recipe award')
            keep.update(item.id for item in result.items.value if item.kind in (6,7))
    if has_table(db,'normal_mission_presents'):
        for row in db.execute('SELECT mail FROM normal_mission_presents WHERE uid=? AND claimed_unix IS NOT NULL',(p.uid,)):
            item = decode(row[0]).item
            if item.kind in (6,7):keep.add(item.id)
    appends = {gid for rd in d.recipeNoteMap.values() if not rd.eventId
               and d.kitchenwareMap[rd.kitchenwareId].type in (0,1,2,3) for gid in rd.appends.value}
    for gid in appends - keep:
        owned = p.gudetamaMap.get(gid)
        if owned is None:continue
        old = db.execute('SELECT before_player FROM player_migrations WHERE uid=? AND name=?',
                         (p.uid,f'local-compatible-cooking-candidate-{gid}')).fetchone()
        if old and gid not in decode(old[0]).gudetamaMap:
            del p.gudetamaMap[gid]
    db.execute('INSERT INTO player_migrations VALUES(?,?,?,?)',(p.uid,name,before,int(time.time())))
    db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))


def progress(p, db, gd):
    """Return available/current/goal; fail closed for unrecognized conditions."""
    if gd.targetType == 0 and gd.targetId > 0:
        value = int(db.execute("SELECT 1 FROM cooking_runs WHERE uid=? AND result_id=? AND status='claimed' LIMIT 1",
                               (p.uid,gd.targetId)).fetchone() is not None)
        return bool(value),value,1
    if gd.targetType != -1:return False,0,0
    text = gd.conditionDesc.strip()
    if not text:return True,0,0
    rank = re.search(r'レベルが(\d+)',text)
    if rank:return p.rank>=int(rank[1]),p.rank,int(rank[1])
    voice = re.search(r'レアセリフを(\d+)種類',text)
    if voice:
        value = sum(bool(g.unlockedVoiceIndex&2) for g in p.gudetamaMap.values() if g.count or g.num)
        return value>=int(voice[1]),value,int(voice[1])
    challenge = re.search(r'チャレンジを(\d+)個クリア',text)
    if challenge:
        value = (db.execute('SELECT count(*) FROM normal_mission_presents WHERE uid=? AND mission_id BETWEEN 1 AND 999',
                            (p.uid,)).fetchone()[0] if has_table(db,'normal_mission_presents') else 0)
        return value>=int(challenge[1]),value,int(challenge[1])
    return False,0,0
