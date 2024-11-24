if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """
    Keep only usefull columns on commune shapefile file
    """
    # Specify your transformation logic here

    data = data.drop(
        columns=[
            "NOM_M",
            "STATUT",
            "POPULATION",
            "INSEE_CAN",
            "INSEE_ARR",
            "INSEE_DEP",
            "INSEE_REG",
            "SIREN_EPCI",
        ],
    )

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
