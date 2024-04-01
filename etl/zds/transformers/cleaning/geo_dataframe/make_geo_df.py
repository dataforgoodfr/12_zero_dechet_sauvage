from shapely.geometry import Point
import geopandas as gpd

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, data_2, *args, **kwargs):
    """Turn cleaned dataframe into a geo dataframe"""

    # Make GPS points
    geometry = [Point(xy) for xy in zip(data.LIEU_COORD_GPS_X, data.LIEU_COORD_GPS_Y)]

    # Attach points to corrected data
    gdf_data_zds = gpd.GeoDataFrame(data, geometry=geometry, crs=data_2.crs)

    return gdf_data_zds


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
