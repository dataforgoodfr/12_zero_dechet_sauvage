import geopandas as gpd

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, data_2, *args, **kwargs):
    """Join every data to make a new table"""

    full_table = gpd.sjoin_nearest(data, data_2, distance_col="distance", how="left")

    return full_table


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"