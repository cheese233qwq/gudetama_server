"""Evidence-backed basic actions; no generated random events or rewards."""
import logging
import re
import time
from .library import c
from .protocol import encode

LOG = logging.getLogger("gudetama.local")
MONEY_MAX = 999999999  # UserData.as:15; local overflow policy rejects, never clamps.
TYPES = {59, 60, 62, 66, 114, 141, 142, 145, 149, 159, 190, 249, 201326757, 150995129}
CUP_RECIPE_LIST = 134217977
LOCAL_COLLECTION_TYPES = {166, 218, CUP_RECIPE_LIST}


def null(value):
    return value is None or isinstance(value, c.Null)


def integers(value, length):
    if not isinstance(value, c.IntArray) or len(value.value) != length:
        raise ValueError(f"expected IntArray of length {length}")
    return value.value


def settle_touch(player, db, extras, definition):
    from . import tutorial
    if tutorial.enabled(db):
        from . import home_items
        if player.noticeFlagData.tutorialProgress>=7:
            from . import home_events
            result = home_events.settle(player,db,extras,definition)
        else:
            result = tutorial.settle_touch(player,db,extras,definition)
        home_items.close_pending(player,db,extras)
        return result + home_items.synchronize(player,db,definition)
    if null(extras):
        return []
    if not isinstance(extras, c.ObjArray):
        raise ValueError("extra requires ObjArray")
    if not extras.value:
        return []
    if len(extras.value) != 1 or not isinstance(extras.value[0], c.String):
        raise ValueError("only one confirmed send_touch batch supported")
    text = extras.value[0].value
    match = re.fullmatch(r"send_touch:([0-9]+(?:,[0-9]+)*)-([0-9]+)-([0-9]+)-([01])", text)
    if not match:
        raise ValueError("unsupported extra; no changes applied")
    counts = [int(x) for x in match[1].split(",")]
    bonus, baseline, started = map(int, match.groups()[1:])
    rewards = definition.rule.touchRewards.value
    # HomeScene.as:1980-2009: only index 0 can carry bonus. The local
    # profile has empty bonusRange and no generated random TouchEventParams.
    if len(counts) > len(rewards) or not counts[0] or any(counts[1:]) or bonus or not started:
        raise ValueError("only ordinary index-0 touches without bonus/events supported")
    if player.touchInfo.bonusRange.value or player.touchInfo.params.value:
        raise ValueError("random/event touch state not implemented")
    if baseline > 2147483647 or counts[0] > 2147483647:
        raise ValueError("touch values exceed signed integer range")
    receipt = db.execute("SELECT request FROM touch_receipts WHERE uid=? AND baseline=?", (player.uid, baseline)).fetchone()
    if receipt:
        if receipt[0] != text:
            raise ValueError("touch baseline already used for a different batch")
        LOG.info("touch_replay uid=%s baseline=%s", player.uid, baseline)
    else:
        if baseline != player.sendTouchCount:
            raise ValueError("stale/future touch baseline; re-login to synchronize")
        reward = counts[0] * rewards[0] * player.rank
        if reward < 0 or player.freeMoney + player.chargeMoney + reward > MONEY_MAX or baseline + counts[0] > 2147483647:
            raise ValueError("touch settlement would overflow")
        player.freeMoney += reward
        # Local monotonic cursor policy. Original server cursor advancement is
        # UNKNOWN; source confirms the client consumes this returned integer.
        player.sendTouchCount += counts[0]
        db.execute("INSERT INTO touch_receipts VALUES (?, ?, ?, ?, ?)", (player.uid, baseline, text, reward, int(time.time())))
        db.execute("UPDATE player_state SET revision=revision+1 WHERE uid=?", (player.uid,))
        LOG.info("touch_prepared uid=%s count=%s reward=%s balance=%s cursor=%s", player.uid, counts[0], reward, player.freeMoney, player.sendTouchCount)
    # Absolute balance: client already optimistically added the touch reward.
    # Never send touch:+reward or it would be credited twice in the client UI.
    return [c.String(f"touch_u:{player.freeMoney}"), c.String(f"touch_count:{player.sendTouchCount}")]


def process(accounts, packet, session, definition, *, allow_local_actions=False):
    if not session.initialized:
        raise ValueError("initialize player before gameplay")
    if packet.type in LOCAL_COLLECTION_TYPES and not allow_local_actions:
        raise ValueError("collection action requires isolated local_compatible mode")
    if not null(packet.payloadObj0) or not null(packet.payloadObj1):
        raise ValueError("unexpected object payload")
    if packet.type == 149 and not allow_local_actions:raise ValueError('AR scene entry requires local compatible mode')
    if packet.type in (59, 60, 62, 66, 114, 141, 142, 145, 149, 159, 190) and not null(packet.payloadInt):
        raise ValueError("state/extra request has no integer payload")

    def operation(player, db):
        extra = settle_touch(player, db, packet.payloadExtra, definition)
        if packet.type in (60,145,201326757):
            from .profile import sync_unlock
            if sync_unlock(player,db,definition):extra.append(c.ObjArray([c.String('feature:'),player.features]))
        if packet.type in (60, 62, 141, 142, 145, 149):
            if packet.type == 142 and allow_local_actions:
                features = {x.value if isinstance(x,c.Int) else x for x in player.features.value}
                if not player.utensilMap.get(1) or not player.utensilMap[1].acquired or 0 not in features:
                    raise ValueError('buy picturebook and finish shop guide before collection entry')
            if packet.type == 149 and (not player.utensilMap.get(2) or not player.utensilMap[2].acquired):
                raise ValueError('buy AR camera before entering AR scene')
            # 142: HomeScene.as:2674-2681 -> sendChangeState -> CollectionScene.
            # Collection reads existing UserData.gudetamaMap locally; entering
            # never creates collectible records or grants rewards.
            db.execute("UPDATE player_state SET scene=?, revision=revision+1 WHERE uid=?", (packet.type, player.uid))
            result = c.ObjArray([])  # Real scene state persisted, callback consumes Array.
        elif packet.type == CUP_RECIPE_LIST:
            kid, = integers(packet.payloadInt,1)
            kitchen = definition.kitchenwareMap.get(kid)
            owned = player.kitchenwareMap.get(kitchen.type) if kitchen else None
            param = owned.paramMap.get(kid) if owned else None
            if not param or not param.available:
                raise ValueError('unknown or unavailable kitchenware')
            # CookingScene.as:1739-1756 consumes [recipeID -> ItemParam[]],
            # or [null] for its native "no obtainable cups" dialog. Cooking
            # currently grants no bonus cups (local rules extra_rewards=false).
            # GameDef has cup prizes, but no recipe -> cup drop assignment;
            # do not advertise shop products as obtainable cooking drops.
            result = c.ObjArray([c.Null()])
        elif packet.type == 190:
            result = c.ObjArray([])  # Business outcome is in confirmed extra responses.
        elif packet.type in (59, 114):
            result = c.Null()  # Existing source-confirmed ping / no billing key.
        elif packet.type in (66, 159):
            result = c.ObjArray([])  # No local system mails / cleared mission rewards.
        elif packet.type == 249:
            kind = integers(packet.payloadInt, 1)[0]
            if kind not in (0, 1, 2, 3):
                raise ValueError("event kitchenware availability rules UNKNOWN")
            owned = player.kitchenwareMap.get(kind)
            grades = {}
            if owned is not None:
                if owned.recipeNoteId:
                    raise ValueError("cooking timer/result lifecycle not implemented")
                for kitchen_id, param in owned.paramMap.items():
                    kdef = definition.kitchenwareMap.get(kitchen_id)
                    if kdef is None or kdef.type != kind or not null(kdef.eventIds):
                        raise ValueError("kitchenware configuration/event rules unresolved")
                    if param.available:
                        # CookingScene.as:2441 shows a grade only for status 0.
                        # Other status codes are UNKNOWN and are never invented.
                        grades[kdef.grade] = c.Int(0)
            result = c.IntHashMap(grades)
        elif packet.type == 201326757:
            flags = integers(packet.payloadInt, 2)
            if any(x not in (0, 1) for x in flags):
                raise ValueError("invalid profile refresh flags")
            # This local account has no presents or social relationships. These
            # systems cannot mutate through any supported route.
            result = c.ObjArray([c.ObjArray([]), c.ObjArray([]), c.ObjArray([])])
        elif packet.type == 150995129:
            if allow_local_actions and (not player.utensilMap.get(5) or not player.utensilMap[5].acquired):
                raise ValueError('buy refrigerator before collection placement')
            selected = integers(packet.payloadInt, 1)[0]
            owned = player.gudetamaMap.get(selected)
            if selected not in definition.gudetamaMap or owned is None or not owned.available or owned.count <= 0:
                raise ValueError("cannot place an unavailable/unowned character")
            player.placedGudetamaId = selected
            if allow_local_actions:
                from .local_voices import helper_extra
                extra.append(helper_extra(player,definition))
            db.execute("UPDATE player_state SET revision=revision+1 WHERE uid=?", (player.uid,))
            result = c.ObjArray([])  # GudetamaDetailDialog.as:572-579 ignores contents.
        elif packet.type == 166:
            # GudetamaDetailDialog.as:128-168 / ProfileScene.as:317-338:
            # [slot, character ID], returning the complete UserWantedData Array.
            slot, selected = integers(packet.payloadInt, 2)
            wanted = player.wantedGudetamas
            if not isinstance(wanted, c.ObjArray) or len(wanted.value) != 3 or any(
                not isinstance(item, c.UserWantedData) for item in wanted.value
            ):
                raise ValueError("unknown wanted-list state; no automatic repair")
            if slot not in (0, 1, 2) or (selected != 0 and selected not in definition.gudetamaMap):
                raise ValueError("invalid wanted slot or unknown character")
            # Local policy: one slot per ID; an unowned character can be wanted.
            if selected and any(item.id == selected for i, item in enumerate(wanted.value) if i != slot):
                raise ValueError("character already in another wanted slot")
            item = wanted.value[slot]
            if item.id != selected:
                # Official updateTime semantics UNKNOWN. Local policy uses the
                # same offset-seconds clock as main; clearing resets it to zero.
                updated = int(time.time()) - 1262271600 if selected else 0
                if not 0 <= updated <= 2147483647:
                    raise ValueError("wanted timestamp outside protocol range")
                item.id, item.updateTime = selected, updated
                db.execute("UPDATE player_state SET revision=revision+1 WHERE uid=?", (player.uid,))
            result = wanted
        elif packet.type == 218:
            # SnsShareDialog.as:141-230 explicitly supports a null bonus.
            # Null opens the original preview without creating a reward claim.
            # GudetamaShareDialog.as:266-269 passes the selected Gudetama ID
            # as argi, not always zero. PacketUtil.as:34-49 wraps it in [ID].
            selected = 0 if null(packet.payloadInt) else integers(packet.payloadInt, 1)[0]
            if selected != 0 and selected not in definition.gudetamaMap:
                raise ValueError("unknown share character")
            LOG.info("local_share_preview uid=%s character=%s bonus=none", player.uid, selected)
            result = c.Null()
        else:
            raise ValueError("unsupported gameplay packet")
        from . import tutorial
        extra.extend(tutorial.rearm_voice_exercise(player,db,packet))
        if allow_local_actions:
            from . import guides
            extra.extend(guides.extras(player,db,definition))
        if packet.type == 60:
            from . import events
            extra.append(events.extra(db,definition))
        if allow_local_actions and packet.type in (60,190):
            from . import home_events,home_rewards
            extra.extend(home_events.issue(player,db,definition,refresh=packet.type==190))
            extra.extend(home_rewards.sync(player,db,definition))
        encode(result)
        encode(c.ObjArray(extra))
        return result, c.ObjArray(extra) if extra else None

    result = accounts.transact(session.uiid, operation)
    LOG.info("gameplay_committed type=%s", packet.type)
    if packet.type == 249:
        LOG.info("kitchen_query type=%s grades=%s", packet.payloadInt.value[0], sorted(result[0].value))
    return result
