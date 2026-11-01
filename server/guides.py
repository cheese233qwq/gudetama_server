"""NON-OFFICIAL activation policy for the original GameDef notice scripts.

Do not enable tutorials whose interruptions require unavailable backend systems.
Client scripts, dialogue, arrows and completion packet 210 remain unmodified.
"""
import time
from .library import c
from .protocol import encode

# Full inventory, including explicit dependency blockers (not fake completion).
BLOCKED = {
    0:'GameDef6045 has no script1000 or confirmed caller',
    5:'friend-list backend and local friend relationship lifecycle',
    8:'mission reward tutorial activation/resume not verified; three mission presents supported',
    9:'normal mission tutorial/full catalogue; only three normal missions supported',
    10:'daily mission supply/evaluation/reset lifecycle',
    11:'friend detail backend and real local peer',
    12:'friend visit/assist backend and real local peer',
    18:'gacha requests, candidate validation and award transaction',
    19:'SNS icon feature is not enabled by the current backend',
    21:'event mission backend and enabled event',
    24:'event kitchenware lifecycle',
    25:'hidden-character spawn/claim lifecycle',
    28:'home decoration placement/inventory backend',
}
SUPPORTED = frozenset(set(range(31))-set(BLOCKED))


def sync(player,db,definition,*,rare_unlocked=False):
    """Open eligible original guides, in the caller's player transaction.

    Official activation thresholds are UNKNOWN. Only 0 -> 1 is automatic;
    1 -> 2 is exclusively the source-confirmed completion request.
    """
    from . import tutorial
    if not tutorial.enabled(db) or player.noticeFlagData.tutorialProgress < 7:
        return False
    flags = bytearray(player.noticeFlagData.noticeFlags.value)
    if len(flags) != 31:raise ValueError('unknown notice flag layout')
    done = lambda n:flags[n] & 15 == 2
    owned = lambda n:bool(player.utensilMap.get(n) and player.utensilMap[n].acquired)
    features = {x.value if isinstance(x,c.Int) else x for x in player.features.value}
    has_rare = any(g.count > 0 and g.unlockedVoiceIndex & 2 for g in player.gudetamaMap.values())
    candidates = {1,2}
    from . import events,event_gameplay
    if any(event_gameplay.profile(definition,eid) for eid,deadline in events.active(db)):
        candidates.add(23)  # Local activation: only a playable, in-term ranking.
    if done(2) and owned(1):candidates.add(3)
    if player.freeMetal+player.chargeMetal > 0:candidates.add(4)
    if done(2):
        if not owned(3):candidates.add(15)
        if 9 in features:candidates.add(7)
        if 14 in features:candidates.add(26)
    if done(26) and 14 in features:candidates.add(6)
    if owned(3):candidates.add(16)
    if owned(2):candidates.update((14,17))
    if player.rank >= 50 and player.utensilMap.get(4) and player.utensilMap[4].available:candidates.add(22)
    if any(g.available and not g.unlocked and g.count == 0 for g in player.gudetamaMap.values()):candidates.add(13)
    if owned(6) and (has_rare or rare_unlocked):candidates.add(20)
    if owned(6) and done(3) and definition.screening.flags.value[15]:candidates.add(29)
    # Never start notice3 and notice30 together; CollectionScene reuses one panel.
    if done(3) and done(20) and has_rare:candidates.add(30)
    if done(2) and 15 in features:candidates.add(27)  # Local activation, not a recovered level threshold.
    opened = sorted(i for i in candidates if i in SUPPORTED and flags[i] & 15 == 0)
    if not opened:return False
    for i in opened:
        if 1000+i not in definition.guideTalkTable:raise ValueError('missing original notice script')
    before = encode(player)
    db.execute('CREATE TABLE IF NOT EXISTS guide_activation_audit(uid INTEGER NOT NULL,notice_id INTEGER NOT NULL,before_player BLOB NOT NULL,created_unix INTEGER NOT NULL,policy TEXT NOT NULL,PRIMARY KEY(uid,notice_id))')
    for i in opened:
        flags[i] = (flags[i] & 240) | 1
        db.execute('INSERT OR IGNORE INTO guide_activation_audit VALUES(?,?,?,?,?)',
                   (player.uid,i,before,int(time.time()),'local-supported-notice-chain-v1'))
    player.noticeFlagData.noticeFlags = c.ByteArray(bytes(flags))
    db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
    return True


def extras(player,db,definition,**kwargs):
    return [player.noticeFlagData] if sync(player,db,definition,**kwargs) else []
