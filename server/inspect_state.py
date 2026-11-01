"""Read-only state summary for local verification; no UIID/keys/credentials."""
import argparse
import json
import sqlite3
from pathlib import Path
from .library import ROOT
from .protocol import decode


def inspect(path):
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        players = []
        for uid, blob in db.execute("SELECT uid,player FROM accounts ORDER BY uid"):
            if blob is None:
                continue
            p = decode(blob)
            receipts = db.execute("SELECT baseline,reward,created_unix FROM touch_receipts WHERE uid=? ORDER BY baseline", (uid,)).fetchall()
            players.append({"uid": uid, "rank": p.rank, "freeMoney": p.freeMoney, "sendTouchCount": p.sendTouchCount,
                            "placedGudetamaId": p.placedGudetamaId, "decorationId": p.decorationId,
                            "kitchenwareTypes": list(p.kitchenwareMap), "receiptCount": len(receipts),
                            "receipts": [{"baseline": x[0], "reward": x[1], "created_unix": x[2]} for x in receipts]})
        return {"players": players}
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, default=ROOT / "server/state/accounts.sqlite3")
    args = parser.parse_args()
    print(json.dumps(inspect(args.state), indent=2, ensure_ascii=False))
