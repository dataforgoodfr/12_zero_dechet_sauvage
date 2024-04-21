from shapely.geometry import Point
import geopandas as gpd

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, data_2, *args, **kwargs):
    """Turn cleaned dataframe into a geo dataframe"""

    if "LIEU_COORD_GPS_X" in data.columns:
        data.rename(columns={"LIEU_COORD_GPS_X": "longitude"}, inplace=True)
    if "LIEU_COORD_GPS_Y" in data.columns:
        data.rename(columns={"LIEU_COORD_GPS_Y": "latitude"}, inplace=True)

    # Make GPS points
    geometry = [Point(xy) for xy in zip(data.latitude, data.longitude)]

    # Attach points to corrected data
    gdf_data_zds = gpd.GeoDataFrame(data, geometry=geometry, crs=data_2.crs)

    return gdf_data_zds


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"