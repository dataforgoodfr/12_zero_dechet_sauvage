if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """remove useless columns"""
    data = data.drop(columns=["geometry", "distance"])
    data.rename(
        columns={
            "NOM_right": "COMMUNE",
            "NOM_left": "NOM_structure",
            "region_1": "region",
        },
        inplace=True,
    )
    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"