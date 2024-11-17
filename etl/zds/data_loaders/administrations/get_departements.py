import pandas as pd

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_region(data, *args, **kwargs):
    """Get <data> from <data_provider>"""

    year = data["year"]

    url = (
        f"https://www.insee.fr/fr/statistiques/fichier/6800675/v_departement_{year}.csv"
    )

    return pd.read_csv(url)


@test
def test_file_is_still_in_directory(output, *args) -> None:
    """-"""
    assert output is not None
