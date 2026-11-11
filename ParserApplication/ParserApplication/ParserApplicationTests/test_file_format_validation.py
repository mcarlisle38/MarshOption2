from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
APP_DIR = TESTS_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from Scripts.file_format_validation import CsvFileFormatValidator, JsonFileFormatValidator, XmlFileFormatValidator
from Scripts.parser_shared import ValidationError


class FileFormatValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.csv_validator = CsvFileFormatValidator()
        self.json_validator = JsonFileFormatValidator()
        self.xml_validator = XmlFileFormatValidator()

    def _write_temp_file(self, suffix: str, content: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        file_path = Path(temp_dir.name) / f"input{suffix}"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    # CSV
    def test_csv_success_valid_header_passes(self):
        content = (
            "transaction_uti,isin,notional,notional_currency,transaction_type,"
            "transaction_datetime,exchange_rate,legal_entity_identifier\n"
            "ABC123,US1234567890,1000.0,EUR,Buy,2024-01-10T12:34:00Z,1.0,ABCDEFGHIJ1234567890\n"
        )
        file_path = self._write_temp_file(".csv", content)
        self.csv_validator.validate(file_path)

    def test_csv_missing_field_fails(self):
        content = (
            "transaction_uti,isin,notional,notional_currency,transaction_type,"
            "transaction_datetime,exchange_rate\n"
            "ABC123,US1234567890,1000.0,EUR,Buy,2024-01-10T12:34:00Z,1.0\n"
        )
        file_path = self._write_temp_file(".csv", content)
        with self.assertRaises(ValidationError):
            self.csv_validator.validate(file_path)

    def test_csv_too_many_fields_fails(self):
        content = (
            "transaction_uti,isin,notional,notional_currency,transaction_type,"
            "transaction_datetime,exchange_rate,legal_entity_identifier,extra_field\n"
            "ABC123,US1234567890,1000.0,EUR,Buy,2024-01-10T12:34:00Z,1.0,ABCDEFGHIJ1234567890,x\n"
        )
        file_path = self._write_temp_file(".csv", content)
        with self.assertRaises(ValidationError):
            self.csv_validator.validate(file_path)

    def test_csv_incorrectly_named_field_fails(self):
        content = (
            "transaction_uti,isin,notional,notional_currency,transaction_type,"
            "transaction_datetime,exchange_rate,legal_entity_id\n"
            "ABC123,US1234567890,1000.0,EUR,Buy,2024-01-10T12:34:00Z,1.0,ABCDEFGHIJ1234567890\n"
        )
        file_path = self._write_temp_file(".csv", content)
        with self.assertRaises(ValidationError):
            self.csv_validator.validate(file_path)

    def test_csv_incorrect_case_field_fails(self):
        content = (
            "Transaction_Uti,Isin,Notional,Notional_Currency,Transaction_Type,"
            "Transaction_Datetime,Exchange_Rate,Legal_Entity_Identifier\n"
            "ABC123,US1234567890,1000.0,EUR,Buy,2024-01-10T12:34:00Z,1.0,ABCDEFGHIJ1234567890\n"
        )
        file_path = self._write_temp_file(".csv", content)
        with self.assertRaises(ValidationError):
            self.csv_validator.validate(file_path)

    # JSON
    def test_json_success_valid_format_passes(self):
        payload = {
            "transactions": [
                {
                    "transaction_uti": "ABC123",
                    "isin": "US1234567890",
                    "notional": "1000.0",
                    "notional_currency": "EUR",
                    "transaction_type": "Buy",
                    "transaction_datetime": "2024-01-10T12:34:00Z",
                    "exchange_rate": "1.0",
                    "lei": "ABCDEFGHIJ1234567890",
                }
            ]
        }
        file_path = self._write_temp_file(".json", json.dumps(payload))
        self.json_validator.validate(file_path)

    def test_json_missing_fields_fails(self):
        payload = {
            "transactions": [
                {
                    "transaction_uti": "ABC123",
                    "isin": "US1234567890",
                    "notional": "1000.0",
                    "notional_currency": "EUR",
                    "transaction_type": "Buy",
                    "transaction_datetime": "2024-01-10T12:34:00Z",
                    "exchange_rate": "1.0",
                }
            ]
        }
        file_path = self._write_temp_file(".json", json.dumps(payload))
        with self.assertRaises(ValidationError):
            self.json_validator.validate(file_path)

    def test_json_too_many_fields_fails(self):
        payload = {
            "transactions": [
                {
                    "transaction_uti": "ABC123",
                    "isin": "US1234567890",
                    "notional": "1000.0",
                    "notional_currency": "EUR",
                    "transaction_type": "Buy",
                    "transaction_datetime": "2024-01-10T12:34:00Z",
                    "exchange_rate": "1.0",
                    "lei": "ABCDEFGHIJ1234567890",
                    "extra": "unexpected",
                }
            ]
        }
        file_path = self._write_temp_file(".json", json.dumps(payload))
        with self.assertRaises(ValidationError):
            self.json_validator.validate(file_path)

    def test_json_incorrectly_named_field_fails(self):
        payload = {
            "transactions": [
                {
                    "transaction_uti": "ABC123",
                    "isin": "US1234567890",
                    "notional": "1000.0",
                    "notional_currency": "EUR",
                    "transaction_type": "Buy",
                    "transaction_datetime": "2024-01-10T12:34:00Z",
                    "exchange_rate": "1.0",
                    "legal_entity_identifier": "ABCDEFGHIJ1234567890",
                }
            ]
        }
        file_path = self._write_temp_file(".json", json.dumps(payload))
        with self.assertRaises(ValidationError):
            self.json_validator.validate(file_path)

    def test_json_incorrect_case_field_fails(self):
        payload = {
            "transactions": [
                {
                    "Transaction_Uti": "ABC123",
                    "Isin": "US1234567890",
                    "Notional": "1000.0",
                    "Notional_Currency": "EUR",
                    "Transaction_Type": "Buy",
                    "Transaction_Datetime": "2024-01-10T12:34:00Z",
                    "Exchange_Rate": "1.0",
                    "Lei": "ABCDEFGHIJ1234567890",
                }
            ]
        }
        file_path = self._write_temp_file(".json", json.dumps(payload))
        with self.assertRaises(ValidationError):
            self.json_validator.validate(file_path)

    def test_json_transactions_object_missing_fails(self):
        payload = {"data": []}
        file_path = self._write_temp_file(".json", json.dumps(payload))
        with self.assertRaises(ValidationError):
            self.json_validator.validate(file_path)

    def test_json_transactions_not_list_fails(self):
        payload = {"transactions": {"a": 1}}
        file_path = self._write_temp_file(".json", json.dumps(payload))
        with self.assertRaises(ValidationError):
            self.json_validator.validate(file_path)

    # XML
    def test_xml_success_valid_format_passes(self):
        content = """
<transactions>
  <transaction>
    <transaction_uti>ABC123</transaction_uti>
    <isin>US1234567890</isin>
    <notional>1000.0</notional>
    <notional_currency>EUR</notional_currency>
    <transaction_type>Buy</transaction_type>
    <transaction_datetime>2024-01-10T12:34:00Z</transaction_datetime>
    <exchange_rate>1.0</exchange_rate>
    <lei>ABCDEFGHIJ1234567890</lei>
  </transaction>
</transactions>
""".strip()
        file_path = self._write_temp_file(".xml", content)
        self.xml_validator.validate(file_path)

    def test_xml_missing_field_fails(self):
        content = """
<transactions>
  <transaction>
    <transaction_uti>ABC123</transaction_uti>
    <isin>US1234567890</isin>
    <notional>1000.0</notional>
    <notional_currency>EUR</notional_currency>
    <transaction_type>Buy</transaction_type>
    <transaction_datetime>2024-01-10T12:34:00Z</transaction_datetime>
    <exchange_rate>1.0</exchange_rate>
  </transaction>
</transactions>
""".strip()
        file_path = self._write_temp_file(".xml", content)
        with self.assertRaises(ValidationError):
            self.xml_validator.validate(file_path)

    def test_xml_too_many_fields_fails(self):
        content = """
<transactions>
  <transaction>
    <transaction_uti>ABC123</transaction_uti>
    <isin>US1234567890</isin>
    <notional>1000.0</notional>
    <notional_currency>EUR</notional_currency>
    <transaction_type>Buy</transaction_type>
    <transaction_datetime>2024-01-10T12:34:00Z</transaction_datetime>
    <exchange_rate>1.0</exchange_rate>
    <lei>ABCDEFGHIJ1234567890</lei>
    <extra>unexpected</extra>
  </transaction>
</transactions>
""".strip()
        file_path = self._write_temp_file(".xml", content)
        with self.assertRaises(ValidationError):
            self.xml_validator.validate(file_path)

    def test_xml_incorrectly_named_field_fails(self):
        content = """
<transactions>
  <transaction>
    <transaction_uti>ABC123</transaction_uti>
    <isin>US1234567890</isin>
    <notional>1000.0</notional>
    <notional_currency>EUR</notional_currency>
    <transaction_type>Buy</transaction_type>
    <transaction_datetime>2024-01-10T12:34:00Z</transaction_datetime>
    <exchange_rate>1.0</exchange_rate>
    <legal_entity_identifier>ABCDEFGHIJ1234567890</legal_entity_identifier>
  </transaction>
</transactions>
""".strip()
        file_path = self._write_temp_file(".xml", content)
        with self.assertRaises(ValidationError):
            self.xml_validator.validate(file_path)

    def test_xml_incorrect_case_field_fails(self):
        content = """
<transactions>
  <transaction>
    <Transaction_Uti>ABC123</Transaction_Uti>
    <Isin>US1234567890</Isin>
    <Notional>1000.0</Notional>
    <Notional_Currency>EUR</Notional_Currency>
    <Transaction_Type>Buy</Transaction_Type>
    <Transaction_Datetime>2024-01-10T12:34:00Z</Transaction_Datetime>
    <Exchange_Rate>1.0</Exchange_Rate>
    <Lei>ABCDEFGHIJ1234567890</Lei>
  </transaction>
</transactions>
""".strip()
        file_path = self._write_temp_file(".xml", content)
        with self.assertRaises(ValidationError):
            self.xml_validator.validate(file_path)

    def test_xml_transactions_object_missing_fails(self):
        content = """
<root>
  <transaction>
    <transaction_uti>ABC123</transaction_uti>
  </transaction>
</root>
""".strip()
        file_path = self._write_temp_file(".xml", content)
        with self.assertRaises(ValidationError):
            self.xml_validator.validate(file_path)


if __name__ == "__main__":
    unittest.main()
