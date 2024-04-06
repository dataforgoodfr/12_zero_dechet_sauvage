if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, data_2, data_3, data_4, *args, **kwargs):
    """Merge every table
    data -- table appartenance
    data_2 -- epci
    data_3 -- departements
    data_4 -- regions
    """

    # Merge epci
    data = data.merge(data_2, how="left", on="EPCI")
    # Merge departements
    data = data.merge(data_3, how="left", on="DEP")
    # Merge regions
    data = data.merge(data_4, how="left", on="REG")

    return data


@test
def test_output(output, *args) -> None:
    """-"""
    assert output is not None, "The output is undefined"
