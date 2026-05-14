"""
Unit tests for `_migrate_legacy_symbol_denom` — the one-shot pref-value
rename from the cryptic legacy ``"symbol"`` to the readable ``"₿ symbol"``.

The migration runs in DisplayWallet.onCreate so any user who picked
"₿ sats" (stored value "symbol") on an earlier build gets their pref
converted on first launch under 0.4.1+.

The migration is idempotent — these tests pin that contract.

Usage (from the LightningPiggyApp repo root):
    Desktop: bash tests/unittest.sh tests/test_symbol_denom_migration.py
    Device:  bash tests/unittest.sh tests/test_symbol_denom_migration.py --ondevice
"""

import unittest

try:
    from displaywallet import _migrate_legacy_symbol_denom
    _HAVE = True
except Exception:
    _HAVE = False


class _StubPrefs:
    """Minimal SharedPreferences-like view that records writes — lets us
    assert what the migration did without touching the real on-disk file."""

    class _Editor:
        def __init__(self, prefs):
            self._prefs = prefs

        def put_string(self, key, value):
            self._prefs.writes.append((key, value))
            self._prefs._data[key] = value

        def commit(self):
            self._prefs.commits += 1

    def __init__(self, initial=None):
        self._data = dict(initial or {})
        self.writes = []
        self.commits = 0

    def get_string(self, key, default=None):
        v = self._data.get(key)
        return v if v is not None else default

    def edit(self):
        return self._Editor(self)


@unittest.skipUnless(_HAVE, "_migrate_legacy_symbol_denom not installed")
class TestMigrateLegacySymbolDenom(unittest.TestCase):

    def test_legacy_symbol_value_gets_migrated(self):
        # The exact regression case: user has the legacy "symbol" value
        # in prefs from an earlier build. After migration the pref must
        # hold "₿ symbol" and the helper must return True.
        prefs = _StubPrefs({"balance_denomination": "symbol"})
        migrated = _migrate_legacy_symbol_denom(prefs)
        self.assertTrue(migrated)
        self.assertEqual(prefs.get_string("balance_denomination"), "₿ symbol")
        # Exactly one write + commit — no accidental other prefs touched.
        self.assertEqual(prefs.writes, [("balance_denomination", "₿ symbol")])
        self.assertEqual(prefs.commits, 1)

    def test_already_migrated_is_no_op(self):
        # User already on the new value (post-migration boot, or fresh
        # install on 0.4.1+) — no write, no commit, helper returns False.
        prefs = _StubPrefs({"balance_denomination": "₿ symbol"})
        migrated = _migrate_legacy_symbol_denom(prefs)
        self.assertFalse(migrated)
        self.assertEqual(prefs.writes, [])
        self.assertEqual(prefs.commits, 0)

    def test_unrelated_denomination_is_no_op(self):
        # User picked something other than ₿ mode (bits, btc, sats, etc.)
        # — migration must not touch the pref.
        for unrelated in ("sats", "bits", "ubtc", "mbtc", "btc"):
            prefs = _StubPrefs({"balance_denomination": unrelated})
            migrated = _migrate_legacy_symbol_denom(prefs)
            self.assertFalse(migrated, "should be no-op for value '{}'".format(unrelated))
            self.assertEqual(prefs.get_string("balance_denomination"), unrelated)
            self.assertEqual(prefs.writes, [])

    def test_missing_denomination_is_no_op(self):
        # Fresh install / never-set: no pref → no migration.
        prefs = _StubPrefs({})
        migrated = _migrate_legacy_symbol_denom(prefs)
        self.assertFalse(migrated)
        self.assertEqual(prefs.writes, [])

    def test_idempotent_second_call_after_migration(self):
        # Run migration twice. First call migrates; second is no-op.
        # Asserts idempotency across app restarts (the user reboots
        # multiple times; the helper must keep being a no-op forever).
        prefs = _StubPrefs({"balance_denomination": "symbol"})
        first = _migrate_legacy_symbol_denom(prefs)
        second = _migrate_legacy_symbol_denom(prefs)
        self.assertTrue(first)
        self.assertFalse(second)
        # Total writes / commits: exactly 1 (from the first call).
        self.assertEqual(len(prefs.writes), 1)
        self.assertEqual(prefs.commits, 1)


if __name__ == "__main__":
    unittest.main()
