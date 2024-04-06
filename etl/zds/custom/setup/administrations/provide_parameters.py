import datetime

if "custom" not in globals():
    from mage_ai.data_preparation.decorators import custom
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@custom
def transform_custom(*args, **kwargs):
    """Send the data used to configure the other blocks"""

    # Get current year
    currentDateTime = datetime.datetime.now()
    date = currentDateTime.date()
    year = date.strftime("%Y")
    previous_year = str(int(year) - 1)

    return {"year": previous_year}


@test
def test_year_is_string(output, *args) -> None:
    """Year must be a string"""
    assert isinstance(output["year"], str)
