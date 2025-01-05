import pandas as pd

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """Melt table and drop Nas"""

    data_melt = pd.melt(
        data,
        id_vars=["ID_RELEVE", "NIVEAU_CARAC"],
        value_vars=[c for c in data.columns if "NB_DECHET_" in c],
        value_name="NB_DECHET",
    )
    data_melt = data_melt[~data_melt.NB_DECHET.isna()]

    return data_melt


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
