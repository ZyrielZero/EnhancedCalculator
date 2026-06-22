# Enhanced Calculator

A command-line REPL calculator built around five classic design patterns, with a
`Decimal`-based arithmetic core, pandas-backed history, environment-driven
configuration, and a test suite enforced at 100% coverage through pytest and
GitHub Actions.

## Features

- Six operations: addition, subtraction, multiplication, division, power, root
- Interactive REPL with `help`, `history`, `clear`, `undo`, `redo`, `save`, `load`, `exit`
- Calculation history persisted to CSV via pandas, auto-loaded on startup
- Undo/redo through saved state snapshots
- Configuration via environment variables (and an optional `.env` file)
- Comprehensive error handling using both LBYL and EAFP styles

## Design patterns

| Pattern   | Where it lives |
|-----------|----------------|
| Strategy  | `Operation` subclasses in `operations.py`, selected via `Calculator.set_operation` |
| Factory   | `OperationFactory.create_operation` builds operations by name |
| Observer  | `HistoryObserver` / `LoggingObserver` / `AutoSaveObserver` in `history.py` |
| Memento   | `CalculatorMemento` plus the undo/redo stacks in `calculator.py` |
| Facade    | `Calculator` presents one interface over every subsystem |

## Project structure

```
EnhancedCalculator/
├── app/
│   ├── calculation.py          # value object: one finished calculation
│   ├── calculator.py           # the Facade tying everything together
│   ├── calculator_config.py    # environment-driven settings
│   ├── calculator_memento.py   # undo/redo snapshots
│   ├── calculator_repl.py      # interactive loop
│   ├── exceptions.py           # custom exception hierarchy
│   ├── history.py              # observers (logging, auto-save)
│   ├── input_validators.py     # input parsing and bounds checks
│   └── operations.py           # operations + factory
├── tests/                      # one test module per app module
├── main.py                     # entry point
├── pytest.ini                  # coverage gate config
└── requirements.txt
```

## Setup

```bash
git clone https://github.com/ZyrielZero/EnhancedCalculator.git
cd EnhancedCalculator

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

The REPL prompts for a command, then for operands when one is needed:

```
Enter command: add

Enter numbers (or 'cancel' to abort):
First number: 8
Second number: 5

Result: 13
```

Available commands:

- `add`, `subtract`, `multiply`, `divide`, `power`, `root` — perform a calculation
- `history` — show the session's calculations
- `clear` — empty the history
- `undo` / `redo` — step backward or forward through history
- `save` / `load` — write history to CSV or read it back
- `help` — list commands
- `exit` — save and quit

## Configuration

All settings are optional and fall back to defaults. Set them in the environment
or in a `.env` file at the project root.

| Variable | Default | Purpose |
|----------|---------|---------|
| `CALCULATOR_BASE_DIR` | project root | Base for log/history paths |
| `CALCULATOR_MAX_HISTORY_SIZE` | `1000` | Cap on stored calculations |
| `CALCULATOR_AUTO_SAVE` | `true` | Save automatically after each calculation |
| `CALCULATOR_PRECISION` | `10` | Decimal places for display |
| `CALCULATOR_MAX_INPUT_VALUE` | `1e999` | Largest allowed operand magnitude |
| `CALCULATOR_DEFAULT_ENCODING` | `utf-8` | File encoding |

## Running tests

```bash
pytest
```

This runs the full suite and enforces 100% coverage through `pytest.ini`. The
build fails if coverage drops below 100%. GitHub Actions runs the same command
on every push and pull request to `main`.