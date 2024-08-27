import pytest
from _pytest.fixtures import FixtureRequest
from environ import Env
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres(request: FixtureRequest) -> PostgresContainer:
    postgres_container = PostgresContainer("postgres:16").start()

    def remove_container():
        postgres_container.stop()

    request.addfinalizer(remove_container)

    return postgres_container


@pytest.fixture(scope="session")
def django_db_modify_db_settings(postgres: PostgresContainer) -> None:
    from django.conf import settings
    from django.db import connections

    # remove cached_property of connections.settings from the cache
    del connections.__dict__["settings"]

    # define settings to override during this fixture
    settings.DATABASES = {
        "default": Env.db_url_config(postgres.get_connection_url(driver=None))
    }

    # re-configure the settings given the changed database config
    connections._settings = connections.configure_settings(settings.DATABASES)

    # open a connection to the database with the new database config
    # here the database is called 'default', but one can modify it to whatever fits their needs
    connections["default"] = connections.create_connection("default")
