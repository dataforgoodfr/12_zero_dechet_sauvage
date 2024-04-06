if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """Clean category values"""

    def clean_category(category):
        prefix = [
            "NB_DECHET_GROUPE_",
            "NB_DECHET_DCSMM_GENERIQUE_",
            "NB_DECHET_DCSMM_SPECIFIQUE_",
            "NB_DECHET_DCSMM_",
            "NB_DECHET_MARQUE_",
            "NB_DECHET_REP_",
            "NB_DECHET_SECTEUR_",
        ]
        for p in prefix:
            category = category.replace(p, "")
        return category

    data["CATEGORY"] = data["variable"].apply(clean_category)

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
