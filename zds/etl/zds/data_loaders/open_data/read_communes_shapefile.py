import geopandas as gpd
import logging

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data(*args, **kwargs):
    """Read the Shapefile that contains cities data"""

    logging.getLogger("fiona").setLevel(logging.ERROR)

    shapefile_path = "/home/merterre/open_data/COMMUNE.shp"

    # Importer le fichier Shapefile
    gdf = gpd.read_file(shapefile_path, driver="ESRI Shapefile")

    # Convertir en format WGS 84 (EPSG:4326)
    gdf_wgs84 = gdf.to_crs(epsg=4326)

    return gdf_wgs84


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
