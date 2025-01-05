if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """
    1 - Drop na on ID_RELEVE
    2 - Filter on France
    """

    # Drop na on ID_RELEVE
    data = data[~data["ID_RELEVE"].isna()]

    # Filter on France
    data = data[data.LIEU_PAYS == "France"]

    return data


@test
def test_country_is_france(output, *args) -> None:
    """Assert that Country is only France"""
    unique_vals = output["LIEU_PAYS"].unique()
    assert unique_vals == ["France"]
