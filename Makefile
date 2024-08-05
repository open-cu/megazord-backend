.PHONY: format  ## Auto-format python source files
format:
	ruff check --fix
	ruff format

.PHONY: lint  ## Lint python source files
lint:
	ruff check
	ruff format --check