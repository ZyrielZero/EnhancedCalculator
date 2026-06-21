"""Validation and normalization of user-supplied numbers."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from app.calculator_config import CalculatorConfig
from app.exceptions import ValidationError


@dataclass
class InputValidator:
    """Turns raw input into a clean Decimal, or rejects it."""

    @staticmethod
    def validate_number(value: Any, config: CalculatorConfig) -> Decimal:
        """Parse `value` into a Decimal within the configured bounds.

        Args:
            value: Anything the caller hands in (string, int, float, ...).
            config: Supplies the maximum allowed magnitude.

        Returns:
            The parsed value as a normalized Decimal.

        Raises:
            ValidationError: If the value can't be parsed or is too large.
        """
        try:
            if isinstance(value, str):
                value = value.strip()
            number = Decimal(str(value))
            if abs(number) > config.max_input_value:
                raise ValidationError(
                    f"Number exceeds the maximum allowed value: {config.max_input_value}"
                )
            return number.normalize()
        except InvalidOperation as e:
            raise ValidationError(f"Not a valid number: {value}") from e