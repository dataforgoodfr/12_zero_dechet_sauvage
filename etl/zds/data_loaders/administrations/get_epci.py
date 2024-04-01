import io
import os
import pandas as pd
import requests
import zipfile

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_api(*args, **kwargs):
    """Get EPCI from INSEE"""

    year = "2023"
    path_epci = (
        f"/home/merterre/open_data/Intercommunalite_Metropole_au_01-01-{year}.xlsx"
    )

    # Bypass download
    if os.path.exists(path_epci):
        return pd.read_excel(path_epci, sheet_name="EPCI", skiprows=5)

    url = (
        "https://www.insee.fr/fr/statistiques/fichier/"
        f"2510634/Intercommunalite_Metropole_au_01-01-{year}.zip"
    )
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("/home/merterre/open_data")

    return pd.read_excel(path_epci, sheet_name="EPCI", skiprows=5)


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
