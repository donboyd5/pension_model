This repo contains a Python pension simulation model. It was based initially on the Reason Foundation's R model of the Florida Retirement System, generalized for more plans, and optimized to reduce looping through classes.

## Requirements

- [Python 3.11+](https://www.python.org/downloads/)
- Git

## Installation

```bash
git clone https://github.com/donboyd5/pension_model.git
cd pension_model
python -m venv .venv
```

Activate the virtual environment:

- **Linux / macOS:** `source .venv/bin/activate`
- **Windows (Command Prompt):** `.venv\Scripts\activate`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

Then install:

```bash
pip install -e .
```

You must activate the virtual environment each time you open a new terminal. You'll know it's active when your prompt shows `(.venv)`.

## Running the model

```bash
python scripts/run_model.py                # run the model and validate against baseline
python scripts/run_model.py --no-test      # model + validation only, skip unit tests
python scripts/run_model.py --test-only    # unit tests only
```
