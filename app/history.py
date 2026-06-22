"""Observers that react to each new calculation (logging and auto-saving)."""

from abc import ABC, abstractmethod
import logging
from typing import Any

from app.calculation import Calculation


class HistoryObserver(ABC):
    """Interface every observer implements to be notified of a calculation."""

    @abstractmethod
    def update(self, calculation: Calculation) -> None:
        """Handle a freshly performed calculation."""
        pass  # pragma: no cover


class LoggingObserver(HistoryObserver):
    """Writes every calculation to the log."""

    def update(self, calculation: Calculation) -> None:
        if calculation is None:
            raise AttributeError("Calculation cannot be None")
        logging.info(
            f"Calculation performed: {calculation.operation} "
            f"({calculation.operand1}, {calculation.operand2}) = "
            f"{calculation.result}"
        )


class AutoSaveObserver(HistoryObserver):
    """Saves history automatically when auto-save is enabled."""

    def __init__(self, calculator: Any):
        if not hasattr(calculator, 'config') or not hasattr(calculator, 'save_history'):
            raise TypeError("Calculator must have 'config' and 'save_history' attributes")
        self.calculator = calculator

    def update(self, calculation: Calculation) -> None:
        if calculation is None:
            raise AttributeError("Calculation cannot be None")
        if self.calculator.config.auto_save:
            self.calculator.save_history()
            logging.info("History auto-saved")