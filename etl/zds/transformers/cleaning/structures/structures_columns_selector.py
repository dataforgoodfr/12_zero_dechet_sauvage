from pandas import DataFrame

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def execute_transformer_action(df: DataFrame, *args, **kwargs) -> DataFrame:
    """
    Select only defined columns
    """
    columns_selected = [
        "ID_STRUCT",
        "NOM",
        "SOUS_TYPE",
        "TYPE",
        "ADRESSE",
        "CODE_POSTAL",
        "DEPT",
        "REGION",
        "DATE_INSCRIPTION",
        "ACTION_RAMASSAGE",
        "A1S_NB_SPOTS_ADOPTES",
        "CARACT_ACTIF",
        "CARACT_NB_RELEVES_N1",
        "CARACT_NB_RELEVES_N2",
        "CARACT_NB_RELEVES_N3",
        "CARACT_NB_RELEVES_N4",
    ]
    df = df[columns_selected]
    return df


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
    assert len(output.columns) > 1, "output has more than one column"
