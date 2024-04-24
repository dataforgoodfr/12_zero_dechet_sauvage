if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def execute_transformer_action(df, *args, **kwargs) -> None:
    """Filtering table to get communes which are not too far from geo point
    to avoid attributing foreign geopoints to french communes"""
    df = df.loc[df["distance"] < 0.1, :]

    return df


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
    assert len(output) > 0, "Te output doesn't have any rows left"
