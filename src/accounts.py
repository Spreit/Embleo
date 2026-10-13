"""Persistent accounts using the client's existing bearer-token protocol.

The request owns a SQLite transaction. Existing JSON-shaped saves are retained
verbatim, but keyed by account rather than shared filesystem paths.
"""

import base64
import binascii
import hashlib
import json
import secrets
import sqlite3
import struct
import time
import zlib
from pathlib import Path


SCHEMA_VERSION = 3
INITIAL_SCHEMA = """
    CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY, player_code TEXT UNIQUE NOT NULL,
        created_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS tokens (
        hash TEXT PRIMARY KEY,
        account_id TEXT NOT NULL REFERENCES accounts(id)
    );
    CREATE TABLE IF NOT EXISTS saves (
        account_id TEXT NOT NULL REFERENCES accounts(id),
        name TEXT NOT NULL, value TEXT NOT NULL,
        PRIMARY KEY (account_id, name)
    );
    CREATE TABLE IF NOT EXISTS icons (
        account_id TEXT PRIMARY KEY REFERENCES accounts(id),
        revision TEXT NOT NULL, png BLOB NOT NULL
    );
"""

ACTIVITY_SCHEMA = """
    CREATE TABLE IF NOT EXISTS account_activity (
        account_id TEXT PRIMARY KEY REFERENCES accounts(id),
        last_action_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS login_history (
        id INTEGER PRIMARY KEY,
        account_id TEXT NOT NULL REFERENCES accounts(id),
        logged_in_at INTEGER NOT NULL,
        last_action_at INTEGER NOT NULL,
        logged_out_at INTEGER,
        source TEXT NOT NULL CHECK (source IN ('register', 'login'))
    );
    CREATE INDEX IF NOT EXISTS login_history_account
        ON login_history(account_id, id DESC);
"""

SOCIAL_SCHEMA = """
    CREATE TABLE IF NOT EXISTS follows (
        follower_id TEXT NOT NULL REFERENCES accounts(id),
        followed_id TEXT NOT NULL REFERENCES accounts(id),
        PRIMARY KEY (follower_id, followed_id),
        CHECK (follower_id != followed_id)
    );
    CREATE INDEX IF NOT EXISTS follows_target ON follows(followed_id, follower_id);
    CREATE TABLE IF NOT EXISTS blocks (
        blocker_id TEXT NOT NULL REFERENCES accounts(id),
        blocked_id TEXT NOT NULL REFERENCES accounts(id),
        PRIMARY KEY (blocker_id, blocked_id),
        CHECK (blocker_id != blocked_id)
    );
    CREATE INDEX IF NOT EXISTS blocks_target ON blocks(blocked_id, blocker_id);
"""


class AccountError(ValueError):
    pass


def default_saves():
    # Generate player state from master data, never clone the live shared save.
    from scripts.generate.generate_save_file import (
        ALL_EQUIPMENT, generateUserCharacter, generateUserEquipment,
        generateUserEpisode, generateUserItem,
    )
    return {
        "UserCharacter.json": generateUserCharacter(),
        "UserEquipment.json": generateUserEquipment(ALL_EQUIPMENT),
        "UserEpisode.json": generateUserEpisode(),
        "UserItems.json": generateUserItem(),
        "UserParameter.json": {
            "Gold": 10000, "Coin": 10000, "NobleCoin": 9, "MissionRank": 1,
            "MissionExp": 0, "FollowCount": 0, "FollowerCount": 0,
            "BlockCount": 0, "Flags": [], "MissionNextExp": 3,
            "Word": "Hello, hello, it's nice to meet you.",
            "FavoriteChrId": "pl001", "EmblemId": "emblem_sh001_001",
            "NobleStartAtUnix": 0, "NobleEndAtUnix": 0,
        },
        "HcBalance.json": {"PaidBalance": 3000, "FreeBalance": 3000,
                           "PaidBefore": 500, "FreeBefore": 500},
        "PieUserSetting.json": {"BirthYear": 0, "BirthMonth": 0,
            "HasBirthday": False, "HasStopper": False, "HasParentalpass": False,
            "Banned": False},
        "Presents.json": {"userPresents": [], "UserPresents": []},
        "PresentHistory.json": {"UserPresents": []},
        "checkpoint.txt": {},
    }


def save_key(path):
    """Only the old player paths are redirected; master data stays shared."""
    path = str(path).replace("\\", "/").removeprefix("./")
    if path == "checkpoint.txt":
        return path
    prefix = "data/user/"
    if path.startswith(prefix):
        name = path[len(prefix):]
        if "/" not in name and name.endswith(".json"):
            return name
    return None


def token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AccountStore:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, timeout=30)
        try:
            self.connection.execute("PRAGMA foreign_keys=ON")
            # Lock initialization so simultaneous server starts migrate only once.
            self.connection.execute("BEGIN IMMEDIATE")
            version = self.connection.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise RuntimeError("Account database schema is newer than this server supports.")
            if version == 0:
                # Version zero covers both fresh databases and the initial account
                # release. CREATE IF NOT EXISTS preserves its accounts and saves.
                for statement in INITIAL_SCHEMA.split(";"):
                    if statement.strip():
                        self.connection.execute(statement)
                self.connection.execute("PRAGMA user_version=1")
            if version < 2:
                for statement in ACTIVITY_SCHEMA.split(";"):
                    if statement.strip():
                        self.connection.execute(statement)
                self.connection.execute("PRAGMA user_version=2")
            if version < 3:
                for statement in SOCIAL_SCHEMA.split(";"):
                    if statement.strip():
                        self.connection.execute(statement)
                self.connection.execute("PRAGMA user_version=3")
            self.connection.commit()
            self.connection.execute("BEGIN IMMEDIATE")
        except Exception:
            self.connection.rollback()
            self.connection.close()
            raise

    def authenticate(self, token):
        row = self.connection.execute(
            "SELECT account_id FROM tokens WHERE hash=?", (token_hash(token),)
        ).fetchone()
        return row[0] if row else None

    def record_login(self, account_id, now, source="login"):
        self.connection.execute("""INSERT INTO login_history
            (account_id, logged_in_at, last_action_at, source)
            VALUES (?, ?, ?, ?)""", (account_id, now, now, source))

    def record_activity(self, account_id, now):
        self.connection.execute("""INSERT INTO account_activity VALUES (?, ?)
            ON CONFLICT(account_id) DO UPDATE SET
                last_action_at=MAX(last_action_at, excluded.last_action_at)""",
            (account_id, now))
        self.connection.execute("""UPDATE login_history
            SET last_action_at=MAX(last_action_at, ?)
            WHERE id=(SELECT id FROM login_history WHERE account_id=?
                      ORDER BY id DESC LIMIT 1) AND logged_out_at IS NULL""",
            (now, account_id))

    def presence(self, account_id, now, timeout):
        row = self.connection.execute("""SELECT last_action_at
            FROM account_activity WHERE account_id=?""", (account_id,)).fetchone()
        login = self.connection.execute("""SELECT logged_in_at FROM login_history
            WHERE account_id=? ORDER BY id DESC LIMIT 1""", (account_id,)).fetchone()
        return bool(row and 0 <= now - row[0] < timeout), login[0] if login else 0

    def relationship_counts(self, account_id):
        row = self.connection.execute("""SELECT
            (SELECT COUNT(*) FROM follows WHERE follower_id=?),
            (SELECT COUNT(*) FROM follows WHERE followed_id=?),
            (SELECT COUNT(*) FROM blocks WHERE blocker_id=?)""",
            (account_id, account_id, account_id)).fetchone()
        return dict(zip(("FollowCount", "FollowerCount", "BlockCount"), row))

    def relationship_flags(self, viewer_id, target_id):
        row = self.connection.execute("""SELECT
            EXISTS(SELECT 1 FROM follows WHERE follower_id=? AND followed_id=?),
            EXISTS(SELECT 1 FROM follows WHERE follower_id=? AND followed_id=?),
            EXISTS(SELECT 1 FROM blocks WHERE blocker_id=? AND blocked_id=?)""",
            (viewer_id, target_id, target_id, viewer_id, viewer_id, target_id)).fetchone()
        return dict(zip(("IsFollow", "IsFollower", "IsBlock"), map(bool, row)))

    def relationship_lists(self, account_id):
        queries = {
            "FollowUsers": "SELECT followed_id FROM follows WHERE follower_id=? ORDER BY followed_id",
            "FollowerUsers": "SELECT follower_id FROM follows WHERE followed_id=? ORDER BY follower_id",
            "BlockUsers": "SELECT blocked_id FROM blocks WHERE blocker_id=? ORDER BY blocked_id",
        }
        return {key: [row[0] for row in self.connection.execute(query, (account_id,))]
                for key, query in queries.items()}

    def change_relationship(self, account_id, target_id, action):
        if account_id == target_id:
            raise AccountError("Cannot follow or block yourself.")
        pair = (account_id, target_id)
        reverse = (target_id, account_id)
        if action == "follow":
            blocked = self.connection.execute("""SELECT 1 FROM blocks
                WHERE (blocker_id=? AND blocked_id=?) OR (blocker_id=? AND blocked_id=?)""",
                pair + reverse).fetchone()
            if blocked:
                raise AccountError("Cannot follow a blocked player.")
            self.connection.execute("INSERT OR IGNORE INTO follows VALUES (?, ?)", pair)
        elif action == "follow-release":
            self.connection.execute("DELETE FROM follows WHERE follower_id=? AND followed_id=?", pair)
        elif action == "follower-release":
            self.connection.execute("DELETE FROM follows WHERE follower_id=? AND followed_id=?", reverse)
        elif action == "block":
            self.connection.execute("INSERT OR IGNORE INTO blocks VALUES (?, ?)", pair)
            self.connection.execute("""DELETE FROM follows
                WHERE (follower_id=? AND followed_id=?) OR (follower_id=? AND followed_id=?)""",
                pair + reverse)
        elif action == "block-release":
            self.connection.execute("DELETE FROM blocks WHERE blocker_id=? AND blocked_id=?", pair)
        else:
            raise AccountError("Unknown relationship action.")

    def create(self, name, saves):
        if not isinstance(name, str) or not 2 <= len(name.strip()) <= 64:
            raise AccountError("Nickname must contain 2 to 64 characters.")
        account_id = secrets.token_hex(16)
        player_code = secrets.token_hex(8)
        user = {"id": account_id, "name": name, "idHash": account_id,
                "playerCode": player_code}
        self.connection.execute("INSERT INTO accounts VALUES (?, ?, ?)",
                                (account_id, player_code, int(time.time())))
        for key, value in saves.items():
            self.write(account_id, key, value)
        self.write(account_id, "User.json", user)
        if not self.exists(account_id, "checkpoint.txt"):
            self.write(account_id, "checkpoint.txt", {})
        token = secrets.token_urlsafe(32)
        self.connection.execute("INSERT INTO tokens VALUES (?, ?)",
                                (token_hash(token), account_id))
        return account_id, token

    def read(self, account_id, name):
        row = self.connection.execute(
            "SELECT value FROM saves WHERE account_id=? AND name=?",
            (account_id, name)).fetchone()
        if row is None:
            raise AccountError("Missing account save: " + name)
        return json.loads(row[0])

    def exists(self, account_id, name):
        return self.connection.execute(
            "SELECT 1 FROM saves WHERE account_id=? AND name=?",
            (account_id, name)).fetchone() is not None

    def write(self, account_id, name, value):
        self.connection.execute("""INSERT INTO saves VALUES (?, ?, ?)
            ON CONFLICT(account_id, name) DO UPDATE SET value=excluded.value""",
            (account_id, name, json.dumps(value, ensure_ascii=False)))

    def put_icon(self, account_id, png):
        revision = hashlib.sha256(png).hexdigest()
        self.connection.execute("""INSERT INTO icons VALUES (?, ?, ?)
            ON CONFLICT(account_id) DO UPDATE SET
                revision=excluded.revision, png=excluded.png""",
            (account_id, revision, png))
        return revision

    def get_icon(self, account_id, revision):
        row = self.connection.execute(
            "SELECT png FROM icons WHERE account_id=? AND revision=?",
            (account_id, revision)).fetchone()
        return row[0] if row else None

    def icon_revision(self, account_id):
        row = self.connection.execute("SELECT revision FROM icons WHERE account_id=?",
                                      (account_id,)).fetchone()
        return row[0] if row else None

    def find_account(self, identifier):
        row = self.connection.execute(
            "SELECT id FROM accounts WHERE id=? OR player_code=?",
            (identifier, identifier)).fetchone()
        return row[0] if row else None

    def search_accounts(self, query):
        """Resolve an exact ID/code, otherwise find up to 32 matching names."""
        account_id = self.find_account(query)
        if account_id is not None:
            return [account_id]
        query = query.casefold()
        matches = []
        for account_id, value in self.connection.execute(
                "SELECT account_id, value FROM saves WHERE name='User.json' ORDER BY account_id"):
            name = json.loads(value).get("name", "")
            if isinstance(name, str) and query in name.casefold():
                matches.append((name.casefold() != query, name.casefold(), account_id))
        return [match[2] for match in sorted(matches)[:32]]

    def close(self):
        self.connection.close()


def decode_icon(encoded):
    """Validate a bounded PNG without resizing the character capture."""
    if not isinstance(encoded, str) or len(encoded) > 2_800_000:
        raise AccountError("Invalid icon upload.")
    try:
        png = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AccountError("Icon must be base64 PNG data.") from exc
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise AccountError("Icon must be PNG data.")
    offset, chunks, data = 8, [], bytearray()
    width = height = 0
    while offset + 12 <= len(png):
        size = struct.unpack_from(">I", png, offset)[0]
        end = offset + 12 + size
        if end > len(png):
            raise AccountError("Truncated PNG.")
        kind = png[offset + 4:offset + 8]
        body = png[offset + 8:end - 4]
        crc = struct.unpack_from(">I", png, end - 4)[0]
        if zlib.crc32(kind + body) != crc:
            raise AccountError("Invalid PNG checksum.")
        if not chunks:
            if kind != b"IHDR" or size != 13:
                raise AccountError("Invalid PNG header.")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", body)
            if (not 1 <= width <= 1024 or not 1 <= height <= 1024
                    or depth != 8 or color not in (2, 6)
                    or compression or filtering or interlace):
                raise AccountError("Unsupported icon PNG format.")
        if kind == b"IDAT":
            data.extend(body)
        chunks.append(kind)
        offset = end
        if kind == b"IEND":
            if size or offset != len(png):
                raise AccountError("Invalid PNG end.")
            break
    if not chunks or chunks[-1] != b"IEND" or not data:
        raise AccountError("Incomplete PNG.")
    expected = height * (1 + width * (4 if color == 6 else 3))
    try:
        decoder = zlib.decompressobj()
        pixels = decoder.decompress(bytes(data), expected + 1)
        if len(pixels) != expected or not decoder.eof or decoder.unused_data:
            raise AccountError("Invalid PNG image data.")
    except zlib.error as exc:
        raise AccountError("Invalid PNG image data.") from exc
    stride = expected // height
    if any(pixels[i] > 4 for i in range(0, expected, stride)):
        raise AccountError("Invalid PNG filter.")
    return png
