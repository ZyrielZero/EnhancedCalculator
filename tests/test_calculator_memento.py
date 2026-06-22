import datetime
from decimal import Decimal

from app.calculation import Calculation
from app.calculator_memento import CalculatorMemento


def make_history():
    return [
        Calculation(operation="Addition", operand1=Decimal("8"), operand2=Decimal("5")),
        Calculation(operation="Multiplication", operand1=Decimal("7"), operand2=Decimal("6")),
    ]


def test_holds_history_and_default_timestamp():
    history = make_history()
    memento = CalculatorMemento(history=history)
    assert memento.history == history
    assert isinstance(memento.timestamp, datetime.datetime)


def test_accepts_explicit_timestamp():
    moment = datetime.datetime(2025, 1, 2, 3, 4, 5)
    memento = CalculatorMemento(history=[], timestamp=moment)
    assert memento.timestamp == moment


def test_to_dict_serializes_history_and_timestamp():
    memento = CalculatorMemento(history=make_history())
    data = memento.to_dict()

    assert isinstance(data["history"], list)
    assert len(data["history"]) == 2
    assert data["history"][0]["operation"] == "Addition"
    assert data["history"][0]["result"] == "13"
    assert data["timestamp"] == memento.timestamp.isoformat()


def test_from_dict_rebuilds_snapshot():
    original = CalculatorMemento(history=make_history())
    restored = CalculatorMemento.from_dict(original.to_dict())

    assert len(restored.history) == 2
    assert restored.history[0].operation == "Addition"
    assert restored.history[0].result == Decimal("13")
    assert restored.history[1].operation == "Multiplication"
    assert restored.history[1].result == Decimal("42")
    assert restored.timestamp == original.timestamp


def test_round_trip_on_empty_history():
    memento = CalculatorMemento(history=[])
    restored = CalculatorMemento.from_dict(memento.to_dict())
    assert restored.history == []
    assert restored.timestamp == memento.timestamp