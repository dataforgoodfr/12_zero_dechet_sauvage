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
def load_data_from_api(*args, **kwargs):
    """Get DATA from <data_provider>"""

    path_DATA = "<path_to_data>"

    # Bypass download
    if os.path.exists(path_DATA):
        return pd.read_csv(path_DATA)

    url = "<url_from_data_provider>"
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("<path_target_folder_for_extraction>")

    return pd.read_csv(path_DATA)


@test
def test_file_is_still_in_directory(output, *args) -> None:
    """Check that the downloaded file is still here"""
    assert os.path.exists(path_DATA)
