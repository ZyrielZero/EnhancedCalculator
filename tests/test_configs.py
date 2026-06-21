import pytest
import os
from decimal import Decimal
from pathlib import Path

from app.calculator_config import CalculatorConfig, get_project_root
from app.exceptions import ConfigurationError


# Seed the environment once for the env-driven cases below.
os.environ['CALCULATOR_MAX_HISTORY_SIZE'] = '250'
os.environ['CALCULATOR_AUTO_SAVE'] = 'false'
os.environ['CALCULATOR_PRECISION'] = '6'
os.environ['CALCULATOR_MAX_INPUT_VALUE'] = '5000'
os.environ['CALCULATOR_DEFAULT_ENCODING'] = 'ascii'
os.environ['CALCULATOR_LOG_DIR'] = './env_logs'
os.environ['CALCULATOR_HISTORY_DIR'] = './env_history'
os.environ['CALCULATOR_HISTORY_FILE'] = './env_history/log.csv'
os.environ['CALCULATOR_LOG_FILE'] = './env_logs/run.log'


def drop_env(*names):
    for name in names:
        os.environ.pop(name, None)


def test_reads_values_from_environment():
    config = CalculatorConfig()
    assert config.max_history_size == 250
    assert config.auto_save is False
    assert config.precision == 6
    assert config.max_input_value == Decimal("5000")
    assert config.default_encoding == 'ascii'
    assert config.log_dir == Path('./env_logs').resolve()
    assert config.history_dir == Path('./env_history').resolve()
    assert config.history_file == Path('./env_history/log.csv').resolve()
    assert config.log_file == Path('./env_logs/run.log').resolve()


def test_constructor_args_win_over_environment():
    config = CalculatorConfig(
        max_history_size=42,
        auto_save=True,
        precision=3,
        max_input_value=Decimal("750"),
        default_encoding="utf-16",
    )
    assert config.max_history_size == 42
    assert config.auto_save is True
    assert config.precision == 3
    assert config.max_input_value == Decimal("750")
    assert config.default_encoding == "utf-16"


def test_directory_paths_derive_from_base_dir():
    drop_env('CALCULATOR_LOG_DIR', 'CALCULATOR_HISTORY_DIR')
    config = CalculatorConfig(base_dir=Path('/srv/calc'))
    assert config.log_dir == Path('/srv/calc/logs').resolve()
    assert config.history_dir == Path('/srv/calc/history').resolve()


def test_file_paths_derive_from_base_dir():
    drop_env('CALCULATOR_HISTORY_FILE', 'CALCULATOR_LOG_FILE')
    config = CalculatorConfig(base_dir=Path('/srv/calc'))
    assert config.history_file == Path('/srv/calc/history/calculator_history.csv').resolve()
    assert config.log_file == Path('/srv/calc/logs/calculator.log').resolve()


def test_auto_save_true_string():
    os.environ['CALCULATOR_AUTO_SAVE'] = 'true'
    assert CalculatorConfig(auto_save=None).auto_save is True


def test_auto_save_one_string():
    os.environ['CALCULATOR_AUTO_SAVE'] = '1'
    assert CalculatorConfig(auto_save=None).auto_save is True


def test_auto_save_false_string():
    os.environ['CALCULATOR_AUTO_SAVE'] = 'false'
    assert CalculatorConfig(auto_save=None).auto_save is False


def test_auto_save_zero_string():
    os.environ['CALCULATOR_AUTO_SAVE'] = '0'
    assert CalculatorConfig(auto_save=None).auto_save is False


def test_defaults_when_environment_is_empty():
    drop_env(
        'CALCULATOR_MAX_HISTORY_SIZE', 'CALCULATOR_AUTO_SAVE', 'CALCULATOR_PRECISION',
        'CALCULATOR_MAX_INPUT_VALUE', 'CALCULATOR_DEFAULT_ENCODING',
    )
    config = CalculatorConfig()
    assert config.max_history_size == 1000
    assert config.auto_save is True
    assert config.precision == 10
    assert config.max_input_value == Decimal("1e999")
    assert config.default_encoding == 'utf-8'


def test_rejects_non_positive_history_size():
    with pytest.raises(ConfigurationError, match="max_history_size must be positive"):
        CalculatorConfig(max_history_size=-1).validate()


def test_rejects_non_positive_precision():
    with pytest.raises(ConfigurationError, match="precision must be positive"):
        CalculatorConfig(precision=-1).validate()


def test_rejects_non_positive_max_input_value():
    with pytest.raises(ConfigurationError, match="max_input_value must be positive"):
        CalculatorConfig(max_input_value=Decimal("-1")).validate()