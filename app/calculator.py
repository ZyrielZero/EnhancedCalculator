"""The Calculator facade: one object that wires every subsystem together."""

from decimal import Decimal
import logging
import os
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento
from app.exceptions import OperationError, ValidationError
from app.history import HistoryObserver
from app.input_validators import InputValidator
from app.operations import Operation

Number = Union[int, float, Decimal]
CalculationResult = Union[Number, str]


class Calculator:
    """Coordinates operations, history, observers, config, and persistence."""

    def __init__(self, config: Optional[CalculatorConfig] = None):
        if config is None:
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            config = CalculatorConfig(base_dir=project_root)

        self.config = config
        self.config.validate()

        os.makedirs(self.config.log_dir, exist_ok=True)
        self._setup_logging()

        self.history: List[Calculation] = []
        self.operation_strategy: Optional[Operation] = None
        self.observers: List[HistoryObserver] = []
        self.undo_stack: List[CalculatorMemento] = []
        self.redo_stack: List[CalculatorMemento] = []

        self._setup_directories()

        try:
            self.load_history()
        except Exception as e:
            logging.warning(f"Could not load existing history: {e}")

        logging.info("Calculator initialized with configuration")

    def _setup_logging(self) -> None:
        """Point the logger at the configured log file."""
        try:
            os.makedirs(self.config.log_dir, exist_ok=True)
            log_file = self.config.log_file.resolve()
            logging.basicConfig(
                filename=str(log_file),
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                force=True,
            )
            logging.info(f"Logging initialized at: {log_file}")
        except Exception as e:
            print(f"Error setting up logging: {e}")
            raise

    def _setup_directories(self) -> None:
        """Ensure the history directory exists."""
        self.config.history_dir.mkdir(parents=True, exist_ok=True)

    def add_observer(self, observer: HistoryObserver) -> None:
        """Register an observer to be notified of calculations."""
        self.observers.append(observer)
        logging.info(f"Added observer: {observer.__class__.__name__}")

    def remove_observer(self, observer: HistoryObserver) -> None:
        """Stop notifying an observer."""
        self.observers.remove(observer)
        logging.info(f"Removed observer: {observer.__class__.__name__}")

    def notify_observers(self, calculation: Calculation) -> None:
        """Push a calculation out to every observer."""
        for observer in self.observers:
            observer.update(calculation)

    def set_operation(self, operation: Operation) -> None:
        """Choose the operation strategy for the next calculation."""
        self.operation_strategy = operation
        logging.info(f"Set operation: {operation}")

    def perform_operation(
        self,
        a: Union[str, Number],
        b: Union[str, Number],
    ) -> CalculationResult:
        """Validate inputs, run the current operation, record and announce it."""
        if not self.operation_strategy:
            raise OperationError("No operation set")

        try:
            validated_a = InputValidator.validate_number(a, self.config)
            validated_b = InputValidator.validate_number(b, self.config)

            result = self.operation_strategy.execute(validated_a, validated_b)

            calculation = Calculation(
                operation=str(self.operation_strategy),
                operand1=validated_a,
                operand2=validated_b,
            )

            self.undo_stack.append(CalculatorMemento(self.history.copy()))
            self.redo_stack.clear()
            self.history.append(calculation)

            if len(self.history) > self.config.max_history_size:
                self.history.pop(0)

            self.notify_observers(calculation)
            return result

        except ValidationError as e:
            logging.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Operation failed: {str(e)}")
            raise OperationError(f"Operation failed: {str(e)}")

    def save_history(self) -> None:
        """Write the history out to CSV via pandas."""
        try:
            self.config.history_dir.mkdir(parents=True, exist_ok=True)
            history_data = []
            for calc in self.history:
                history_data.append({
                    'operation': str(calc.operation),
                    'operand1': str(calc.operand1),
                    'operand2': str(calc.operand2),
                    'result': str(calc.result),
                    'timestamp': calc.timestamp.isoformat(),
                })

            if history_data:
                df = pd.DataFrame(history_data)
                df.to_csv(self.config.history_file, index=False)
                logging.info(f"History saved successfully to {self.config.history_file}")
            else:
                pd.DataFrame(
                    columns=['operation', 'operand1', 'operand2', 'result', 'timestamp']
                ).to_csv(self.config.history_file, index=False)
                logging.info("Empty history saved")

        except Exception as e:
            logging.error(f"Failed to save history: {e}")
            raise OperationError(f"Failed to save history: {e}")

    def load_history(self) -> None:
        """Read history back from CSV and rebuild the calculations."""
        try:
            if self.config.history_file.exists():
                df = pd.read_csv(self.config.history_file)
                if not df.empty:
                    self.history = [
                        Calculation.from_dict({
                            'operation': row['operation'],
                            'operand1': row['operand1'],
                            'operand2': row['operand2'],
                            'result': row['result'],
                            'timestamp': row['timestamp'],
                        })
                        for _, row in df.iterrows()
                    ]
                    logging.info(f"Loaded {len(self.history)} calculations from history")
                else:
                    logging.info("Loaded empty history file")
            else:
                logging.info("No history file found - starting with empty history")
        except Exception as e:
            logging.error(f"Failed to load history: {e}")
            raise OperationError(f"Failed to load history: {e}")

    def get_history_dataframe(self) -> pd.DataFrame:
        """Return the history as a pandas DataFrame."""
        history_data = []
        for calc in self.history:
            history_data.append({
                'operation': str(calc.operation),
                'operand1': str(calc.operand1),
                'operand2': str(calc.operand2),
                'result': str(calc.result),
                'timestamp': calc.timestamp,
            })
        return pd.DataFrame(history_data)

    def show_history(self) -> List[str]:
        """Return human-readable lines for each calculation."""
        return [
            f"{calc.operation}({calc.operand1}, {calc.operand2}) = {calc.result}"
            for calc in self.history
        ]

    def clear_history(self) -> None:
        """Wipe history and both undo/redo stacks."""
        self.history.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        logging.info("History cleared")

    def undo(self) -> bool:
        """Restore the previous history state. False if nothing to undo."""
        if not self.undo_stack:
            return False
        memento = self.undo_stack.pop()
        self.redo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = memento.history.copy()
        return True

    def redo(self) -> bool:
        """Reapply the last undone state. False if nothing to redo."""
        if not self.redo_stack:
            return False
        memento = self.redo_stack.pop()
        self.undo_stack.append(CalculatorMemento(self.history.copy()))
        self.history = memento.history.copy()
        return True