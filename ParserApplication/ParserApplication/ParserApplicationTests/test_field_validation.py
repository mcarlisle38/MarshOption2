from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
APP_DIR = TESTS_DIR.parent / "ParserApplication"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from Scripts.field_validation import SharedFieldValidator
from Scripts.parser_shared import ValidationError


class SharedFieldValidatorTests(unittest.TestCase):
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

    def test_success_normalizes_all_fields(self):
        normalized = self.normalize()
        self.assertEqual(normalized.transaction_uti, "ABC123")
        self.assertEqual(normalized.isin, "US1234567890")
        self.assertEqual(normalized.notional, Decimal("1000.0"))
        self.assertEqual(normalized.notional_currency, "EUR")
        self.assertEqual(normalized.transaction_type, "Buy")
        self.assertEqual(normalized.transaction_datetime, "2024-01-10T12:34:00Z")
        self.assertEqual(normalized.exchange_rate, Decimal("1.0000000000"))
        self.assertEqual(normalized.legal_entity_identifier, "ABCDEFGHIJ1234567890")
        self.assertEqual(normalized.eur_notional, Decimal("1000.0"))

    def test_transaction_uti_too_long_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(transaction_uti="A" * 46)

    def test_transaction_uti_empty_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(transaction_uti="")

    def test_transaction_uti_null_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(transaction_uti=None)

    def test_transaction_uti_lowercase_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(transaction_uti="abc123")

    def test_isin_success_lowercase_is_normalized_to_upper(self):
        normalized = self.normalize(isin="us1234567890")
        self.assertEqual(normalized.isin, "US1234567890")

    def test_isin_too_long_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(isin="A" * 13)

    def test_isin_empty_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(isin="")

    def test_isin_null_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(isin=None)

    def test_notional_success_accepts_e_notation(self):
        normalized = self.normalize(notional="1E2")
        self.assertEqual(normalized.notional, Decimal("100.0"))

    def test_notional_too_large_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(notional="100000000.0")

    def test_notional_negative_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(notional="-0.1")

    def test_notional_non_numeric_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(notional="abc")

    def test_notional_empty_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(notional="")

    def test_notional_null_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(notional=None)

    def test_notional_more_than_one_decimal_place_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(notional="10.12")

    def test_notional_currency_success_lowercase_is_normalized(self):
        normalized = self.normalize(notional_currency="usd")
        self.assertEqual(normalized.notional_currency, "USD")

    def test_notional_currency_invalid_length_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(notional_currency="US")

    def test_notional_currency_empty_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(notional_currency="")

    def test_notional_currency_null_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(notional_currency=None)

    def test_transaction_type_accepts_upper_and_lower_case(self):
        self.assertEqual(self.normalize(transaction_type="BUY").transaction_type, "Buy")
        self.assertEqual(self.normalize(transaction_type="sell").transaction_type, "Sell")

    def test_transaction_type_invalid_alphabetic_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(transaction_type="hold")

    def test_transaction_type_invalid_numeric_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(transaction_type="1")

    def test_transaction_type_empty_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(transaction_type="")

    def test_transaction_type_null_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(transaction_type=None)

    def test_transaction_datetime_accepts_offset_and_normalizes_to_utc(self):
        normalized = self.normalize(transaction_datetime="2024-01-10T12:34+02:00")
        self.assertEqual(normalized.transaction_datetime, "2024-01-10T10:34:00Z")

    def test_transaction_datetime_accepts_minute_accuracy(self):
        normalized = self.normalize(transaction_datetime="2024-01-10T12:34+00:00")
        self.assertEqual(normalized.transaction_datetime, "2024-01-10T12:34:00Z")

    def test_transaction_datetime_without_timezone_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(transaction_datetime="2024-01-10T12:34:00")

    def test_transaction_datetime_with_microseconds_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(transaction_datetime="2024-01-10T12:34:00.123456+00:00")

    def test_exchange_rate_success_rounds_to_ten_decimals(self):
        normalized = self.normalize(exchange_rate="1.12345678905")
        self.assertEqual(normalized.exchange_rate, Decimal("1.1234567891"))

    def test_exchange_rate_negative_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(exchange_rate="-0.0000000001")

    def test_exchange_rate_zero_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(exchange_rate="0")

    def test_exchange_rate_non_numeric_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(exchange_rate="abc")

    def test_exchange_rate_empty_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(exchange_rate="")

    def test_exchange_rate_null_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(exchange_rate=None)

    def test_legal_entity_identifier_too_long_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(legal_entity_identifier="A" * 21)

    def test_legal_entity_identifier_empty_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(legal_entity_identifier="")

    def test_legal_entity_identifier_null_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(legal_entity_identifier=None)

    def test_legal_entity_identifier_lowercase_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(legal_entity_identifier="abc123")

    def test_eur_notional_too_large_fails(self):
        with self.assertRaises(ValidationError):
            self.normalize(notional="99999999.0", exchange_rate="2")


if __name__ == "__main__":
    unittest.main()
