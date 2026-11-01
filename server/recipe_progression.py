"""Local progression based on archived Japanese condition text, not server code."""
import re
import time
from .library import c
from .player import blank
from .protocol import encode
from . import gameplay

PURCHASE = 134217926


def condition(recipe):
    if recipe.id == 1:return 'rank',1
    if recipe.targetType == 0 and recipe.targetId > 0:return 'character',recipe.targetId
    if recipe.targetType != -1:raise ValueError('recipe progression condition UNKNOWN')
    rank = re.search(r'レベルが(\d+)',recipe.conditionDesc)
    number = re.search(r'(\d+)種類',recipe.conditionDesc)
    if rank and gameplay.null(recipe.premises):return 'rank',int(rank[1])
    if number and isinstance(recipe.premises,c.IntArray) and recipe.premises.value:
        return 'crafted',int(number[1])
    if not recipe.conditionDesc.strip() and gameplay.null(recipe.premises):return 'kitchen',1
    raise ValueError('recipe progression condition UNKNOWN')


def ordinary_ids(d):
    return tuple(sorted(r.id for r in d.recipeNoteMap.values() if r.eventId == 0
                        and d.kitchenwareMap[r.kitchenwareId].type in (0,1,2,3)))


def refresh(p,db,d,policy):
    if p.noticeFlagData.tutorialProgress < 7:return []
    before = encode(p)
    changed_kitchens,changed_notes = [],[]
    from .restoration import policy as restoration_policy
    # Archive has no condition-map entry for base microwave4. This is an
    # explicit local fallback, not a recovered official unlock requirement.
    pot=p.kitchenwareMap.get(2)
    if (p.rank >= restoration_policy()['microwave_level'] and pot and 3 in pot.paramMap
            and pot.paramMap[3].available and 3 not in p.kitchenwareMap):
        k=blank(c.KitchenwareData,type=3,paramMap={4:c.KitchenwareParam(id=4,available=True)},assistUsefulIds=c.IntArray([]),assistEncodedUids=c.IntArray([]))
        p.kitchenwareMap[3]=k
        changed_kitchens.append(k)
    if p.rank >= 4 and 1 not in p.kitchenwareMap:
        kd = d.kitchenwareMap[2]
        if kd.type != 1 or kd.grade != 0:raise ValueError('base frying pan configuration mismatch')
        k = blank(c.KitchenwareData,type=1,paramMap={2:c.KitchenwareParam(id=2,available=True)},assistUsefulIds=c.IntArray([]),assistEncodedUids=c.IntArray([]))
        p.kitchenwareMap[1] = k
        changed_kitchens.append(k)
    for rid in ordinary_ids(d):
        rd = d.recipeNoteMap[rid]
        kd = d.kitchenwareMap[rd.kitchenwareId]
        k = p.kitchenwareMap.get(kd.type)
        if not k or rd.kitchenwareId not in k.paramMap:continue
        try:kind,goal = condition(policy.recipeNoteMap[rid])
        except ValueError:continue  # Unknown future conditions remain unavailable.
        if kind == 'character':
            value = int(db.execute("SELECT 1 FROM cooking_runs WHERE uid=? AND result_id=? AND status='claimed' LIMIT 1",(p.uid,goal)).fetchone() is not None)
            goal = 1
        elif kind == 'rank':value = p.rank
        elif kind == 'kitchen':value = 1
        else:
            value = len({row[0] for row in db.execute(
                "SELECT DISTINCT result_id FROM cooking_runs WHERE uid=? AND recipe_id IN ("+','.join('?' for _ in rd.premises.value)+") AND status='claimed' AND result_type=0",
                (p.uid,*rd.premises.value))})
        previous = p.recipeNoteMap.get(rid)
        # Local display policy: reveal a note only once its prerequisites are
        # met. Keep purchased notes visible, including legacy saved purchases.
        # Recompute visibility too so old visible=True placeholders are hidden.
        available = bool((previous and previous.purchased) or value>=goal)
        if previous is None:
            previous = c.RecipeNoteData(id=rid,visible=available,available=available,purchased=False,targetValue=goal,currentValue=value)
            p.recipeNoteMap[rid] = previous
            changed_notes.append(previous)
        elif (previous.visible,previous.available,previous.targetValue,previous.currentValue) != (available,available,goal,value):
            previous.visible,previous.available,previous.targetValue,previous.currentValue = available,available,goal,value
            changed_notes.append(previous)
        if previous.available and not previous.purchased and rd.price==0:
            # Local compatibility: PurchaseRecipeDialog always consumes price,
            # and UserDataWrapper.consumeMetal(0) throws. Free eligible notes
            # must reach the normal purchased UI without that callback.
            db.execute('CREATE TABLE IF NOT EXISTS recipe_purchase_receipts(uid INTEGER NOT NULL,recipe_id INTEGER NOT NULL,cost INTEGER NOT NULL,created_unix INTEGER NOT NULL,PRIMARY KEY(uid,recipe_id))')
            db.execute('INSERT INTO recipe_purchase_receipts VALUES(?,?,?,?)',(p.uid,rid,0,int(time.time())))
            previous.purchased=True
            if all(note.id!=rid for note in changed_notes):changed_notes.append(previous)
    if changed_notes or changed_kitchens:
        db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',(p.uid,'local-recipe-progression-v1',before,int(time.time())))
        db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))
    extra = []
    if changed_kitchens:extra.append(c.ObjArray([c.String('kitchenware:'),c.ObjArray(changed_kitchens)]))
    if changed_notes:extra.append(c.ObjArray([c.String('recipe_note:'),c.ObjArray(changed_notes)]))
    return extra


def purchase(accounts,packet,session,d,policy,engine):
    if not session.initialized or not gameplay.null(packet.payloadObj0) or not gameplay.null(packet.payloadObj1):raise ValueError('invalid recipe purchase request')
    rid = gameplay.integers(packet.payloadInt,1)[0]
    if rid not in ordinary_ids(d):raise ValueError('recipe unlock condition UNKNOWN')
    condition(policy.recipeNoteMap[rid])
    if d.recipeNoteMap[rid].price==0:
        # A stale client must not receive the success frame that calls consumeMetal(0).
        raise ValueError('free recipe unlocks automatically; re-login to synchronize recipes')
    def operation(p,db):
        extra = gameplay.settle_touch(p,db,packet.payloadExtra,d)
        extra.extend(refresh(p,db,d,policy))
        note,rd = p.recipeNoteMap.get(rid),d.recipeNoteMap[rid]
        if not note or not note.visible or not note.available or p.noticeFlagData.tutorialProgress<7:raise ValueError('recipe prerequisites not met')
        if note.purchased:raise ValueError('recipe already purchased; no additional deduction')
        if rd.price<0 or p.freeMetal<rd.price:raise ValueError('insufficient free gold eggs; cash payment excluded')
        db.execute('CREATE TABLE IF NOT EXISTS recipe_purchase_receipts(uid INTEGER NOT NULL,recipe_id INTEGER NOT NULL,cost INTEGER NOT NULL,created_unix INTEGER NOT NULL,PRIMARY KEY(uid,recipe_id))')
        db.execute('INSERT INTO recipe_purchase_receipts VALUES(?,?,?,?)',(p.uid,rid,rd.price,int(time.time())))
        p.freeMetal -= rd.price
        note.purchased = True
        engine.enable_candidates(p,db,d)
        from . import guides
        extra.extend(guides.extras(p,db,d))
        result = c.ObjArray([note,c.ObjArray([]),c.ObjArray([]),c.ObjArray(list(p.gudetamaMap.values()))])
        encode(result)
        extras = c.ObjArray(extra) if extra else None
        if extras is not None:encode(extras)
        return result,extras
    return accounts.transact(session.uiid,operation)
