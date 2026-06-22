import pytest
from unittest.mock import Mock, patch

from app.calculation import Calculation
from app.history import LoggingObserver, AutoSaveObserver
from app.calculator import Calculator
from app.calculator_config import CalculatorConfig


# A stand-in calculation so we aren't coupled to real arithmetic here.
sample = Mock(spec=Calculation)
sample.operation = "Addition"
sample.operand1 = 8
sample.operand2 = 5
sample.result = 13


@patch('logging.info')
def test_logging_observer_writes_to_log(mock_log_info):
    LoggingObserver().update(sample)
    mock_log_info.assert_called_once_with(
        "Calculation performed: Addition (8, 5) = 13"
    )


def test_logging_observer_rejects_none():
    with pytest.raises(AttributeError):
        LoggingObserver().update(None)


def test_autosave_fires_when_enabled():
    calc = Mock(spec=Calculator)
    calc.config = Mock(spec=CalculatorConfig)
    calc.config.auto_save = True
    AutoSaveObserver(calc).update(sample)
    calc.save_history.assert_called_once()


@patch('logging.info')
def test_autosave_logs_when_it_saves(mock_log_info):
    calc = Mock(spec=Calculator)
    calc.config = Mock(spec=CalculatorConfig)
    calc.config.auto_save = True
    AutoSaveObserver(calc).update(sample)
    mock_log_info.assert_called_once_with("History auto-saved")


def test_autosave_skips_when_disabled():
    calc = Mock(spec=Calculator)
    calc.config = Mock(spec=CalculatorConfig)
    calc.config.auto_save = False
    AutoSaveObserver(calc).update(sample)
    calc.save_history.assert_not_called()


def test_autosave_rejects_bad_calculator():
    with pytest.raises(TypeError):
        AutoSaveObserver(None)


def test_autosave_rejects_none_calculation():
    calc = Mock(spec=Calculator)
    calc.config = Mock(spec=CalculatorConfig)
    calc.config.auto_save = True
    with pytest.raises(AttributeError):
        AutoSaveObserver(calc).update(None)