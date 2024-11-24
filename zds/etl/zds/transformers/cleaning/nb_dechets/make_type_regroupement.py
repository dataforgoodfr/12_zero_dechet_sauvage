import re

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, data_2, *args, **kwargs):
    """Make types de regroupement

    data -- nb_dechet table from melting
    data_2 -- trash file
    """

    regroupements = data_2["types_regroupement"]

    def get_regroupement(val, rgps=regroupements) -> str:
        elems = [re.sub(r"^_|_$", "", elem) for elem in rgps if elem in val]
        rgp = "-".join(elems)
        return rgp

    data["TYPE_REGROUPEMENT"] = data["variable"].apply(get_regroupement)

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
