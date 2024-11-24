import pandas as pd

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_excel_file(*args, **kwargs):
    """Read the Zero Dechet Sauvage dataset Corrected by MerTerre"""
    dataset_path = "/home/merterre/zds/inputs/export_structures_29022024 (1).xlsx"
    df = pd.read_excel(dataset_path)

    return df


@test
def test_output(output, *args) -> None:
    """-"""
    assert output is not None, "The output is undefined"
