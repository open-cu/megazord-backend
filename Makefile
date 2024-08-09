FILES = $(filter-out $@,$(MAKECMDGOALS))

.PHONY: format ## Auto-format python source files
format:
	ruff format $(FILES)
	ruff check --fix $(FILES)

.PHONY: lint ## Lint python source files
lint:
	ruff check $(FILES)
	ruff format --check $(FILES)

.PHONY: local_postgres
local_postgres:
	docker run --name my-postgres -e POSTGRES_DB=megazord -e POSTGRES_USER=megazord_user -e POSTGRES_PASSWORD=megazord_super_user -p 5432:5432 -d postgres:16

.PHONY: run_django
run_django:
	docker build -t megazord-app .
	docker run -p 8000:8000 --name megazord-app --link my-postgres:postgres megazord-app

%:
	@:
