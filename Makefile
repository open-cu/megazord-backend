FILES = $(filter-out $@,$(MAKECMDGOALS))

.PHONY: format ## Auto-format python source files
format:
	ruff format $(FILES)
	ruff check --fix $(FILES)

.PHONY: lint ## Lint python source files
lint:
	ruff check $(FILES)
	ruff format --check $(FILES)

%:
	@:
