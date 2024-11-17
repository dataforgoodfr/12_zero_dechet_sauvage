import numpy as np

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, data_2, *args, **kwargs):
    """Rename trash lvl 3 columns

    data -- ouput lvl 2
    data_2 -- trash file
    """

    # Use lvl 3
    lvl = 3
    mandatory3 = data_2["dechets_oblig_niveau_3"]

    # Extracte every NB_DECHET_GROUPE_ column name
    cols_nb_dechet_groupe = [
        c.replace("NB_DECHET_GROUPE_", "")
        for c in data.columns
        if "NB_DECHET_GROUPE_" in c
    ]

    optional3 = [
        "NB_DECHET_GROUPE_" + c for c in cols_nb_dechet_groupe if c not in mandatory3
    ]

    for c in optional3:
        data.loc[data.NIVEAU_CARAC == 3, c] = data.loc[data.NIVEAU_CARAC == 3, c].apply(
            lambda x: np.nan if x == 0 else x
        )

    return data


@test
def test_output(output, *args) -> None:
    """TO DO : maybe check that there are Nas in NIVEAU_CARAC == 3"""

    assert output is not None, "The output is undefined"
