if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """GET lines other than

    'REP and is equal to 0 and NIVEAU_CARAC less than 4'
    """

    data = data.loc[
        ~(
            (data.NB_DECHET == 0)
            & (data.TYPE_REGROUPEMENT == "REP")
            & (data.NIVEAU_CARAC < 4)
        )
    ]

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
