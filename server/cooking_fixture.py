"""Explicit temporary kitchen fixture. Source DB is opened read-only."""
import argparse
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from .configuration import Configuration
from .library import ROOT, c
from .player import blank
from .protocol import decode, encode
from .state import Accounts
from .cooking import describe


def snapshot(path):
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return {"players": [{"uid": uid, "player_sha256": hashlib.sha256(blob or b"").hexdigest()} for uid, blob in db.execute("SELECT uid,player FROM accounts ORDER BY uid")],
                "touch_receipts": list(db.execute("SELECT uid,baseline,reward,created_unix FROM touch_receipts ORDER BY uid,baseline"))}
    finally:
        db.close()


def create(source, destination, uid, definition, active_seconds=None):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or destination.exists() or not destination.is_relative_to(ROOT / "server/state"):
        raise ValueError("fixture requires new destination under server/state; never overwrite")
    if active_seconds is not None and not -172801 <= active_seconds <= 3600:
        raise ValueError("fixture remaining time outside explicitly supported research range")
    before = snapshot(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    target = sqlite3.connect(destination)
    try:
        db.backup(target)
    finally:
        db.close()
        target.close()
    accounts = Accounts(destination)
    try:
        row = accounts.db.execute("SELECT uiid FROM accounts WHERE uid=? AND player IS NOT NULL", (uid,)).fetchone()
        if row is None:
            raise ValueError("initialized fixture source account required")
        def operation(player, db):
            if player.kitchenwareMap or player.recipeNoteMap:
                raise ValueError("fixture only adds to an explicitly empty kitchen; review existing states")
            kd, rd = definition.kitchenwareMap[1], definition.recipeNoteMap[1]
            if (kd.type, kd.grade, rd.kitchenwareId) != (0, 0, 1):
                raise ValueError("fixture configuration mismatch")
            player.kitchenwareMap[0] = blank(c.KitchenwareData, type=0, paramMap={1: c.KitchenwareParam(id=1, available=True)}, assistUsefulIds=c.IntArray([]), assistEncodedUids=c.IntArray([]))
            player.recipeNoteMap[1] = c.RecipeNoteData(id=1, visible=True, available=True, purchased=True, targetValue=0, currentValue=0)
            for gid in rd.defaults.value:
                if gid in player.gudetamaMap:
                    raise ValueError("fixture would overwrite owned character")
                player.gudetamaMap[gid] = blank(c.GudetamaData, id=gid, available=True, unlocked=True, count=1 if gid == 6 else 0, num=1 if gid == 6 else 0)
            if active_seconds is not None:
                kitchen = player.kitchenwareMap[0]
                kitchen.recipeNoteId, kitchen.gudetamaId, kitchen.restTimeSecs = 1, 6, active_seconds
                db.execute("INSERT INTO kitchen_clocks VALUES (?,0,1,6,?,'fixture')", (player.uid, int(time.time()) + active_seconds))
            return {"freeMoney": player.freeMoney, "sendTouchCount": player.sendTouchCount, "kitchens": describe(player, definition)}
        result = accounts.transact(row[0], operation)
    finally:
        accounts.close()
    after = snapshot(source)
    if before != after:
        raise RuntimeError("source changed during fixture creation")
    return {"fixture_only": True, "source": str(source), "destination": str(destination), "uid": uid,
            "source_snapshot": before, "source_unchanged": before == after,
            "changes": {"kitchenware_id": 1, "recipe_note_id": 1, "gudetama_ids_unlocked": [6, 7, 8], "gudetama_id_with_count_one": 6, "currency_granted": 0, "active_seconds_fixture": active_seconds, "duration_is_original": False}, "result": result}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "server/state/accounts.sqlite3")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--uid", type=int, default=1)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--active-seconds", type=int, help="explicit synthetic timer, never original cooking duration")
    args = parser.parse_args()
    args.manifest = args.manifest.resolve()
    if args.manifest.exists() or not args.manifest.is_relative_to(ROOT / "docs/evidence"):
        parser.error("manifest requires a new file under docs/evidence; never overwrite archives")
    result = create(args.source, args.output, args.uid, Configuration("http://127.0.0.1:8080/gde/static/").definitions["ja"], args.active_seconds)
    args.manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"fixture_only": True, "source_unchanged": result["source_unchanged"], "destination": result["destination"], "freeMoney": result["result"]["freeMoney"]}))


if __name__ == "__main__":
    main()
