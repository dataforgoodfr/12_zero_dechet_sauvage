import io
import os
import pandas as pd
import requests
import zipfile

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_api(data, *args, **kwargs):
    """Get <data> from <data_provider>"""

    # url = (
    #     "<url_from_data_provider>"
    # )
    year = data["year"][2:]

    return pd.read_excel(
        f"/home/merterre/zds/inputs/table-appartenance-geo-communes-{year}.xlsx",
        sheet_name="COM",
        skiprows=5,
    )


@test
def test_file_is_still_in_directory(output, *args) -> None:
    """-"""
    assert output is not None
