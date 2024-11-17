if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """Split the data
    Used to prevent the dateime loading issue at the Geodataframe creaction
    """

    geo_cols = ["LIEU_PAYS", "LIEU_COORD_GPS_X", "LIEU_COORD_GPS_Y"]
    cols = [c for c in list(data.columns) if c not in geo_cols]

    data = data[cols]

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
