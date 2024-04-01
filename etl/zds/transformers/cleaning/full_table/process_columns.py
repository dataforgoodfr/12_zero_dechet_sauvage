if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, data_2, *args, **kwargs):
    """Keep the original columns + NOM + INSEE"""

    columns_to_keep = list(data_2.columns) + ["NOM", "INSEE_COM"]

    data = data[columns_to_keep]
    data.rename(columns={"NOM": "commune"}, inplace=True)

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
