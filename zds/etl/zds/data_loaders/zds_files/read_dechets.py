import json

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_file(*args, **kwargs):
    """Read dechet.json

    It contains data about optional trash counts
    """

    filepath = "/home/merterre/zds/inputs/dechets.json"

    with open(filepath, "r") as f:
        content = f.read()

    return json.loads(content)


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
