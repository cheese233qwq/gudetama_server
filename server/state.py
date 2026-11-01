import hashlib
import secrets
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field
from .protocol import decode, encode


class Accounts:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('PRAGMA busy_timeout=10000')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute("CREATE TABLE IF NOT EXISTS accounts (uid INTEGER PRIMARY KEY AUTOINCREMENT, uiid TEXT UNIQUE NOT NULL, player BLOB)")
        self.db.execute("CREATE TABLE IF NOT EXISTS player_state (uid INTEGER PRIMARY KEY REFERENCES accounts(uid), scene INTEGER NOT NULL DEFAULT 60, revision INTEGER NOT NULL DEFAULT 0)")
        self.db.execute("CREATE TABLE IF NOT EXISTS touch_receipts (uid INTEGER NOT NULL REFERENCES accounts(uid), baseline INTEGER NOT NULL, request TEXT NOT NULL, reward INTEGER NOT NULL, created_unix INTEGER NOT NULL, PRIMARY KEY(uid, baseline))")
        self.db.execute("CREATE TABLE IF NOT EXISTS player_migrations (uid INTEGER NOT NULL REFERENCES accounts(uid), name TEXT NOT NULL, before_player BLOB NOT NULL, created_unix INTEGER NOT NULL, PRIMARY KEY(uid,name))")
        self.db.execute("CREATE TABLE IF NOT EXISTS kitchen_clocks (uid INTEGER NOT NULL REFERENCES accounts(uid), kitchen_type INTEGER NOT NULL, recipe_id INTEGER NOT NULL, gudetama_id INTEGER NOT NULL, deadline_unix INTEGER NOT NULL, source TEXT NOT NULL CHECK(source='fixture'), PRIMARY KEY(uid,kitchen_type))")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.commit()

    def new_uiid(self):
        value = str(uuid.uuid4())  # Local policy; client only requires a 36-char string.
        with self.lock:
            self.db.execute("INSERT INTO accounts (uiid) VALUES (?)", (value,))
            self.db.commit()
        return value

    def register_uiid(self, value):
        """Register a cached client identifier on this save, without replacing players."""
        # Our UIID endpoint issues canonical UUID strings. Reject malformed input
        # before writing, and let the unique constraint serialize repeat logins.
        if not isinstance(value,str) or len(value)!=36:
            raise ValueError('invalid client UIID')
        try:parsed=uuid.UUID(value)
        except ValueError:raise ValueError('invalid client UIID') from None
        if str(parsed)!=value.lower() or parsed.int==0:
            raise ValueError('invalid client UIID')
        with self.lock:
            try:
                created=self.db.execute('INSERT OR IGNORE INTO accounts(uiid) VALUES(?)',(value,)).rowcount==1
                self.db.commit()
            except BaseException:
                self.db.rollback()
                raise
        return created

    def player(self, uiid, factory):
        with self.lock:
            row = self.db.execute("SELECT uid, player FROM accounts WHERE uiid=?", (uiid,)).fetchone()
            if row is None:
                raise ValueError("unknown local UIID; request /gde/uiid first")
            if row[1] is not None:
                return decode(row[1])
            player = factory(row[0])
            self.db.execute("UPDATE accounts SET player=? WHERE uid=?", (encode(player), row[0]))
            self.db.commit()
            return player

    def has(self, uiid):
        with self.lock:
            return self.db.execute("SELECT 1 FROM accounts WHERE uiid=?", (uiid,)).fetchone() is not None

    def save(self, uiid, player):
        with self.lock:
            self.db.execute("UPDATE accounts SET player=? WHERE uiid=?", (encode(player), uiid))
            self.db.commit()

    def transact(self, uiid, operation):
        """Player, metadata and reward receipt commit together or all roll back."""
        with self.lock:
            try:
                self.db.execute("BEGIN IMMEDIATE")
                row = self.db.execute("SELECT uid, player FROM accounts WHERE uiid=?", (uiid,)).fetchone()
                if row is None or row[1] is None:
                    raise ValueError("player not initialized")
                player = decode(row[1])
                self.db.execute("INSERT OR IGNORE INTO player_state(uid) VALUES (?)", (row[0],))
                result = operation(player, self.db)
                self.db.execute("UPDATE accounts SET player=? WHERE uid=?", (encode(player), row[0]))
                self.db.commit()
                return result
            except BaseException:
                self.db.rollback()
                raise

    def close(self):
        self.db.close()


@dataclass
class Session:
    uiid: str
    locale: str
    key: bytes = field(default_factory=lambda: secrets.token_bytes(16))
    expires: float = field(default_factory=lambda: time.monotonic() + 3600)
    last_fingerprint: bytes | None = None
    last_sequence: int | None = None
    last_response: bytes | None = None
    initialized: bool = False
    entered_home: bool = False
    cooking_run_id: str | None = None
    lock: threading.RLock = field(default_factory=threading.RLock)
    platform: str = '1'


class Sessions:
    def __init__(self):
        self.items = {}
        self.lock = threading.Lock()

    def create(self, uiid, locale, platform='1'):
        if platform not in ('0','1'): raise ValueError('unsupported session platform')
        session = Session(uiid, locale, platform=platform)
        sid = secrets.token_hex(16)
        with self.lock:
            self.items = {key: value for key, value in self.items.items() if value.expires > time.monotonic()}
            self.items[sid] = session
        return sid, session

    def get(self, sid):
        with self.lock:
            session = self.items.get(sid)
            if session is None or session.expires <= time.monotonic():
                raise KeyError("invalid/expired session")
            return session


def fingerprint(form):
    return hashlib.sha256(form["e"].encode("ascii")).digest()


def request_token(session, digest):
    """Durable purchase boundary; separate fresh requests from exact replays."""
    if not isinstance(digest,bytes) or len(digest)!=32:
        raise ValueError('missing purchase request fingerprint')
    return 'request:'+hashlib.sha256(session.key+digest).hexdigest()
