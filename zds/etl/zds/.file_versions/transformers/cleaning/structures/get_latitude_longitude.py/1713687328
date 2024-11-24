from pandas import DataFrame
import requests
import time
import numpy as np
import pandas as pd

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def get_latitude_longitude(df: DataFrame, *args, **kwargs) -> DataFrame:
    """
    Get latitude and longitude associated to structures adresses using open data api
    """
    ADDOK_URL = "http://api-adresse.data.gouv.fr/search/"

    columns_df = df.columns

    def get_latitude_longitude_based_on_address(address):
        dict_resolv = {
            "Les Deuxièmes Borrels, Hyères, Toulon, Var, Provence-Alpes-Côte d'Azur, France métropolitaine, 83400, France": "Les Deuxièmes Borrels, Hyères, Toulon",
            "34, Rue de la Justice, Quartier Saint-Fargeau, Paris 20e Arrondissement, Paris, Île-de-France, France métropolitaine, 75020, France": "34, Rue de la Justice, Quartier Saint-Fargeau, Paris 20e Arrondissement",
            "Avenue du Palais de la Mer, Port Camargue, Le Grau-du-Roi, Nîmes, Gard, Occitanie, France métropolitaine, 30240, France": "Avenue du Palais de la Mer, Port Camargue, Le Grau-du-Roi",
            "37, Avenue de la Ferrière, Le Petit Chantilly, Le Bois Saint-Louis, Plaisance, Orvault, Nantes, Loire-Atlantique, Pays de la Loire, France métropolitaine, 44700, France": "37, Avenue de la Ferrière, Orvault",
            "Avenue du Palais de la Mer, Port Camargue, Le Grau-du-Roi, Nîmes, Gard, Occitanie, France métropolitaine, 30240, France": "Avenue du Palais de la Mer, Port Camargue, Le Grau-du-Roi",
            "Quadro, 181, Place Ernest Granier, Port Marianne, Montpellier, Hérault, Occitanie, France métropolitaine, 34000, France": "181, Place Ernest Granier, Port Marianne, Montpellier",
            "La Seyne-sur-Mer, Toulon, Var, Provence-Alpes-Côte d'Azur, France métropolitaine, 83500, France": "La Seyne-sur-Mer, Toulon",
            "Boulevard Émile Loubet, Fuveau, Aix-en-Provence, Bouches-du-Rhône, Provence-Alpes-Côte d'Azur, France métropolitaine, 13710, France": "Boulevard Émile Loubet, Fuveau, Aix-en-Provence",
            "Place Claude Pinoteau, La Bonne Eau, Le Praz, Valloire, Saint-Jean-de-Maurienne, Savoie, Auvergne-Rhône-Alpes, France métropolitaine, 73450, France": "Place Claude Pinoteau, Valloire",
            "Rue Dumont d'Urville, Technopôle Pointe du Diable, Technopôle Brest Iroise, Plouzané, Brest, Finistère, Bretagne, France métropolitaine, 29280, France": "525 Av. Alexis de Rochon, 29280 Plouzané",
            "Boulevard de la Liberté, Jean-Macé, Jean-Macé - Chantenay, Bellevue - Chantenay - Sainte-Anne, Nantes, Loire-Atlantique, Pays de la Loire, France métropolitaine, 44100, France": "Boulevard de la Liberté,  Nantes, 44100",
        }

        if address in dict_resolv.keys():
            address_search = dict_resolv[address]
        else:
            address_search = address
        params = {"q": address_search, "limit": 5}
        response = requests.get(ADDOK_URL, params=params)
        j = response.json()
        if len(j.get("features")) > 0:
            first_result = j.get("features")[0]
            lon, lat = first_result.get("geometry").get("coordinates")
            # api limit is 50 call per second, we add time sleep to ensure not to hit the limit
            time.sleep(1 / 50)
            return lon, lat
        else:
            print(f"No result for address : {address}")
            return np.NaN, np.NaN

    df["longitude_latitude"] = df["ADRESSE"].apply(
        lambda x: get_latitude_longitude_based_on_address(x)
    )
    df[["longitude", "latitude"]] = df["longitude_latitude"].apply(pd.Series)

    cols_final = list(columns_df) + ["longitude", "latitude"]
    return df[cols_final]


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
    assert "latitude" in list(output.columns), "latitude columns is missing"
    assert "longitude" in list(output.columns), "longitude columns is missing"
