import base64
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
import zlib

import msgpack

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import server
from accounts import AccountStore, default_saves, decode_icon, AccountError, SCHEMA_VERSION


def png(width=128, height=128, color=0):
    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body)))
    pixels = (b"\0" + bytes([color, 0, 0, 255]) * width) * height
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))


def seeds():
    return {
        "UserItems.json": [{"ItemId": "dish_3_01", "Count": 10}],
        "UserCharacter.json": [{"CharacterId": "pl001", "Level": 1,
                                "VisualEquipment": ["original"], "Exp": 0}],
        "UserEquipment.json": [],
        "UserEpisode.json": [{"EpisodeId": e, "Status": 0}
                             for e in ("pl001_ep001", "pl002_ep001")],
        "UserParameter.json": {"Gold": 10000, "FavoriteChrId": "pl001",
                               "EmblemId": "emblem_sh001_001", "Word": "Hello"},
        "HcBalance.json": {}, "PieUserSetting.json": {},
        "Presents.json": {"UserPresents": [], "userPresents": []},
        "checkpoint.txt": {},
    }


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "accounts.sqlite3"

    def test_unversioned_account_database_keeps_all_player_data(self):
        from accounts import INITIAL_SCHEMA
        with closing(sqlite3.connect(self.path)) as connection:
            connection.executescript(INITIAL_SCHEMA)
            connection.execute("INSERT INTO accounts VALUES (?, ?, ?)", ("existing", "code", 123))
            connection.execute("INSERT INTO tokens VALUES (?, ?)", ("hashed-token", "existing"))
            connection.execute("INSERT INTO saves VALUES (?, ?, ?)",
                               ("existing", "checkpoint.txt", '{"pl001_ep001":20000}'))
            connection.execute("INSERT INTO icons VALUES (?, ?, ?)", ("existing", "revision", png()))
            connection.commit()
            before = connection.iterdump()
            original = [line for line in before if line.startswith("INSERT")]
        store = AccountStore(self.path)
        self.assertEqual(store.connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
        self.assertEqual(store.read("existing", "checkpoint.txt"), {"pl001_ep001": 20000})
        store.close()
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual([line for line in connection.iterdump() if line.startswith("INSERT")], original)

    def test_newer_schema_is_rejected_without_modifying_database(self):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("PRAGMA user_version=99")
            connection.execute("CREATE TABLE future (value TEXT)")
            connection.commit()
        with self.assertRaisesRegex(RuntimeError, "newer"):
            AccountStore(self.path)
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 99)
            self.assertEqual(connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(), [("future",)])

    def test_failed_initialization_rolls_back_schema_and_version(self):
        with patch("accounts.INITIAL_SCHEMA", "CREATE TABLE incomplete (id TEXT); invalid SQL;"):
            with self.assertRaises(sqlite3.OperationalError):
                AccountStore(self.path)
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(), [])
        store = AccountStore(self.path)
        store.close()

    def test_concurrent_initialization_and_reopen_are_safe(self):
        def open_store(_):
            store = AccountStore(self.path)
            version = store.connection.execute("PRAGMA user_version").fetchone()[0]
            store.close()
            return version
        with ThreadPoolExecutor(max_workers=3) as pool:
            self.assertEqual(list(pool.map(open_store, range(3))), [SCHEMA_VERSION] * 3)

    def test_version_one_upgrade_preserves_saves_without_inventing_logins(self):
        from accounts import INITIAL_SCHEMA
        with closing(sqlite3.connect(self.path)) as connection:
            connection.executescript(INITIAL_SCHEMA)
            connection.execute("INSERT INTO accounts VALUES ('existing', 'code', 123)")
            connection.execute("INSERT INTO saves VALUES ('existing', 'custom.json', '{\"x\":42}')")
            connection.execute("PRAGMA user_version=1")
            connection.commit()
        store = AccountStore(self.path)
        self.addCleanup(store.close)
        self.assertEqual(store.read('existing', 'custom.json'), {'x': 42})
        self.assertEqual(store.presence('existing', 1000, 300), (False, 0))
        self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM login_history').fetchone()[0], 0)


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = str(Path(self.directory.name) / "accounts.sqlite3")
        self.config = patch.dict(server.app.config, {
            "TESTING": True, "ACCOUNT_DB": self.db, "ACCOUNT_DEFAULTS": seeds})
        self.config.start()
        self.addCleanup(self.config.stop)
        self.client = server.app.test_client()

    def post(self, path, data=None, token=None, client=None):
        return (client or self.client).post(path,
            data=msgpack.packb(data or {}, use_bin_type=True),
            content_type="application/msgpack",
            headers={"Authorization": token} if token else {})

    def unpack(self, response):
        self.assertEqual(response.status_code, 200, response.data)
        return msgpack.unpackb(response.data, raw=False)

    def register(self, name="Alice"):
        response = self.post("/api/user/register", {"name": name})
        user = self.unpack(response)["User"]
        token = response.headers["Authorization"]
        self.assertTrue(token.startswith("Bearer "))
        return user, token

    def saved(self, user, key):
        store = AccountStore(self.db)
        try:
            return store.read(user["id"], key)
        finally:
            store.close()

    def test_registration_login_and_restart_keep_identity(self):
        alice, token = self.register()
        bob, bob_token = self.register("Bob")
        self.assertNotEqual(alice["id"], bob["id"])
        self.assertNotEqual(alice["playerCode"], bob["playerCode"])
        self.assertNotEqual(token, bob_token)
        # A fresh client and freshly opened database represent a restarted session.
        login = self.unpack(self.post("/api/user/login", token=token,
                                     client=server.app.test_client()))
        self.assertEqual(login["user"], alice)
        self.assertEqual(login["loginInfo"]["name"], "Alice")
        info = self.unpack(self.post("/api/user/info", token=bob_token))
        self.assertEqual(info["user"], bob)

    def test_login_history_and_activity_based_presence(self):
        with patch('server.time.time', return_value=1000):
            alice, token = self.register()
            bob, bob_token = self.register('Bob')
        with patch('server.time.time', return_value=1100):
            self.unpack(self.post('/api/user/login', token=token))
        with patch('server.time.time', return_value=1200):
            self.unpack(self.post('/api/user/info', token=token))
        def view(now):
            with patch('server.time.time', return_value=now):
                return self.unpack(self.post('/api/user/other-user-info',
                    {'userIdInfo': [alice['id']]}, token=bob_token))['UserViews'][0]
        self.assertTrue(view(1499)['IsLogin'])
        self.assertFalse(view(1500)['IsLogin'])
        self.assertEqual(view(1500)['LastLoginAt'], '1970-01-01T00:18:20Z')
        with patch('server.time.time', return_value=1600):
            self.unpack(self.post('/api/user/info', token=token))
        self.assertTrue(view(1601)['IsLogin'])
        with closing(sqlite3.connect(self.db)) as connection:
            history = connection.execute('''SELECT logged_in_at, last_action_at,
                logged_out_at, source FROM login_history WHERE account_id=? ORDER BY id''',
                (alice['id'],)).fetchall()
        self.assertEqual(history, [(1000, 1000, None, 'register'), (1100, 1600, None, 'login')])

    def test_failed_requests_and_anonymous_heartbeat_do_not_refresh_presence(self):
        with patch('server.time.time', return_value=1000):
            alice, token = self.register()
        with patch('server.time.time', return_value=1200):
            self.assertEqual(self.post('/api/user/change-name', {'name': ''}, token=token).status_code, 400)
            self.assertEqual(self.post('/api/game/heartbeat', token=token).status_code, 200)
            self.assertEqual(self.post('/api/user/login', token='Bearer invalid').status_code, 401)
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute('SELECT last_action_at FROM account_activity WHERE account_id=?',
                (alice['id'],)).fetchone()[0], 1000)
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM login_history').fetchone()[0], 1)

    def test_noble_policy_applies_to_existing_saves_and_profiles(self):
        alice, token = self.register()
        store = AccountStore(self.db)
        try:
            parameter = store.read(alice['id'], 'UserParameter.json')
            parameter.update(NobleStartAtUnix=0, NobleEndAtUnix=0)
            store.write(alice['id'], 'UserParameter.json', parameter)
            store.connection.commit()
        finally:
            store.close()
        with server.app.test_request_context('/api/user/top'):
            server.g.account_id = alice['id']
            server.g.account_store = AccountStore(self.db)
            parameter = server.load_json('./data/user/UserParameter.json')
            self.assertLess(parameter['NobleStartAtUnix'], server.time.time())
            self.assertGreater(parameter['NobleEndAtUnix'], server.time.time())
        view = self.unpack(self.post('/api/user/other-user-info',
            {'userIdInfo': [alice['id']]}, token=token))['UserViews'][0]
        self.assertLess(view['NobleStartAt'], server.utc_date(server.time.time()))
        self.assertGreater(view['NobleEndAt'], server.utc_date(server.time.time()))
        self.assertEqual(self.saved(alice, 'UserParameter.json')['NobleEndAtUnix'], 0)

    def test_prelogin_routes_do_not_require_an_account(self):
        for path in ("/api/game/heartbeat", "/api/server-message/anonymous-list",
                     "/api/privacy-policy/get-terms-url", "/api/log/anonymous-action"):
            with self.subTest(path=path):
                self.assertEqual(self.post(path).status_code, 200)
        self.assertEqual(self.post("/api/user/get-migration-info").status_code, 501)

    def test_episode_list_uses_own_progress_and_shared_master_data(self):
        alice, token = self.register()
        _, bob_token = self.register("Bob")
        with patch.object(server, "fill_episode_master_group", return_value={}):
            self.unpack(self.post("/api/episode/check-point",
                {"episodeId": "pl001_ep001", "scenarioNo": 10000}, token))
        original = server.load_json
        def load(path):
            return [] if path == "./data/masterdata/EpisodeMasterData.json" else original(path)
        with patch.object(server, "load_json", side_effect=load):
            episodes = self.unpack(self.post("/api/episode/list", token=token))
            bob_episodes = self.unpack(self.post("/api/episode/list", token=bob_token))
        self.assertEqual(episodes["episodeUsers"], self.saved(alice, "UserEpisode.json"))
        self.assertEqual(bob_episodes["episodeUsers"][0]["Status"], 0)
        self.assertEqual(episodes["episodes"], bob_episodes["episodes"])

    def test_top_includes_own_profile_and_progress(self):
        alice, token = self.register()
        self.unpack(self.post("/api/user/change-view-param", {"favoriteChrId": "pl018"}, token))
        original = server.load_json
        def load(path):
            return [] if path.startswith("./data/masterdata/") else original(path)
        with patch.object(server, "load_json", side_effect=load):
            top = self.unpack(self.post("/api/user/top", token=token))
        self.assertEqual(top["user"], alice)
        self.assertEqual(top["parameter"]["FavoriteChrId"], "pl018")
        self.assertEqual(top["episodeUsers"], self.saved(alice, "UserEpisode.json"))

    def test_tokens_are_required_for_all_player_routes(self):
        for path in ("/api/user/login", "/api/user/info", "/api/user/top",
                     "/api/episode/list", "/api/episode/check-point",
                     "/api/present/list", "/api/character-icon/upload-icon",
                     "/api/user/unknown"):
            with self.subTest(path=path):
                self.assertEqual(self.post(path).status_code, 401)
                self.assertEqual(self.post(path, token="Bearer forged").status_code, 401)

    def test_nickname_is_not_a_credential(self):
        alice, _ = self.register("Same name")
        bob, _ = self.register("Same name")
        self.assertNotEqual(alice["id"], bob["id"])
        self.assertEqual(self.post("/api/user/register", {"name": "Alice"},
                                  "Bearer invalid").status_code, 401)

    def test_registration_with_existing_token_is_idempotent(self):
        alice, token = self.register()
        response = self.post("/api/user/register", {"name": "Replacement"}, token)
        self.assertEqual(self.unpack(response)["User"], alice)

    def test_names_and_profile_values_are_account_specific(self):
        alice, token = self.register()
        bob, bob_token = self.register("Bob")
        self.unpack(self.post("/api/user/change-name", {"name": "New Alice"}, token))
        self.unpack(self.post("/api/user/change-view-param",
            {"favoriteChrId": "pl002", "word": "My profile", "emblemId": "emblem_2"}, token))
        self.assertEqual(self.saved(alice, "User.json")["name"], "New Alice")
        self.assertEqual(self.saved(alice, "UserParameter.json")["FavoriteChrId"], "pl002")
        self.assertEqual(self.saved(bob, "UserParameter.json"), seeds()["UserParameter.json"])
        self.assertEqual(self.unpack(self.post("/api/user/login", token=bob_token))["user"], bob)

    def test_invalid_profile_update_rolls_back_earlier_fields(self):
        user, token = self.register()
        response = self.post("/api/user/change-view-param",
                             {"word": "changed", "favoriteChrId": 123}, token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.saved(user, "UserParameter.json")["Word"], "Hello")

    def test_character_loadout_persists_without_overwriting_progress_or_other_players(self):
        alice, token = self.register()
        bob, _ = self.register("Bob")
        response = self.post("/api/user/character-update", {"userCharacter": [
            {"CharacterId": "pl001", "VisualEquipment": ["new"], "Level": 999,
             "Exp": 999, "UnknownClientField": "ignored"}]}, token)
        updated = self.unpack(response)["UserCharacter"][0]
        self.assertEqual(updated["VisualEquipment"], ["new"])
        self.assertEqual(updated["Level"], 1)
        self.assertEqual(self.saved(bob, "UserCharacter.json"), seeds()["UserCharacter.json"])

    def test_character_update_accepts_camel_case_wire_fields(self):
        user, token = self.register()
        result = self.unpack(self.post("/api/user/character-update", {"userCharacter": [
            {"characterId": "pl001", "visualEquipment": ["new"]}]}, token))
        self.assertEqual(result["UserCharacter"][0]["VisualEquipment"], ["new"])
        self.assertEqual(self.saved(user, "UserCharacter.json")[0]["Level"], 1)

    def test_checkpoints_are_isolated_and_reset_only_own_save(self):
        alice, token = self.register()
        bob, bob_token = self.register("Bob")
        with patch.object(server, "fill_episode_master_group", return_value={}):
            self.unpack(self.post("/api/episode/check-point",
                {"episodeId": "pl001_ep001", "scenarioNo": 10000}, token))
            self.unpack(self.post("/api/episode/check-point",
                {"episodeId": "pl001_ep001", "scenarioNo": 20000}, bob_token))
        self.unpack(self.post("/api/episode/reset", {"episodeId": "pl001_ep001"}, token))
        self.assertEqual(self.saved(alice, "checkpoint.txt"), {})
        self.assertEqual(self.saved(bob, "checkpoint.txt"), {"pl001_ep001": 20000})

    def test_concurrent_requests_do_not_lose_checkpoint_updates(self):
        user, token = self.register()
        def save(episode):
            return self.post("/api/episode/check-point",
                {"episodeId": episode, "scenarioNo": 10000}, token,
                client=server.app.test_client()).status_code
        with patch.object(server, "fill_episode_master_group", return_value={}):
            with ThreadPoolExecutor(max_workers=2) as executor:
                self.assertEqual(list(executor.map(save, ("pl001_ep001", "pl002_ep001"))), [200, 200])
        self.assertEqual(len(self.saved(user, "checkpoint.txt")), 2)

    def test_failed_checkpoint_request_rolls_back_progress(self):
        user, token = self.register()
        with patch.object(server, "fill_episode_master_group", side_effect=RuntimeError("failed")):
            with self.assertRaises(RuntimeError):
                self.post("/api/episode/check-point",
                          {"episodeId": "pl001_ep001", "scenarioNo": 10000}, token)
        self.assertEqual(self.saved(user, "checkpoint.txt"), {})

    def test_portrait_is_png_and_is_still_available_after_restart(self):
        alice, token = self.register()
        bob, bob_token = self.register("Bob")
        image = png()
        url = self.unpack(self.post("/api/character-icon/upload-icon",
            {"icon": base64.b64encode(image).decode()}, token))["IconUrl"]
        response = server.app.test_client().get(urlsplit(url).path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "image/png")
        self.assertEqual(response.data, image)
        views = self.unpack(self.post("/api/user/other-user-info",
            {"userIdInfo": [alice["id"], bob["playerCode"]]}, bob_token))["UserViews"]
        self.assertEqual(views[0]["IconUrl"], url)
        self.assertIsNone(views[1]["IconUrl"])

    def test_portrait_update_changes_url_and_rejects_bad_upload(self):
        user, token = self.register()
        urls = []
        for image in (png(), png(200, 200, 100)):
            urls.append(self.unpack(self.post("/api/character-icon/upload-icon",
                {"icon": base64.b64encode(image).decode()}, token))["IconUrl"])
        self.assertNotEqual(*urls)
        self.assertEqual(self.client.get(urlsplit(urls[0]).path).status_code, 404)
        bad = self.post("/api/character-icon/upload-icon", {"icon": "not PNG"}, token)
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.client.get(urlsplit(urls[1]).path).data, png(200, 200, 100))

    def test_database_does_not_store_plaintext_tokens(self):
        _, token = self.register()
        with closing(sqlite3.connect(self.db)) as connection:
            hashes = [r[0] for r in connection.execute("SELECT hash FROM tokens")]
        self.assertNotIn(token[7:], hashes)

    def test_portrait_url_uses_https_behind_reverse_proxy(self):
        _, token = self.register()
        response = self.client.post("/api/character-icon/upload-icon",
            data=msgpack.packb({"icon": base64.b64encode(png()).decode()}),
            headers={"Authorization": token, "X-Forwarded-Proto": "https"},
            content_type="application/msgpack")
        self.assertTrue(self.unpack(response)["IconUrl"].startswith("https://"))

    def test_api_responses_use_messagepack_and_are_not_cached(self):
        _, token = self.register()
        response = self.post("/api/user/change-view-param", {"favoriteChrId": "pl018"}, token)
        self.assertEqual(response.content_type, "application/x-msgpack")
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_fallback_never_creates_raw_request_logs(self):
        _, token = self.register()
        with patch("builtins.open", side_effect=AssertionError("must not record requests")):
            # Path-based response fixtures use Path.open, not the old debug log writer.
            self.assertEqual(self.post("/api/user/check-device", token=token).status_code, 200)

    def test_purchase_attempts_are_disabled_and_do_not_create_gifts(self):
        user, token = self.register()
        response = self.post("/api/billing/is-buyable?productId=medium-pack", token=token)
        self.assertTrue(self.unpack(response)["IsStopped"])
        self.assertEqual(self.saved(user, "Presents.json"), seeds()["Presents.json"])

    def test_real_defaults_are_fresh_and_do_not_read_old_saves(self):
        data = default_saves()
        self.assertEqual(data["checkpoint.txt"], {})
        self.assertEqual(data["Presents.json"]["userPresents"], [])
        self.assertEqual(len(data["UserCharacter.json"]), 21)

    def test_invalid_registration_creates_no_account(self):
        self.assertEqual(self.post("/api/user/register", {"name": "x"}).status_code, 400)
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM accounts").fetchone()[0], 0)

    def test_png_validation_checks_dimensions_crc_and_complete_data(self):
        for image in (png(1025, 1), png()[:-5], png() + b"trailing"):
            with self.assertRaises(AccountError):
                decode_icon(base64.b64encode(image).decode())
        self.assertEqual(decode_icon(base64.b64encode(png(200, 200)).decode()), png(200, 200))


if __name__ == "__main__":
    unittest.main()
