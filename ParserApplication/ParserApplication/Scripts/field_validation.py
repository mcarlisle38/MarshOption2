from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping

from Scripts.parser_shared import IFieldValidator, NormalizedTransaction, ValidationError


class SharedFieldValidator(IFieldValidator):
    _max_notional = Decimal("99999999.0")
    _one_dp = Decimal("0.1")
    _ten_dp = Decimal("0.0000000001")

    def normalize_transaction(self, raw: Mapping[str, Any]) -> NormalizedTransaction:
        normalized_map = {str(k).lower(): v for k, v in raw.items()}

        transaction_uti = self._validate_transaction_uti(self._required_text(normalized_map, "transaction_uti"))
        isin = self._validate_isin(self._required_text(normalized_map, "isin"))
        notional = self._validate_notional(self._required_value(normalized_map, "notional"))
        notional_currency = self._validate_currency(self._required_text(normalized_map, "notional_currency"))
        transaction_type = self._validate_transaction_type(self._required_text(normalized_map, "transaction_type"))
        transaction_datetime = self._validate_datetime(self._required_text(normalized_map, "transaction_datetime"))
        exchange_rate = self._validate_exchange_rate(self._required_value(normalized_map, "exchange_rate"))
        legal_entity_identifier = self._validate_lei(self._required_text(normalized_map, "legal_entity_identifier"))

        eur_notional = self._validate_eur_notional(notional * exchange_rate)

        return NormalizedTransaction(
            transaction_uti=transaction_uti,
            isin=isin,
            notional=notional,
            notional_currency=notional_currency,
            eur_notional=eur_notional,
            transaction_type=transaction_type,
            transaction_datetime=transaction_datetime,
            exchange_rate=exchange_rate,
            legal_entity_identifier=legal_entity_identifier,
        )

    def _required_text(self, source: Mapping[str, Any], key: str) -> str:
        value = source.get(key)
        if value is None:
            raise ValidationError(f"Missing required field '{key}'.")
        value_text = str(value).strip()
        if value_text == "":
            raise ValidationError(f"Field '{key}' cannot be empty.")
        return value_text

    def _required_value(self, source: Mapping[str, Any], key: str) -> Any:
        if key not in source:
            raise ValidationError(f"Missing required field '{key}'.")
        return source[key]

    def _validate_transaction_uti(self, value: str) -> str:
        if len(value) > 45 or not re.fullmatch(r"[A-Z0-9]+", value):
            raise ValidationError("Invalid transaction_uti value.")
        return value

    def _validate_isin(self, value: str) -> str:
        if len(value) > 12 or not re.fullmatch(r"[A-Za-z0-9]+", value):
            raise ValidationError("Invalid isin value.")
        return value.upper()

    def _validate_notional(self, value: Any) -> Decimal:
        decimal_value = self._to_decimal(value, "notional")
        if decimal_value < 0 or decimal_value > self._max_notional:
            raise ValidationError("notional is outside the accepted range.")
        if decimal_value != decimal_value.quantize(self._one_dp):
            raise ValidationError("notional must have no more than 1 decimal place.")
        return decimal_value.quantize(self._one_dp)

    def _validate_currency(self, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z]{3}", value):
            raise ValidationError("Invalid notional_currency value.")
        return value.upper()

    def _validate_transaction_type(self, value: str) -> str:
        lowered = value.lower()
        if lowered not in {"buy", "sell"}:
            raise ValidationError("transaction_type must be Buy or Sell.")
        return lowered.capitalize()

    def _validate_datetime(self, value: str) -> str:
        candidate = value
        if candidate.endswith("Z"):
            candidate = f"{candidate[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError as ex:
            raise ValidationError("transaction_datetime is not a valid ISO date-time value.") from ex
        if parsed.tzinfo is None:
            raise ValidationError("transaction_datetime must include timezone information.")
        if parsed.microsecond != 0:
            raise ValidationError("transaction_datetime must only be accurate to seconds.")
        utc_value = parsed.astimezone(timezone.utc)
        return utc_value.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _validate_exchange_rate(self, value: Any) -> Decimal:
        decimal_value = self._to_decimal(value, "exchange_rate")
        if decimal_value < 0:
            raise ValidationError("exchange_rate must be non-negative.")
        return decimal_value.quantize(self._ten_dp, rounding=ROUND_HALF_UP)

    def _validate_lei(self, value: str) -> str:
        if len(value) > 20 or not re.fullmatch(r"[A-Z0-9]+", value):
            raise ValidationError("Invalid legal_entity_identifier value.")
        return value

    def _validate_eur_notional(self, value: Decimal) -> Decimal:
        rounded = value.quantize(self._one_dp, rounding=ROUND_HALF_UP)
        if rounded < 0 or rounded > self._max_notional:
            raise ValidationError("eur_notional is outside the accepted range.")
        return rounded

    def _to_decimal(self, value: Any, field_name: str) -> Decimal:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as ex:
            raise ValidationError(f"{field_name} is not a valid numeric value.") from ex
        if not decimal_value.is_finite():
            raise ValidationError(f"{field_name} must be a finite numeric value.")
        return decimal_value
