import pytest
from decimal import Decimal

from app.calculator_config import CalculatorConfig
from app.exceptions import ValidationError
from app.input_validators import InputValidator


config = CalculatorConfig(max_input_value=Decimal("1000000"))


def check(value):
    return InputValidator.validate_number(value, config)


# --- accepted inputs ---

def test_accepts_positive_int():
    assert check(150) == Decimal("150")

def test_accepts_positive_float():
    assert check(3.14) == Decimal("3.14").normalize()

def test_accepts_positive_string():
    assert check("275") == Decimal("275")

def test_accepts_decimal_string():
    assert check("12.5") == Decimal("12.5").normalize()

def test_accepts_negative_int():
    assert check(-64) == Decimal("-64")

def test_accepts_negative_decimal_string():
    assert check("-9.75") == Decimal("-9.75").normalize()

def test_accepts_zero():
    assert check(0) == Decimal("0")

def test_strips_surrounding_whitespace():
    assert check("   88   ") == Decimal("88")


# --- rejected inputs ---

def test_rejects_non_numeric_string():
    with pytest.raises(ValidationError, match="Not a valid number"):
        check("hello")

def test_rejects_value_over_max():
    with pytest.raises(ValidationError, match="exceeds the maximum"):
        check(Decimal("1000001"))

def test_rejects_value_over_max_as_string():
    with pytest.raises(ValidationError, match="exceeds the maximum"):
        check("1000001")

def test_rejects_negative_value_over_max():
    with pytest.raises(ValidationError, match="exceeds the maximum"):
        check(Decimal("-1000001"))

def test_rejects_empty_string():
    with pytest.raises(ValidationError, match="Not a valid number"):
        check("")

def test_rejects_whitespace_only_string():
    with pytest.raises(ValidationError, match="Not a valid number"):
        check("   ")

def test_rejects_none():
    with pytest.raises(ValidationError, match="Not a valid number"):
        check(None)

def test_rejects_non_numeric_type():
    with pytest.raises(ValidationError, match="Not a valid number"):
        check([])