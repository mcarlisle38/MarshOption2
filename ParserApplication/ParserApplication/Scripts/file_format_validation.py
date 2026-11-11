from __future__ import annotations

import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from Scripts.parser_shared import IFileFormatValidator, ValidationError


class CsvFileFormatValidator(IFileFormatValidator):
    _required_fields = {
        "transaction_uti",
        "isin",
        "notional",
        "notional_currency",
        "transaction_type",
        "transaction_datetime",
        "exchange_rate",
        "legal_entity_identifier",
    }

    def validate(self, file_path: Path) -> None:
        with file_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle, delimiter=",")
            try:
                header = next(reader)
            except StopIteration as ex:
                raise ValidationError(f"CSV file '{file_path.name}' is empty.") from ex

            normalized_header = {column.strip() for column in header}
            if normalized_header != self._required_fields:
                raise ValidationError(f"CSV file '{file_path.name}' does not contain the expected header.")


class JsonFileFormatValidator(IFileFormatValidator):
    _required_fields = {
        "transaction_uti",
        "isin",
        "notional",
        "notional_currency",
        "transaction_type",
        "transaction_datetime",
        "exchange_rate",
        "lei",
    }

    def validate(self, file_path: Path) -> None:
        with file_path.open("r", encoding="utf-8") as handle:
            try:
                payload = json.load(handle)
            except json.JSONDecodeError as ex:
                raise ValidationError(f"JSON file '{file_path.name}' is not valid JSON.") from ex

        if not isinstance(payload, dict):
            raise ValidationError(f"JSON file '{file_path.name}' must contain an object at root level.")

        transactions_key = next((key for key in payload.keys() if key.lower() == "transactions"), None)
        if transactions_key is None:
            raise ValidationError(f"JSON file '{file_path.name}' must contain a transactions object.")

        transactions = payload[transactions_key]
        if not isinstance(transactions, list):
            raise ValidationError(f"JSON file '{file_path.name}' transactions must be a list.")

        for index, transaction in enumerate(transactions):
            if not isinstance(transaction, dict):
                raise ValidationError(f"JSON file '{file_path.name}' contains non-object transaction at index {index}.")
            keys = {str(key) for key in transaction.keys()}
            if keys != self._required_fields:
                raise ValidationError(f"JSON file '{file_path.name}' transaction at index {index} is missing required fields.")


class XmlFileFormatValidator(IFileFormatValidator):
    _required_fields = {
        "transaction_uti",
        "isin",
        "notional",
        "notional_currency",
        "transaction_type",
        "transaction_datetime",
        "exchange_rate",
        "lei",
    }

    def validate(self, file_path: Path) -> None:
        try:
            tree = ET.parse(file_path)
        except ET.ParseError as ex:
            raise ValidationError(f"XML file '{file_path.name}' is not valid XML.") from ex

        root = tree.getroot()
        if root.tag.lower() != "transactions":
            raise ValidationError(f"XML file '{file_path.name}' root element must be transactions.")

        transaction_nodes = [node for node in root if node.tag.lower() == "transaction"]
        for index, node in enumerate(transaction_nodes):
            children = {child.tag for child in node}
            if children != self._required_fields:
                raise ValidationError(f"XML file '{file_path.name}' transaction at index {index} is missing required fields.")
