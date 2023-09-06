.PHONY: test precommit_init lint lint_ci clean


POETRY = poetry run

test:
	${POETRY} pytest -s ${ARGS}

precommit_init:
	${POETRY} pre-commit install

lint:
	${POETRY} black .
	${POETRY} ruff . --fix

lint_ci:
	${POETRY} black . --check -v
	${POETRY} ruff .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -exec rm -f {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
