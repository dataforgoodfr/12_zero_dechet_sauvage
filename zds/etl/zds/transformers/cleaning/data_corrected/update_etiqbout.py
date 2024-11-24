import numpy as np

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """Update étiquette bouteille

    Reason : column did not exist before v2
    """

    data["NB_DECHET_GROUPE_ETIQUETTES DE BOUTEILLE"] = np.where(
        (data["NB_DECHET_GROUPE_ETIQUETTES DE BOUTEILLE"] == 0)
        & (data["VERSION_PROTOCOLE"] == 1),
        np.nan,
        data["NB_DECHET_GROUPE_ETIQUETTES DE BOUTEILLE"],
    )

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
