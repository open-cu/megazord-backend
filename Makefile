TEST           = pytest $(arg)
DC	           = docker compose
ENV			   = --env-file .env
CODE 	       = src tests

.PHONY: build
build:
	$(DC) build

.PHONY: up
up:
	$(DC) $(ENV) up -d
	$(DC) $(ENV) exec -it backend python src/manage.py migrate

.PHONY: up-prod
up-prod:
	$(DC) $(ENV) -f compose.yaml -f compose.prod.yaml up -d
	$(DC) $(ENV) exec backend python src/manage.py migrate

.PHONY: down
down:
	$(DC) down --volumes

.PHONY: logs
logs:
	$(DC) logs -f

.PHONY install:
install:
	pip install -r requirements.txt -r requirements.tests.txt

.PHONY: format ## Auto-format python source files
format:
	ruff format $(CODE)
	ruff check --fix $(CODE)

.PHONY: lint ## Lint python source files
lint:
	ruff check $(CODE)
	ruff format --check $(CODE)

.PHONY: test-unit
test-unit:
	$(TEST) tests/unit --cov=./ --cov-append

.PHONY: test-integration
test-integration:
	$(TEST) tests/integration --cov=./ --cov-append

.PHONY: test-e2e
test-e2e:
	$(TEST) tests/e2e --cov=./ --cov-append

.PHONY: test
test: test-unit test-integration test-e2e

.PHONY: report
report:
	$(TEST) unit integration e2e --cov=./ --cov-report html
