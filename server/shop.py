"""Non-official catalogue policy; atomic GP/free-gold purchases and unlocks."""
import logging
import time
import uuid
import re
from .library import c
from .protocol import encode
from .state import request_token
from . import gameplay

LOG = logging.getLogger('gudetama.local')
PURCHASE = 50331664
CHANGE = 16777460
OPEN = 62
PICTUREBOOK_MONEY = 50331859
TYPES = {PURCHASE, CHANGE, OPEN, PICTUREBOOK_MONEY}
GROUPS = {8:('usefulMap',c.UsefulData),9:('decorationMap',c.DecorationData),
          10:('utensilMap',c.UtensilData),11:('stampMap',c.StampData),12:('avatarMap',c.AvatarData)}
PREREQUISITES = {5:3,6:5,7:6,8:7}
FEATURES = {1:0,2:1,3:2,4:3,5:4,6:5,7:6,8:7}
OFFSET_SECS = 1262271600


def item_available(player,kind,ident,item):
    # GameDef conditionDesc: room variants require level 12; utensil chain
    # and level-50 oven are checked against ownership/rank on every purchase.
    if kind == 10:return utensil_available(player,ident)
    condition = getattr(item,'conditionDesc','')
    if not condition:return True
    level = re.fullmatch(r'レベルが(\d+)になると買えるようになるよ！',condition)
    if level:return player.rank >= int(level[1])
    if kind == 8 and ident == 80:return True  # Daily/stock limits below.
    return False  # Unknown conditions never become unconditional eligibility.


def picturebook_money(accounts,packet,session,definition):
    # PurchaseShopDialog.as:381-387: callback consumes an Int GP delta.
    # Local rule: one 100-GP tutorial allowance, not recovered server amount.
    if not session.initialized or any(not gameplay.null(x) for x in (packet.payloadInt,packet.payloadObj0,packet.payloadObj1)):
        raise ValueError('invalid picturebook allowance request')
    def operation(player,db):
        from . import tutorial
        if not tutorial.enabled(db) or player.noticeFlagData.tutorialProgress < 7 or player.noticeFlagData.noticeFlags.value[2]&15 != 1:
            raise ValueError('picturebook allowance requires active shop guide')
        extra = gameplay.settle_touch(player,db,packet.payloadExtra,definition)
        if not db.execute('SELECT 1 FROM shop_visits WHERE uid=?',(player.uid,)).fetchone():
            raise ValueError('enter shop before tutorial allowance')
        token = 'shop-picturebook-allowance-v1'
        exists = db.execute('SELECT 1 FROM player_migrations WHERE uid=? AND name=?',(player.uid,token)).fetchone()
        amount = 0
        if not exists and not (player.utensilMap.get(1) and player.utensilMap[1].acquired):
            amount = definition.utensilMap[1].price.num
            if player.freeMoney+amount > gameplay.MONEY_MAX:raise ValueError('GP overflow')
            db.execute('INSERT INTO player_migrations VALUES(?,?,?,?)',(player.uid,token,encode(player),int(time.time())))
            player.freeMoney += amount
            db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
        extra = [x for x in extra if not (isinstance(x,c.String) and x.value.startswith('touch_u:'))]
        extra.append(c.String(f'touch_u:{player.freeMoney}'))
        result,extras = c.Int(amount),c.ObjArray(extra)
        encode(result);encode(extras)
        return result,extras
    return accounts.transact(session.uiid,operation)


def utensil_available(player, ident):
    prerequisite = PREREQUISITES.get(ident)
    return (ident != 4 or player.rank >= 50) and (prerequisite is None or
        bool(player.utensilMap.get(prerequisite) and player.utensilMap[prerequisite].acquired))


def open_shop(accounts, packet, session, definition):
    if not session.initialized or not gameplay.null(packet.payloadInt) or not gameplay.null(packet.payloadObj0) or not gameplay.null(packet.payloadObj1):
        raise ValueError('invalid shop entry')
    def operation(player,db):
        if player.noticeFlagData.tutorialProgress < 7:raise ValueError('complete core tutorial before entering shop')
        extra = gameplay.settle_touch(player,db,packet.payloadExtra,definition)
        enable_catalogue(player,db,definition)
        extra.extend(catalogue_extras(player))
        from . import guides
        extra.extend(guides.extras(player,db,definition))
        # Entry remains a prerequisite; consumables use per-request receipts.
        db.execute('INSERT OR REPLACE INTO shop_visits VALUES(?,?)',(player.uid,str(uuid.uuid4())))
        db.execute('UPDATE player_state SET scene=62,revision=revision+1 WHERE uid=?',(player.uid,))
        return c.ObjArray([]),c.ObjArray(extra) if extra else None
    return accounts.transact(session.uiid,operation)


def change(accounts, packet, session, definition):
    if not session.initialized or packet.type != CHANGE:
        raise ValueError('initialize player before background change')
    if not gameplay.null(packet.payloadObj0) or not gameplay.null(packet.payloadObj1):
        raise ValueError('unexpected background object payload')
    ident = gameplay.integers(packet.payloadInt, 1)[0]
    def operation(player, db):
        extra = gameplay.settle_touch(player,db,packet.payloadExtra,definition)
        owned = player.decorationMap.get(ident)
        if (ident not in definition.decorationMap or not isinstance(owned,c.DecorationData)
                or owned.id != ident or not owned.acquired or not owned.available):
            raise ValueError('background must be owned and available')
        if player.decorationId != ident:
            player.decorationId = ident
            db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
        # DecorationDetailDialog.as:171-200 treats Array as a warning; Null
        # follows the normal setDecorationId + HomeScene path.
        result = c.Null()
        extras = c.ObjArray(extra) if extra else None
        encode(result)
        if extras is not None:encode(extras)
        return result,extras
    answer = accounts.transact(session.uiid,operation)
    LOG.info('background_change_committed id=%s',ident)
    return answer


def prepare_database(accounts):
    # Called after the shared server's isolated database validation.
    accounts.db.execute('''CREATE TABLE IF NOT EXISTS shop_receipts(
        purchase_id TEXT PRIMARY KEY, uid INTEGER NOT NULL REFERENCES accounts(uid),
        kind INTEGER NOT NULL, item_id INTEGER NOT NULL, cost INTEGER NOT NULL,
        item_after BLOB NOT NULL, created_unix INTEGER NOT NULL,
        UNIQUE(uid,kind,item_id))''')
    accounts.db.commit()
    accounts.db.execute('CREATE TABLE IF NOT EXISTS shop_visits(uid INTEGER PRIMARY KEY REFERENCES accounts(uid),visit_id TEXT NOT NULL)')
    accounts.db.execute('''CREATE TABLE IF NOT EXISTS shop_stack_receipts(
        uid INTEGER NOT NULL REFERENCES accounts(uid),visit_id TEXT NOT NULL,
        kind INTEGER NOT NULL,item_id INTEGER NOT NULL,quantity INTEGER NOT NULL,
        cost INTEGER NOT NULL,created_unix INTEGER NOT NULL,
        PRIMARY KEY(uid,visit_id,kind,item_id))''')
    accounts.db.commit()


def process(accounts, packet, session, definition, *, request_fingerprint=None):
    if not session.initialized or packet.type != PURCHASE:
        raise ValueError('initialize player before purchase')
    if not gameplay.null(packet.payloadObj0) or not gameplay.null(packet.payloadObj1):
        raise ValueError('unexpected purchase object payload')
    ident, kind, quantity = gameplay.integers(packet.payloadInt, 3)
    if kind not in GROUPS or type(quantity) is not int or not 1 <= quantity <= 99:
        raise ValueError('unsupported item kind or purchase quantity')
    stack = kind in (8,11)
    if not stack and quantity != 1:raise ValueError('one-time item quantity must be one')

    def operation(player, db):
        extra = gameplay.settle_touch(player, db, packet.payloadExtra, definition)
        if player.noticeFlagData.tutorialProgress < 7:raise ValueError('complete core tutorial before shopping')
        from . import tutorial
        if tutorial.enabled(db) and player.noticeFlagData.noticeFlags.value[2]&15 != 2:
            if (kind,ident) != (10,1) or player.noticeFlagData.noticeFlags.value[2]&15 != 1:
                raise ValueError('buy picturebook during the shop guide first')
            if not db.execute('SELECT 1 FROM shop_visits WHERE uid=?',(player.uid,)).fetchone():
                raise ValueError('enter shop before picturebook purchase')
        name,cls = GROUPS[kind]
        item = getattr(definition,name).get(ident)
        owned = getattr(player,name).get(ident)
        if (item is None or not isinstance(item.price, c.ItemParam) or item.price.kind not in (0,1)
                or item.price.num <= 0 or not isinstance(owned, cls)
                or owned.id != ident or not owned.available
                or getattr(item,'eventId',0) or getattr(item,'event',False) or getattr(item,'privately',False)
                or not item_available(player,kind,ident,item)):
            raise ValueError('item unavailable or price unsupported')
        visit = None
        if stack:
            row = db.execute('SELECT visit_id FROM shop_visits WHERE uid=?',(player.uid,)).fetchone()
            if not row:raise ValueError('enter shop before purchasing consumables')
            visit = request_token(session,request_fingerprint)
            receipt = db.execute('SELECT quantity FROM shop_stack_receipts WHERE uid=? AND visit_id=? AND kind=? AND item_id=?',
                                 (player.uid,visit,kind,ident)).fetchone()
            if receipt and receipt[0] != quantity:raise ValueError('purchase receipt quantity mismatch')
        else:
            receipt = db.execute('SELECT purchase_id FROM shop_receipts WHERE uid=? AND kind=? AND item_id=?',
                                 (player.uid,kind,ident)).fetchone()
        if receipt:
            if not stack and not owned.acquired:
                raise ValueError('purchase receipt and inventory disagree')
            cost = 0  # Real previously committed ownership, never a second debit.
        else:
            if not stack and owned.acquired:raise ValueError('item already owned outside purchase ledger')
            cost = item.price.num*quantity
            field = 'freeMoney' if item.price.kind == 0 else 'freeMetal'
            if cost > gameplay.MONEY_MAX or getattr(player,field) < cost:raise ValueError('insufficient free currency')
            if stack:
                limit = item.possessionLimit if kind == 8 else 99999
                if limit <= 0 or owned.num+quantity > limit:raise ValueError('inventory limit exceeded')
                if kind == 8:
                    now = int(time.time())
                    reset_hour = item.purchaseResetHourOffset
                    if reset_hour not in (-1,255):
                        if not 0 <= reset_hour <= 23:raise ValueError('unknown daily reset hour')
                        if owned.nextAvailablePurchaseSec > now-OFFSET_SECS:raise ValueError('daily purchase limit reached')
                        if quantity != 1:raise ValueError('daily limited item quantity must be one')
                        # Local boundary: persisted player time zone. Unix
                        # deadline is encoded using the client's offset epoch.
                        zone = player.timeZoneOffset//1000
                        owned.nextAvailablePurchaseSec = ((now+zone-reset_hour*3600)//86400+1)*86400-zone+reset_hour*3600-OFFSET_SECS
                owned.num += quantity
                db.execute('INSERT INTO shop_stack_receipts VALUES(?,?,?,?,?,?,?)',
                           (player.uid,visit,kind,ident,quantity,cost,int(time.time())))
            else:
                owned.acquired = True
                db.execute('INSERT INTO shop_receipts VALUES(?,?,?,?,?,?,?)',
                           (str(uuid.uuid4()),player.uid,kind,ident,cost,encode(owned),int(time.time())))
            setattr(player,field,getattr(player,field)-cost)
            db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(player.uid,))
        # DecorationPurchaseDialog.as purchase callback consumes [ItemParam,
        # DecorationData]: addItem replaces the absolute record; useItem debits.
        # Absolute GP extra runs afterward, also correcting repeat callbacks.
        enable_catalogue(player,db,definition)
        from . import guides
        extra.extend(guides.extras(player,db,definition))
        # Stackable callbacks ADD an ItemParam, unlike owned-object replacement.
        # A zero delta plus typed absolute inventory extra makes replay safe.
        result = c.ObjArray([c.ItemParam(kind=item.price.kind,id=0,num=cost),
                             c.ItemParam(kind=kind,id=ident,num=0) if stack else owned])
        extra.extend(catalogue_extras(player))
        from .local_voices import helper_extra
        extra.append(helper_extra(player,definition))
        extra = [x for x in extra if not (isinstance(x,c.String) and x.value.startswith('touch_u:'))]
        extra.append(c.String(f'touch_u:{player.freeMoney}'))
        extras = c.ObjArray(extra)
        encode(result)
        encode(extras)
        return result, extras

    result = accounts.transact(session.uiid, operation)
    LOG.info('shop_purchase_committed kind=%s item=%s charged=%s',kind,ident,result[0].value[0].num)
    return result


def catalogue_extras(player):
    result = [c.ObjArray([c.String('feature:'),player.features])]
    for name,cls,updates,removes,prefix in (
        ('utensilMap',c.UtensilInfo,'updateUtensils','removeUtensilIds','utensil:'),
        ('usefulMap',c.UsefulInfo,'updateUsefuls','removeUsefulIds','useful:'),
        ('decorationMap',c.DecorationInfo,'updateDecorations','removeDecorationIds','decoration:'),
        ('avatarMap',c.AvatarInfo,'updateAvatars','removeAvatarIds','avatar:'),
        ('stampMap',c.StampInfo,'updateStamps','removeStampIds','stamp:')):
        result.append(c.ObjArray([c.String(prefix),cls(**{updates:c.ObjArray(list(getattr(player,name).values())),removes:c.IntArray([])})]))
    return result


def enable_catalogue(player, db, definition):
    from .profile import sync_unlock
    sync_unlock(player,db,definition)
    # ItemShopDialog_Gudetama.as:1266,1314,1395,1451,1544 reads
    # UserData availability, not GameDef prices. PurchaseShopDialog.as:193-199
    # selects description (274) vs lock condition (337) on that same flag.
    # Local browsing policy for non-event GP/free-gold goods. Known conditions
    # are shared with purchase validation; unknown nonempty conditions lock.
    from . import tutorial
    groups = (('utensilMap', c.UtensilData), ('usefulMap', c.UsefulData),
              ('avatarMap', c.AvatarData), ('decorationMap', c.DecorationData),
              ('stampMap', c.StampData))
    if not isinstance(player.features,(c.IntArray,c.ObjArray)):
        raise ValueError('unknown feature representation')
    features = [x.value if isinstance(x,c.Int) else x for x in player.features.value]
    if any(type(x) is not int for x in features):
        raise ValueError('noninteger feature ID')
    # GudetamaUtil.as:731-734 + ShopScene_Gudetama.as:198: category 4
    # also requires feature 14 and the original screening flag 2.
    show_backgrounds = (14 not in features and 14 in definition.feature.paramMap
                        and len(definition.screening.flags.value) > 2 and definition.screening.flags.value[2] != 0)
    changes = []
    for name, cls in groups:
        owned = getattr(player, name)
        for ident, item in getattr(definition, name).items():
            price = item.price
            if (not isinstance(price, c.ItemParam) or price.kind not in (0,1) or price.num < 0
                    or getattr(item, 'eventId', 0) or getattr(item, 'event', False)
                    or getattr(item, 'privately', False)):
                continue
            data = owned.get(ident)
            if data is not None and (not isinstance(data, cls) or data.id != ident):
                raise ValueError('unknown shop item state; no automatic repair')
            available = item_available(player,{'utensilMap':10,'usefulMap':8,'avatarMap':12,'decorationMap':9,'stampMap':11}[name],ident,item)
            if data is None or data.available != available:
                changes.append((name, ident, cls, data, available))
    # Replace early compatibility placement grants with the purchase chain.
    desired = set(features)
    # Original useful-item list is client-side; local permission enables browsing.
    # Individual use requests remain rejected until their effects are implemented.
    if any(getattr(v,'available',False) for v in player.usefulMap.values()) or any(name == 'usefulMap' and available for name,_,_,_,available in changes):
        desired.add(9)
    for utensil,feature in FEATURES.items():
        data = player.utensilMap.get(utensil)
        ready = feature != 0 or not tutorial.enabled(db) or player.noticeFlagData.noticeFlags.value[2]&15 == 2
        if data and data.acquired and ready:desired.add(feature)
        else:desired.discard(feature)
    if not changes and not show_backgrounds and desired == set(features):
        return
    # Inside the login transaction; encode failure also prevents state writes.
    db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',
               (player.uid, 'local-compatible-gp-catalogue-availability-v1', encode(player), int(time.time())))
    db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',
               (player.uid, 'local-compatible-purchase-chain-v2', encode(player), int(time.time())))
    if show_backgrounds:
        db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',
                   (player.uid, 'local-compatible-background-shop-feature-14', encode(player), int(time.time())))
        desired.add(14)
    player.features = c.IntArray(sorted(desired))
    for name, ident, cls, data, available in changes:
        if data is None:
            if cls is c.UsefulData:
                data = cls(id=ident, num=0, available=available, nextAvailablePurchaseSec=-1)
            elif cls is c.StampData:
                data = cls(id=ident, num=0, available=available)
            else:
                data = cls(id=ident, acquired=False, available=available)
            getattr(player, name)[ident] = data
        else:
            data.available = available  # Preserve quantities, ownership and timers.
    db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?', (player.uid,))
    LOG.info('local_catalogue_prepared uid=%s available=%s', player.uid,
             [(name, ident) for name, ident, _, _, _ in changes])
