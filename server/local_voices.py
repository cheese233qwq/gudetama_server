"""Local first-voice grants and ladle-gated acquisition of archived rare voices."""
import logging
import time
from .library import ROOT, c
from .protocol import encode
from .paths import STATIC

LOG = logging.getLogger('gudetama.local')
UNLOCK, HELPER = 16777410,16777464
TYPES = {UNLOCK,HELPER}


def helper_extra(player,definition):
    # ResidentMenuUI_Gudetama.as:779-782 consumes this exact String.
    # Local rule: expose the archived helper until the placed role's rare voice
    # is collected. No random arrival timer or bonus currency is invented.
    ladle = player.utensilMap.get(6)
    data = player.gudetamaMap.get(player.placedGudetamaId)
    available = (player.noticeFlagData.tutorialProgress >= 7 and ladle and ladle.acquired
                 and data and not data.unlockedVoiceIndex & 2
                 and eligible(player,definition,player.placedGudetamaId,1))
    return c.String('helper:true' if available else 'helper:false')


def eligible(player, definition, gid, index=0):
    owned, gd = player.gudetamaMap.get(gid), definition.gudetamaMap.get(gid)
    if owned is None or gd is None or owned.count <= 0 or not owned.available:
        return False
    if index not in (0,1) or not isinstance(gd.voices, c.IntArray) or len(gd.voices.value) <= index:
        return False
    vd = definition.voiceMap.get(gd.voices.value[index])
    # Simple archived MP3 only. Composite/missing audio remains unsupported.
    if vd is None or vd.type != 1 or vd.gudetamaId != gid or vd.rsrc <= 0 or not isinstance(vd.params,c.Null):
        return False
    path = STATIC / 'rsrc/voice' / f'{vd.rsrc}.mp3'
    if not path.is_file():
        return False
    with path.open('rb') as file:
        return not file.read(128).startswith(b'version https://git-lfs.github.com/spec/v1')


def process(accounts,packet,session,definition):
    from . import gameplay
    if not session.initialized or packet.type not in TYPES or not gameplay.null(packet.payloadObj0) or not gameplay.null(packet.payloadObj1):
        raise ValueError('invalid voice request')
    selector = gameplay.integers(packet.payloadInt,1)[0]
    if selector not in (-1,-2):raise ValueError('unknown voice selector')
    index = -selector-1
    def operation(player,db):
        extra = gameplay.settle_touch(player,db,packet.payloadExtra,definition)
        if player.noticeFlagData.tutorialProgress < 7:raise ValueError('complete tutorial before local voice acquisition')
        ladle = player.utensilMap.get(6)
        if index == 1 and (not ladle or not ladle.acquired):raise ValueError('buy talking ladle before rare voice')
        gid = player.placedGudetamaId
        if not eligible(player,definition,gid,index):raise ValueError('owned character voice asset unavailable')
        data = player.gudetamaMap[gid]
        if packet.type==UNLOCK and index==1 and not data.unlockedVoiceIndex & 2:
            from . import home_events
            from .protocol import decode
            home_events.ensure(db)
            # Packet has no event-expiry/ACK field. Keep this authorization
            # durable across idle/offline periods; the saved unlock bit makes
            # consuming it again harmless and prevents a second grant.
            issued=db.execute("SELECT event FROM local_touch_events WHERE uid=? AND gudetama_id=? AND kind='voice'",(player.uid,gid)).fetchall()
            if not any(decode(r[0]).voice==-2 for r in issued):raise ValueError('rare touch voice was not issued')
        if not data.unlockedVoiceIndex & (1 << index):
            db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',
                       (player.uid,f'local-voice-{gid}-{index}',encode(player),int(time.time())))
            data.unlockedVoiceIndex |= 1 << index
            db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
        from . import guides
        extra.extend(guides.extras(player,db,definition,rare_unlocked=index == 1))
        # HomeScene.as:2353-2390: [nullable GetItemResult], client unlocks bit.
        # No invented bonus item; helper acquisition is deterministic local policy.
        result,extras = c.ObjArray([c.Null()]),c.ObjArray(extra) if extra else None
        encode(result)
        if extras is not None:encode(extras)
        return result,extras
    result = accounts.transact(session.uiid,operation)
    LOG.info('local_voice_committed selector=%s policy=owned_ladle_helper',selector)
    return result


def unlock_first(player, definition, gid):
    # UserDataWrapper.as:3684-3703: bit 0 is voices[0], bit 1 voices[1].
    if eligible(player,definition,gid):
        owned = player.gudetamaMap[gid]
        if not owned.unlockedVoiceIndex & 1:
            owned.unlockedVoiceIndex |= 1
            LOG.info('local_voice_prepared uid=%s character=%s index=0 policy=collected_first_voice',player.uid,gid)
            return True
    return False


def restore_collected(player, db, definition):
    pending = [gid for gid,owned in player.gudetamaMap.items()
               if not owned.unlockedVoiceIndex & 1 and eligible(player,definition,gid)]
    if not pending:
        return
    db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',
               (player.uid,'local-compatible-collected-first-voice-v1',encode(player),int(time.time())))
    for gid in pending:
        unlock_first(player,definition,gid)
    db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
