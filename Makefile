.PHONY: lint lint-check format test

LINT_PATHS = app tests

lint: format
	ruff check $(LINT_PATHS) --fix

lint-check:
	ruff check $(LINT_PATHS)
	black --check $(LINT_PATHS)
	isort --check-only $(LINT_PATHS)

format:
	black $(LINT_PATHS)
	isort $(LINT_PATHS)

test:
	pytest
