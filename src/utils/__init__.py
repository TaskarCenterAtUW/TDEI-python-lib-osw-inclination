import shutil
import zipfile
import requests
from pathlib import Path

DOWNLOAD_DIR = Path(f'{Path.cwd()}/downloads')
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
DEM_DIR = Path(DOWNLOAD_DIR, 'dems')
DEM_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = Path(f'{Path.cwd()}/tests/assets')


def download_dems():
    dem_file = 'n48w123.tif'
    file_path = Path(f'{DEM_DIR}/{dem_file}')

    # Download DEM file if not present
    if not file_path.is_file():
        URL = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n48w123/USGS_13_n48w123.tif'
        with requests.get(URL, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)


def unzip_dataset():
    zip_path = Path(f'{ASSETS_DIR}/medium.zip')
    extract_to = Path(f'{ASSETS_DIR}/medium')

    # Unzip medium.zip to the specified extraction path
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def remove_unzip_dataset():
    extract_to = Path(f'{ASSETS_DIR}/medium')
    if extract_to.exists():
        shutil.rmtree(extract_to, ignore_errors=True)
