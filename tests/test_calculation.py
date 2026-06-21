import pytest
import logging
from decimal import Decimal
from datetime import datetime

from app.calculation import Calculation
from app.exceptions import OperationError


def make(op, a, b):
    return Calculation(operation=op, operand1=Decimal(a), operand2=Decimal(b))


def test_addition_result():
    assert make("Addition", "8", "5").result == Decimal("13")


def test_subtraction_result():
    assert make("Subtraction", "10", "6").result == Decimal("4")


def test_multiplication_result():
    assert make("Multiplication", "7", "6").result == Decimal("42")


def test_division_result():
    assert make("Division", "20", "4").result == Decimal("5")


def test_power_result():
    assert make("Power", "3", "4").result == Decimal("81")


def test_root_result():
    assert make("Root", "81", "2").result == Decimal("9")


def test_division_by_zero_raises():
    with pytest.raises(OperationError, match="Division by zero is not allowed"):
        make("Division", "9", "0")


def test_negative_power_raises():
    with pytest.raises(OperationError, match="Negative exponents are not supported"):
        make("Power", "3", "-2")


def test_root_of_negative_raises():
    with pytest.raises(OperationError, match="Cannot calculate root of negative number"):
        make("Root", "-81", "2")


def test_unknown_operation_raises():
    with pytest.raises(OperationError, match="Unknown operation"):
        make("Modulo", "9", "4")


def test_calculation_failure_is_wrapped():
    # float overflow inside Power raises OverflowError, wrapped as OperationError
    with pytest.raises(OperationError, match="Calculation failed"):
        make("Power", "1e300", "2")


def test_to_dict_shape():
    calc = make("Addition", "8", "5")
    assert calc.to_dict() == {
        "operation": "Addition",
        "operand1": "8",
        "operand2": "5",
        "result": "13",
        "timestamp": calc.timestamp.isoformat(),
    }


def test_from_dict_rebuilds():
    data = {
        "operation": "Addition",
        "operand1": "8",
        "operand2": "5",
        "result": "13",
        "timestamp": datetime.now().isoformat(),
    }
    calc = Calculation.from_dict(data)
    assert calc.operation == "Addition"
    assert calc.operand1 == Decimal("8")
    assert calc.operand2 == Decimal("5")
    assert calc.result == Decimal("13")


def test_from_dict_invalid_data_raises():
    data = {
        "operation": "Addition",
        "operand1": "oops",
        "operand2": "5",
        "result": "13",
        "timestamp": datetime.now().isoformat(),
    }
    with pytest.raises(OperationError, match="Invalid calculation data"):
        Calculation.from_dict(data)


def test_from_dict_warns_on_result_mismatch(caplog):
    data = {
        "operation": "Addition",
        "operand1": "8",
        "operand2": "5",
        "result": "20",   # wrong on purpose; real result is 13
        "timestamp": datetime.now().isoformat(),
    }
    with caplog.at_level(logging.WARNING):
        Calculation.from_dict(data)
    assert "Loaded calculation result 20 differs from computed result 13" in caplog.text


def test_format_result_precision():
    calc = make("Division", "2", "3")
    assert calc.format_result(precision=2) == "0.67"
    assert calc.format_result(precision=10) == "0.6666666667"


def test_equality_between_calculations():
    a = make("Addition", "8", "5")
    b = make("Addition", "8", "5")
    c = make("Subtraction", "10", "6")
    assert a == b
    assert a != c


def test_equality_with_non_calculation():
    calc = make("Addition", "8", "5")
    assert (calc == "not a calculation") is False


def test_str_and_repr():
    calc = make("Addition", "8", "5")
    assert str(calc) == "Addition(8, 5) = 13"
    assert repr(calc).startswith("Calculation(operation='Addition'")