"""Kitchen read models and absolute-clock projection, not cooking outcomes.

No request creates a clock or charges/awards anything. Imported clocks are
explicit test fixtures until original start/settlement rules are recovered.
"""
import time
import argparse
import json
import sqlite3
from pathlib import Path


def project_clocks(player, db, now=None):
    now = int(time.time()) if now is None else int(now)
    rows = {r[0]: r[1:] for r in db.execute(
        "SELECT kitchen_type,recipe_id,gudetama_id,deadline_unix FROM kitchen_clocks WHERE uid=?", (player.uid,))}
    for kind, kitchen in player.kitchenwareMap.items():
        row = rows.get(kind)
        if kitchen.recipeNoteId <= 0:
            if row is not None:
                raise ValueError("idle kitchen has unexpected clock; refusing inconsistent state")
            continue
        if row is None or row[:2] != (kitchen.recipeNoteId, kitchen.gudetamaId):
            raise ValueError("active kitchen requires a matching absolute clock; no guessed deadline")
        remaining = row[2] - now
        if not -2147483648 <= remaining <= 2147483647:
            raise ValueError("kitchen remaining time exceeds wire integer range")
        kitchen.restTimeSecs = remaining  # Preserve negatives for overcook UI.
    if rows.keys() - player.kitchenwareMap.keys():
        raise ValueError("clock refers to absent kitchen")
    return player


def describe(player, definition):
    """Source-backed ownership/visibility report, never authorization to start."""
    result = []
    for kind, kitchen in sorted(player.kitchenwareMap.items()):
        recipes = []
        params = []
        for ident, param in sorted(kitchen.paramMap.items()):
            kd = definition.kitchenwareMap.get(ident)
            if kd is None or kd.type != kind or param.id != ident:
                raise ValueError("kitchen parameter/configuration mismatch")
            params.append({"id": ident, "grade": kd.grade, "available": param.available})
            for rid in kd.recipeNoteIds.value:
                rd = definition.recipeNoteMap[rid]
                owned = player.recipeNoteMap.get(rid)
                candidates = []
                for gid in rd.defaults.value + rd.appends.value:
                    gd = definition.gudetamaMap[gid]
                    data = player.gudetamaMap.get(gid)
                    candidates.append({"id": gid, "cost_display": gd.cost, "reward_display": gd.reward,
                                       "available": bool(data and data.available), "unlocked": bool(data and data.unlocked)})
                recipes.append({"id": rid, "configured_minutes": rd.minutes, "event_id": rd.eventId,
                                "visible": bool(owned and owned.visible), "available": bool(owned and owned.available),
                                "purchased": bool(owned and owned.purchased), "candidates": candidates})
        result.append({"type": kind, "params": params, "recipes": recipes,
                       "recipe_id": kitchen.recipeNoteId, "gudetama_id": kitchen.gudetamaId,
                       "remaining_seconds": kitchen.restTimeSecs,
                       "client_state": "idle" if kitchen.recipeNoteId <= 0 else ("complete" if kitchen.restTimeSecs < 0 else "cooking"),
                       "start_enabled": False, "reason": "original start/settlement rules UNKNOWN"})
    return result


def inspect(path, uid):
    from .configuration import Configuration
    from .protocol import decode
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        row = db.execute("SELECT player FROM accounts WHERE uid=?", (uid,)).fetchone()
        if row is None or row[0] is None:
            raise ValueError("initialized account required")
        player = decode(row[0])
        now = int(time.time())
        project_clocks(player, db, now)
        clocks = [{"type": k, "deadline_unix": d, "source": source} for k,d,source in db.execute("SELECT kitchen_type,deadline_unix,source FROM kitchen_clocks WHERE uid=?", (uid,))]
        cfg = Configuration("http://127.0.0.1:8080/gde/static/").definitions[player.locale]
        return {"uid": uid, "observed_unix": now, "freeMoney": player.freeMoney, "placedGudetamaId": player.placedGudetamaId, "clocks": clocks, "kitchens": describe(player, cfg)}
    finally:
        db.close()


if __name__ == "__main__":
    from .library import ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--uid", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(inspect(args.state, args.uid), ensure_ascii=False, indent=2))
