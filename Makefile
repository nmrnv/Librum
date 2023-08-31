.PHONY: test lint lint_ci precommit_init

POETRY = poetry run

test:
	${POETRY} pytest -s .

precommit_init:
	${POETRY} pre-commit install

lint:
	${POETRY} black .
	${POETRY} ruff . --fix

lint_ci:
	${POETRY} black . --check -v
	${POETRY} ruff .

clean:
	@echo "Cleaning caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -exec rm -f {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "Caches cleaned."
