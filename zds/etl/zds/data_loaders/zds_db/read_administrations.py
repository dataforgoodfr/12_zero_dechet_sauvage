from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.mysql import MySQL
from os import path

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_mysql(*args, **kwargs):
    """Load administrations from the db"""
    query = "SELECT * FROM administrations"
    config_path = path.join(get_repo_path(), "io_config.yaml")
    config_profile = "default"

    with MySQL.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
        return loader.load(query)


@test
def test_output(output, *args) -> None:
    """-"""
    assert output is not None, "The output is undefined"
