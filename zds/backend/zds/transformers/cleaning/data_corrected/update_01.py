import numpy as np

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """Rename trash lvl 0 and 1 columns

    data -- output lvl 3
    """

    # Use lvl 0 and 1
    lvl = [0, 1]

    # Extracte every NB_DECHET_GROUPE_ column name
    cols_nb_dechet_groupe = [c for c in data.columns if "NB_DECHET_GROUPE_" in c]

    for c in cols_nb_dechet_groupe:
        data.loc[data.NIVEAU_CARAC.isin(lvl), c] = data.loc[
            data.NIVEAU_CARAC.isin(lvl),
            c,
        ].apply(lambda x: np.nan if x == 0 else x)

    return data


@test
def test_output(output, *args) -> None:
    """TO DO : maybe check that there are Nas in NIVEAU_CARAC == 0 and 1"""

    assert output is not None, "The output is undefined"
