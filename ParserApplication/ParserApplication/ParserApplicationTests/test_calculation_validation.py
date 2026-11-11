from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
APP_DIR = TESTS_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from Scripts.field_validation import SharedFieldValidator
from Scripts.parser_shared import ValidationError


class EurNotionalCalculationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = SharedFieldValidator()
        self.valid_raw = {
            "transaction_uti": "ABC123",
            "isin": "US1234567890",
            "notional": "1000.0",
            "notional_currency": "EUR",
            "transaction_type": "Buy",
            "transaction_datetime": "2024-01-10T12:34:00Z",
            "exchange_rate": "1.0000000000",
            "legal_entity_identifier": "ABCDEFGHIJ1234567890",
        }

    def normalize(self, **overrides):
        payload = dict(self.valid_raw)
        payload.update(overrides)
        return self.validator.normalize_transaction(payload)

    def test_eur_notional_equals_notional_when_exchange_rate_is_one(self):
        normalized = self.normalize(notional="1234.5", exchange_rate="1")
        self.assertEqual(normalized.eur_notional, Decimal("1234.5"))

    def test_eur_notional_rounds_half_up_to_one_decimal_place(self):
        normalized = self.normalize(notional="10.0", exchange_rate="1.05")
        self.assertEqual(normalized.eur_notional, Decimal("10.5"))

    def test_eur_notional_rounds_down_when_below_half_tenth(self):
        normalized = self.normalize(notional="10.0", exchange_rate="1.04")
        self.assertEqual(normalized.eur_notional, Decimal("10.4"))

    def test_eur_notional_zero_when_notional_is_zero(self):
        normalized = self.normalize(notional="0.0", exchange_rate="9999.9999999999")
        self.assertEqual(normalized.eur_notional, Decimal("0.0"))

    def test_eur_notional_max_boundary_is_accepted(self):
        normalized = self.normalize(notional="99999999.0", exchange_rate="1")
        self.assertEqual(normalized.eur_notional, Decimal("99999999.0"))

if __name__ == "__main__":
    unittest.main()
