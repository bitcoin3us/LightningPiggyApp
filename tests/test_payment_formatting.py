"""
Unit tests for Payment.__str__ — verifies transaction amounts use the
MicroPythonOS NumberFormat thousands separator so transaction lines on
screen match the balance label's separator style.

Regression coverage for a real bug: previously Payment used raw f-string
interpolation (`f"{amount_sats}"`), so the balance row showed "₿8,984"
but the transaction row showed "₿8984" — inconsistent thousands
separator on the same screen.

Usage (from the LightningPiggyApp repo root):
    Desktop: bash tests/unittest.sh tests/test_payment_formatting.py
    Device:  bash tests/unittest.sh tests/test_payment_formatting.py --ondevice
"""

import unittest

from payment import Payment


class TestPaymentSatsFormatting(unittest.TestCase):
    """Default mode (use_symbol=False) — amount shown with "sats" suffix
    and thousands separator from the user's NumberFormat preference
    (which defaults to "comma_dot" — US style 1,234.56)."""

    def setUp(self):
        Payment.use_symbol = False

    def test_small_amount_with_comment(self):
        # 47 sats — too small for a thousands separator. Verifies the
        # base rendering path with a comment.
        p = Payment(1775838000, 47, "Braiins Pool mining reward")
        self.assertEqual(str(p), "47 sats: Braiins Pool mining reward")

    def test_thousands_separator_default_locale(self):
        # 8984 — must contain a thousands separator. The exact separator
        # ("," vs "." vs " ") depends on the device's NumberFormat pref;
        # we just assert "no longer raw 8984" (the bug condition).
        p = Payment(1775838000, 8984, "Apr 9 confirmed")
        s = str(p)
        # Either US "8,984", European "8.984", French "8 984", etc.
        # Bare digit-string "8984" should NEVER appear in the output.
        self.assertFalse("8984" in s, "raw value 8984 leaked into output: {}".format(s))
        # Sanity: the comment and "sats" suffix are still there.
        self.assertTrue("Apr 9 confirmed" in s)
        self.assertTrue("sats" in s)

    def test_singular_sat_for_amount_one(self):
        # Quirky edge case: 1 sat uses "sat" (singular) not "sats".
        p = Payment(1775838000, 1, "lonely satoshi")
        self.assertEqual(str(p), "1 sat: lonely satoshi")

    def test_received_verb_no_comment(self):
        # When comment is empty AND amount > 0 → "<amount> sats received!"
        p = Payment(1775838000, 6884, "")
        self.assertTrue("received!" in str(p))
        self.assertFalse("6884" in str(p))  # separator still applied

    def test_spent_verb_no_comment_negative_amount(self):
        # Negative amount + no comment → "<amount> sats spent"
        p = Payment(1775838000, -5000, "")
        s = str(p)
        self.assertTrue("spent" in s)
        # Negative sign preserved; magnitude formatted with separator.
        self.assertTrue(s.startswith("-"))
        self.assertFalse("-5000" in s, "raw value -5000 leaked: {}".format(s))

    def test_large_amount_seven_digits(self):
        # 1,234,567 sats — checks the separator goes in BOTH gap positions.
        p = Payment(1775838000, 1234567, "big tx")
        s = str(p)
        self.assertFalse("1234567" in s, "raw value leaked: {}".format(s))


class TestPaymentSymbolFormatting(unittest.TestCase):
    """₿-symbol mode (use_symbol=True) — amount shown with "₿" prefix
    and same thousands-separator behavior."""

    def setUp(self):
        Payment.use_symbol = True

    def tearDown(self):
        # Reset for any subsequent tests in the run.
        Payment.use_symbol = False

    def test_with_comment_has_btc_symbol_and_separator(self):
        p = Payment(1775838000, 8984, "Apr 9 confirmed")
        s = str(p)
        self.assertTrue(s.startswith("₿"))
        self.assertTrue("Apr 9 confirmed" in s)
        self.assertFalse("₿8984" in s, "raw value after ₿ leaked: {}".format(s))
        # No "sats" suffix in symbol mode.
        self.assertFalse(" sats" in s)

    def test_received_verb_no_comment_symbol(self):
        p = Payment(1775838000, 47, "")
        s = str(p)
        # "₿47 received!" — small enough that 47 has no separator,
        # so this is the literal expected string.
        self.assertEqual(s, "₿47 received!")

    def test_large_amount_with_separator_symbol_mode(self):
        # Use a value that requires a thousands separator regardless of locale.
        p = Payment(1775838000, 1234567, "")
        s = str(p)
        self.assertTrue(s.startswith("₿"))
        self.assertFalse("₿1234567" in s)


class TestPaymentNumberFormatPreference(unittest.TestCase):
    """Pin down that whatever the MPOS NumberFormat preference returns is
    what Payment uses — protects against silently bypassing the framework
    helper (e.g. a future refactor that reintroduces raw f-string)."""

    def test_payment_uses_number_format_module(self):
        # If the NumberFormat module is available on this build, payment
        # MUST be using it (otherwise the bug regresses). We don't assert
        # the *literal* separator character because that depends on the
        # device's `number_format` pref — instead we assert payment's
        # output matches what NumberFormat.format_number would produce.
        try:
            from mpos import NumberFormat
        except ImportError:
            self.skipTest("NumberFormat not available on this build")
        Payment.use_symbol = False
        try:
            p = Payment(1775838000, 8984, "test")
            expected_amount = NumberFormat.format_number(8984)
            self.assertTrue(expected_amount in str(p),
                "Payment output '{}' doesn't include NumberFormat's '{}'".format(
                    str(p), expected_amount))
        finally:
            Payment.use_symbol = False


if __name__ == "__main__":
    unittest.main()
