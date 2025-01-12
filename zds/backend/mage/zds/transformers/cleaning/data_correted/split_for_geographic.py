if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """Split the data
    Used to prevent the dateime loading issue at the Geodataframe creaction
    """

    cols = [c for c in data.columns if 'NB_DECHET_' not in c]

    data = data[cols]

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
