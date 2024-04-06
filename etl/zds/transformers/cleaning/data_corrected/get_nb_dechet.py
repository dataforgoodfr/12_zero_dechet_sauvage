if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """Get NB_DECHET columns from data"""

    data_nb_dechet = data[
        ["ID_RELEVE", "NIVEAU_CARAC"] + [c for c in data.columns if "NB_DECHET_" in c]
    ]

    return data_nb_dechet


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
