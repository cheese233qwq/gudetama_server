"""Additive SQLite indexes; retain player blobs and all durable receipts."""

INDEXES = {
    'cooking_runs': (
        "CREATE INDEX IF NOT EXISTS cooking_claimed_by_uid ON cooking_runs(uid) WHERE status='claimed'",
    ),
    'local_cup_runs': (
        'CREATE INDEX IF NOT EXISTS cup_active_by_uid ON local_cup_runs(uid) WHERE claimed_unix IS NULL',
    ),
    'normal_mission_presents': (
        'CREATE INDEX IF NOT EXISTS mission_unclaimed_by_uid ON normal_mission_presents(uid,mail_key) WHERE claimed_unix IS NULL',
    ),
}


def optimize_indexes(db):
    """Idempotent startup migration; no deletions, VACUUM or reward rewrites."""
    with db:
        tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table,statements in INDEXES.items():
            if table in tables:
                for statement in statements:db.execute(statement)
