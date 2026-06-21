import pytest
from decimal import Decimal
from typing import Any, Dict, Type

from app.exceptions import ValidationError
from app.operations import (
    Operation,
    Addition,
    Subtraction,
    Multiplication,
    Division,
    Power,
    Root,
    OperationFactory,
)


class TestOperation:
    """Tests for the abstract base Operation."""

    def test_str_returns_class_name(self):
        class SampleOp(Operation):
            def execute(self, a: Decimal, b: Decimal) -> Decimal:
                return a

        assert str(SampleOp()) == "SampleOp"


class BaseOperationTest:
    """Shared driver: each subclass supplies its own case tables."""

    operation_class: Type[Operation]
    valid_test_cases: Dict[str, Dict[str, Any]]
    invalid_test_cases: Dict[str, Dict[str, Any]]

    def test_valid_operations(self):
        operation = self.operation_class()
        for name, case in self.valid_test_cases.items():
            a = Decimal(str(case["a"]))
            b = Decimal(str(case["b"]))
            expected = Decimal(str(case["expected"]))
            assert operation.execute(a, b) == expected, f"Failed case: {name}"

    def test_invalid_operations(self):
        operation = self.operation_class()
        for name, case in self.invalid_test_cases.items():
            a = Decimal(str(case["a"]))
            b = Decimal(str(case["b"]))
            error = case.get("error", ValidationError)
            message = case.get("message", "")
            with pytest.raises(error, match=message):
                operation.execute(a, b)


class TestAddition(BaseOperationTest):
    operation_class = Addition
    valid_test_cases = {
        "positive_numbers": {"a": "7", "b": "4", "expected": "11"},
        "negative_numbers": {"a": "-7", "b": "-4", "expected": "-11"},
        "mixed_signs": {"a": "-7", "b": "4", "expected": "-3"},
        "cancels_to_zero": {"a": "6", "b": "-6", "expected": "0"},
        "decimals": {"a": "6.4", "b": "2.1", "expected": "8.5"},
        "large_numbers": {"a": "1e9", "b": "1e9", "expected": "2000000000"},
    }
    invalid_test_cases = {}


class TestSubtraction(BaseOperationTest):
    operation_class = Subtraction
    valid_test_cases = {
        "positive_numbers": {"a": "9", "b": "4", "expected": "5"},
        "negative_numbers": {"a": "-9", "b": "-4", "expected": "-5"},
        "mixed_signs": {"a": "-9", "b": "4", "expected": "-13"},
        "equal_operands": {"a": "4", "b": "4", "expected": "0"},
        "decimals": {"a": "7.5", "b": "2.2", "expected": "5.3"},
        "large_numbers": {"a": "5e9", "b": "2e9", "expected": "3000000000"},
    }
    invalid_test_cases = {}


class TestMultiplication(BaseOperationTest):
    operation_class = Multiplication
    valid_test_cases = {
        "positive_numbers": {"a": "6", "b": "4", "expected": "24"},
        "negative_numbers": {"a": "-6", "b": "-4", "expected": "24"},
        "mixed_signs": {"a": "-6", "b": "4", "expected": "-24"},
        "times_zero": {"a": "6", "b": "0", "expected": "0"},
        "decimals": {"a": "1.5", "b": "1.5", "expected": "2.25"},
        "large_numbers": {"a": "1e6", "b": "1e4", "expected": "10000000000"},
    }
    invalid_test_cases = {}


class TestDivision(BaseOperationTest):
    operation_class = Division
    valid_test_cases = {
        "positive_numbers": {"a": "12", "b": "4", "expected": "3"},
        "negative_numbers": {"a": "-12", "b": "-4", "expected": "3"},
        "mixed_signs": {"a": "-12", "b": "4", "expected": "-3"},
        "decimals": {"a": "7.5", "b": "2", "expected": "3.75"},
        "zero_numerator": {"a": "0", "b": "7", "expected": "0"},
    }
    invalid_test_cases = {
        "divide_by_zero": {
            "a": "8", "b": "0",
            "error": ValidationError,
            "message": "Division by zero is not allowed",
        },
    }


class TestPower(BaseOperationTest):
    operation_class = Power
    valid_test_cases = {
        "square": {"a": "3", "b": "2", "expected": "9"},
        "fourth_power": {"a": "2", "b": "4", "expected": "16"},
        "zero_exponent": {"a": "7", "b": "0", "expected": "1"},
        "one_exponent": {"a": "7", "b": "1", "expected": "7"},
        "decimal_base": {"a": "1.5", "b": "2", "expected": "2.25"},
        "zero_base": {"a": "0", "b": "4", "expected": "0"},
    }
    invalid_test_cases = {
        "negative_exponent": {
            "a": "3", "b": "-2",
            "error": ValidationError,
            "message": "Negative exponents not supported",
        },
    }


class TestRoot(BaseOperationTest):
    operation_class = Root
    valid_test_cases = {
        "square_root": {"a": "25", "b": "2", "expected": "5"},
        "square_root_large": {"a": "81", "b": "2", "expected": "9"},
        "fourth_root": {"a": "81", "b": "4", "expected": "3"},
        "fourth_root_small": {"a": "16", "b": "4", "expected": "2"},
        "decimal_root": {"a": "6.25", "b": "2", "expected": "2.5"},
    }
    invalid_test_cases = {
        "negative_base": {
            "a": "-25", "b": "2",
            "error": ValidationError,
            "message": "Cannot calculate root of negative number",
        },
        "zero_root": {
            "a": "16", "b": "0",
            "error": ValidationError,
            "message": "Zero root is undefined",
        },
    }


class TestOperationFactory:
    def test_create_valid_operations(self):
        operation_map = {
            'add': Addition,
            'subtract': Subtraction,
            'multiply': Multiplication,
            'divide': Division,
            'power': Power,
            'root': Root,
        }
        for op_name, op_class in operation_map.items():
            assert isinstance(OperationFactory.create_operation(op_name), op_class)
            assert isinstance(OperationFactory.create_operation(op_name.upper()), op_class)

    def test_create_invalid_operation(self):
        with pytest.raises(ValueError, match="Unknown operation: modulo"):
            OperationFactory.create_operation("modulo")

    def test_register_valid_operation(self):
        class ModuloOperation(Operation):
            def execute(self, a: Decimal, b: Decimal) -> Decimal:
                return a % b

        OperationFactory.register_operation("modulo", ModuloOperation)
        assert isinstance(OperationFactory.create_operation("modulo"), ModuloOperation)

    def test_register_invalid_operation(self):
        class NotAnOperation:
            pass

        with pytest.raises(TypeError, match="Operation class must inherit"):
            OperationFactory.register_operation("bad", NotAnOperation)