if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """GET lines other than 'MARQUE and equal to 0'"""

    data = data.loc[(data.TYPE_REGROUPEMENT != "MARQUE") & (data.NB_DECHET != 0)]

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
