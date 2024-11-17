import numpy as np

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """Update DCSMM columns

    Reason : columns exist for lvl 4 ONLY
    """

    cols_dcsmm = [
        c
        for c in data.columns
        if "NB_DECHET_DCSMM_" in c and "GENERIQUE" not in c and "SPECIFIQUE" not in c
    ]

    for c in cols_dcsmm:
        data[c] = np.where((data[c] == 0) & (data["NIVEAU_CARAC"] < 4), np.nan, data[c])

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
