VENV_DIR = .venv
ACTIVATE_VENV := . $(VENV_DIR)/bin/activate

$(VENV_DIR):
	python3 -m venv $(VENV_DIR)
	$(ACTIVATE_VENV) && pip install --upgrade pip
	$(ACTIVATE_VENV) && pip install --requirement requirements.txt

install: $(VENV_DIR)

# Run black formatter
black: $(VENV_DIR)
	$(ACTIVATE_VENV) && black .

# Run ruff linter
ruff: $(VENV_DIR)
	$(ACTIVATE_VENV) && ruff check .

# Run pytest
pytest: $(VENV_DIR)
	$(ACTIVATE_VENV) && PYTHONPATH=. pytest

# Run all tests (includes black, ruff, and pytest)
test: black ruff pytest