import datetime
from pathlib import Path
from decimal import Decimal

import pandas as pd
import pytest
from unittest.mock import Mock, patch

from app.calculator import Calculator
from app.calculator_repl import calculator_repl
from app.calculator_config import CalculatorConfig
from app.exceptions import OperationError, ValidationError
from app.history import LoggingObserver
from app.operations import OperationFactory, Operation


@pytest.fixture(autouse=True)
def isolate_fs(tmp_path, monkeypatch):
    """Redirect all file paths into a per-test temp dir via env vars."""
    monkeypatch.setenv('CALCULATOR_LOG_DIR', str(tmp_path / 'logs'))
    monkeypatch.setenv('CALCULATOR_LOG_FILE', str(tmp_path / 'logs/calculator.log'))
    monkeypatch.setenv('CALCULATOR_HISTORY_DIR', str(tmp_path / 'history'))
    monkeypatch.setenv('CALCULATOR_HISTORY_FILE', str(tmp_path / 'history/history.csv'))
    yield tmp_path


@pytest.fixture
def calculator(tmp_path):
    return Calculator(config=CalculatorConfig(base_dir=tmp_path))


# ---------- Calculator: construction & logging ----------

def test_initial_state(calculator):
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []
    assert calculator.operation_strategy is None


@patch('app.calculator.logging.info')
def test_init_logs_message(mock_info):
    Calculator(CalculatorConfig())
    mock_info.assert_any_call("Calculator initialized with configuration")


def test_setup_logging_failure_propagates():
    with patch('app.calculator.logging.basicConfig', side_effect=OSError("no log")):
        with pytest.raises(OSError):
            Calculator(CalculatorConfig())


def test_init_warns_when_load_fails():
    with patch.object(Calculator, 'load_history', side_effect=OperationError("bad")), \
         patch('app.calculator.logging.warning') as mock_warn:
        Calculator(CalculatorConfig())
    assert any(
        "Could not load existing history" in str(c.args[0])
        for c in mock_warn.call_args_list if c.args
    )


# ---------- Observers ----------

def test_add_observer(calculator):
    obs = LoggingObserver()
    calculator.add_observer(obs)
    assert obs in calculator.observers


def test_remove_observer(calculator):
    obs = LoggingObserver()
    calculator.add_observer(obs)
    calculator.remove_observer(obs)
    assert obs not in calculator.observers


# ---------- Operations ----------

def test_set_operation(calculator):
    op = OperationFactory.create_operation('add')
    calculator.set_operation(op)
    assert calculator.operation_strategy is op


def test_perform_addition(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    assert calculator.perform_operation(8, 5) == Decimal('13')


def test_perform_validation_error(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    with pytest.raises(ValidationError):
        calculator.perform_operation('nope', 5)


def test_perform_without_operation(calculator):
    with pytest.raises(OperationError, match="No operation set"):
        calculator.perform_operation(8, 5)


def test_perform_wraps_unexpected_error(calculator):
    broken = Mock(spec=Operation)
    broken.execute.side_effect = RuntimeError("boom")
    calculator.set_operation(broken)
    with pytest.raises(OperationError, match="Operation failed"):
        calculator.perform_operation(8, 5)


def test_history_respects_max_size(calculator):
    calculator.config.max_history_size = 1
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(8, 5)
    calculator.perform_operation(2, 2)
    assert len(calculator.history) == 1


# ---------- Undo / redo ----------

def test_undo_and_redo(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(8, 5)
    assert calculator.undo() is True
    assert calculator.history == []
    assert calculator.redo() is True
    assert len(calculator.history) == 1


def test_undo_nothing(calculator):
    assert calculator.undo() is False


def test_redo_nothing(calculator):
    assert calculator.redo() is False


# ---------- Save / load ----------

@patch('app.calculator.pd.DataFrame.to_csv')
def test_save_history_with_data(mock_to_csv, calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(8, 5)
    calculator.save_history()
    mock_to_csv.assert_called()


@patch('app.calculator.pd.DataFrame.to_csv')
def test_save_history_empty(mock_to_csv, calculator):
    calculator.save_history()
    mock_to_csv.assert_called_once()


def test_save_history_error(calculator):
    with patch('app.calculator.pd.DataFrame.to_csv', side_effect=OSError("disk")):
        with pytest.raises(OperationError, match="Failed to save history"):
            calculator.save_history()


@patch('app.calculator.pd.read_csv')
@patch('app.calculator.Path.exists', return_value=True)
def test_load_history_with_data(mock_exists, mock_read, calculator):
    mock_read.return_value = pd.DataFrame({
        'operation': ['Addition'],
        'operand1': ['8'],
        'operand2': ['5'],
        'result': ['13'],
        'timestamp': [datetime.datetime.now().isoformat()],
    })
    calculator.load_history()
    assert len(calculator.history) == 1
    assert calculator.history[0].result == Decimal('13')


@patch('app.calculator.pd.read_csv', return_value=pd.DataFrame())
@patch('app.calculator.Path.exists', return_value=True)
def test_load_history_empty_file(mock_exists, mock_read, calculator):
    calculator.load_history()
    assert calculator.history == []


@patch('app.calculator.Path.exists', return_value=False)
def test_load_history_no_file(mock_exists, calculator):
    calculator.load_history()
    assert calculator.history == []


def test_load_history_error(calculator):
    with patch('app.calculator.Path.exists', return_value=True), \
         patch('app.calculator.pd.read_csv', side_effect=OSError("corrupt")):
        with pytest.raises(OperationError, match="Failed to load history"):
            calculator.load_history()


# ---------- Views ----------

def test_get_history_dataframe(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(8, 5)
    df = calculator.get_history_dataframe()
    assert len(df) == 1
    assert df.iloc[0]['operation'] == 'Addition'


def test_show_history(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(8, 5)
    assert calculator.show_history() == ['Addition(8, 5) = 13']


def test_clear_history(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    calculator.perform_operation(8, 5)
    calculator.clear_history()
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []


# ---------- REPL ----------

@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_repl_exit_saves(mock_print, mock_input):
    with patch('app.calculator.Calculator.save_history') as mock_save:
        calculator_repl()
        mock_save.assert_called_once()
        mock_print.assert_any_call("History saved successfully.")
        mock_print.assert_any_call("Goodbye!")


@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_repl_exit_save_failure(mock_print, mock_input):
    with patch('app.calculator.Calculator.save_history', side_effect=OSError("x")):
        calculator_repl()
        mock_print.assert_any_call("Warning: Could not save history: x")


@patch('builtins.input', side_effect=['help', 'exit'])
@patch('builtins.print')
def test_repl_help(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nAvailable commands:")


@patch('builtins.input', side_effect=['add', '8', '5', 'exit'])
@patch('builtins.print')
def test_repl_addition(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nResult: 13")


@patch('builtins.input', side_effect=['history', 'exit'])
@patch('builtins.print')
def test_repl_history_empty(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("No calculations in history")


@patch('builtins.input', side_effect=['add', '8', '5', 'history', 'exit'])
@patch('builtins.print')
def test_repl_history_entries(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nCalculation History:")


@patch('builtins.input', side_effect=['add', '8', '5', 'clear', 'exit'])
@patch('builtins.print')
def test_repl_clear(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("History cleared")


@patch('builtins.input', side_effect=['add', '8', '5', 'undo', 'exit'])
@patch('builtins.print')
def test_repl_undo(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Operation undone")


@patch('builtins.input', side_effect=['undo', 'exit'])
@patch('builtins.print')
def test_repl_undo_nothing(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Nothing to undo")


@patch('builtins.input', side_effect=['add', '8', '5', 'undo', 'redo', 'exit'])
@patch('builtins.print')
def test_repl_redo(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Operation redone")


@patch('builtins.input', side_effect=['redo', 'exit'])
@patch('builtins.print')
def test_repl_redo_nothing(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Nothing to redo")


@patch('builtins.input', side_effect=['save', 'exit'])
@patch('builtins.print')
def test_repl_save(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("History saved successfully")


@patch('builtins.input', side_effect=['save', 'exit'])
@patch('builtins.print')
def test_repl_save_error(mock_print, mock_input):
    with patch('app.calculator.Calculator.save_history', side_effect=OSError("x")):
        calculator_repl()
        mock_print.assert_any_call("Error saving history: x")


@patch('builtins.input', side_effect=['load', 'exit'])
@patch('builtins.print')
def test_repl_load(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("History loaded successfully")


@patch('builtins.input', side_effect=['load', 'exit'])
@patch('builtins.print')
def test_repl_load_error(mock_print, mock_input):
    with patch('app.calculator.Calculator.load_history', side_effect=OSError("x")):
        calculator_repl()
        mock_print.assert_any_call("Error loading history: x")


@patch('builtins.input', side_effect=['add', 'cancel', 'exit'])
@patch('builtins.print')
def test_repl_cancel_first(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Operation cancelled")


@patch('builtins.input', side_effect=['add', '8', 'cancel', 'exit'])
@patch('builtins.print')
def test_repl_cancel_second(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Operation cancelled")


@patch('builtins.input', side_effect=['divide', '8', '0', 'exit'])
@patch('builtins.print')
def test_repl_operation_error(mock_print, mock_input):
    calculator_repl()
    printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
    assert "Error:" in printed


@patch('builtins.input', side_effect=['add', '8', '5', 'exit'])
@patch('builtins.print')
def test_repl_unexpected_error(mock_print, mock_input):
    with patch('app.calculator_repl.OperationFactory.create_operation',
               side_effect=RuntimeError("weird")):
        calculator_repl()
        mock_print.assert_any_call("Unexpected error: weird")


@patch('builtins.input', side_effect=['bogus', 'exit'])
@patch('builtins.print')
def test_repl_unknown_command(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Unknown command: 'bogus'. Type 'help' for available commands.")


@patch('builtins.input', side_effect=[KeyboardInterrupt(), 'exit'])
@patch('builtins.print')
def test_repl_keyboard_interrupt(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nOperation cancelled")


@patch('builtins.input', side_effect=[EOFError()])
@patch('builtins.print')
def test_repl_eof(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nInput terminated. Exiting...")


@patch('builtins.input', side_effect=[RuntimeError("inner"), 'exit'])
@patch('builtins.print')
def test_repl_generic_inner_error(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Error: inner")


@patch('builtins.print')
def test_repl_fatal_error(mock_print):
    with patch('app.calculator_repl.Calculator', side_effect=Exception("init boom")):
        with pytest.raises(Exception):
            calculator_repl()
    mock_print.assert_any_call("Fatal error: init boom")