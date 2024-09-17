from networkx import nodes

# OSW-Incline Package
OSW-Incline is a Python library for calculating the incline of geographical features based on Digital Elevation Models (DEM) and OpenStreetMap (OSM) data. The library processes DEM files and calculates inclines for each edge in a provided OSM graph (GeoJSON format).

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Running Tests](#running-tests)
- [How To Get DEM Files From NED Database](#how-to-get-dem-files-from-ned-database)
- [License](#license)

## Features 

- **DEM Processing**: Reads DEM files and uses various interpolation methods (`IDW`, `Bilinear`, and `Spline`) to infer elevations.
- **OSM Graph Support**: Supports importing nodes and edges from OSM GeoJSON files.
- **Incline Calculation**: Computes the incline of paths between nodes based on elevation differences.
- **Debug Mode**: Detailed logging is available for debugging purposes.

## Installation

- Add `osw-incline` package as dependency in your `requirements.txt`  
- or `pip install osw-incline`  
- Start using this package in your code.  


## Usage

### Basic Example

```python
from osw_incline import OSWIncline

# Define the DEM files and GeoJSON files for nodes and edges
dem_files = ['dem_file1.tif', 'dem_file2.tif']
nodes_file = 'nodes.geojson'
edges_file = 'edges.geojson'

osw_incline = OSWIncline(
    dem_files=dem_files, 
    nodes_file=nodes_file, 
    edges_file=edges_file, 
    debug=True # If debug is need
)

# Perform the incline calculation, it will add the incline to the  original edges file 
result = osw_incline.calculate()

if result:
    print("Incline calculation completed successfully.")
```

## API Reference

### OSWIncline

`__init__(dem_files: List[str], nodes_file: str, edges_file: str, debug: bool = False)`

- **dem_files:** List of DEM files to be used for elevation interpolation.
- **nodes_file:** Path to the GeoJSON file containing nodes.
- **edges_file:** Path to the GeoJSON file containing edges.
- **debug:** Enable debug mode for detailed logging.

`calculate() -> bool`

- Perform the incline calculation and update the edges file with incline values.
- Returns `True` if the calculation is successful, raises an exception on failure.

### DEMProcessor

`process(nodes_path: Path, edges_path: Path)`

- Processes the DEM files and updates the OSM graph with incline data.

## Examples

You can run the calculation with real data by passing your DEM files and GeoJSON data:
```python
osw_incline = OSWIncline(
    dem_files=['path/to/dem1.tif', 'path/to/dem2.tif'], 
    nodes_file='nodes_file_path.geojson', 
    edges_file='edges_file_path.geojson', 
    debug=True # If debug is need
)
osw_incline.calculate()
```

## Running Tests
OSW-Incline includes a suite of unit tests to ensure correct functionality. You can run the tests with the following command:
```bash
# To run the unit test cases
python -m unittest discover -v tests

# To run the unit test cases with coverage
python -m coverage run --source=src -m unittest discover -v tests

# To generate the coverage report
python -m coverage report

# To generate the coverage report in html format
python -m coverage html
```
Make sure that all tests pass before making any changes.

## How To Get DEM Files From NED Database

### Example

You can download DEM files from the National Elevation Dataset (NED) database. Here are the steps to download DEM files:

#### Step 1: Prepare files to download DEM files
```bash
```python
import json
from shapely.geometry import shape
from dem_downloader import DEMDownloader

graph_nodes_path = 'nodes_file_path.geojson'
graph_edges_path = 'edges_file_path.geojson'
with open('ned_13_index.json') as f:
        ned_13_index = json.load(f)['tiles']

dem_downloader = DEMDownloader(ned_13_index=ned_13_index, workdir='Directory Path where you want to download the DEM files')

with open(graph_edges_path, 'r') as edge_file:
    EDGE_FILE = json.load(edge_file)
    
for feature in EDGE_FILE['features']:
    dem_downloader.get_ned13_for_bounds(bounds=shape(feature['geometry']).bounds)
```
#### Step 2: Create a DEMDownloader class to download
```python
import math
import requests
from pathlib import Path


class DEMDownloader:
    TEMPLATE = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/{e}/USGS_13_{e}.tif'

    def __init__(self, ned_13_index, workdir):
        self.ned_13_tiles = []
        self.workdir = workdir
        self.ned_13_index = ned_13_index


    def get_dem_dir(self):
        dem_path = Path(self.workdir, 'dems')
        dem_path.mkdir(exist_ok=True)
        return dem_path

    def fetch_ned_tile(self, tile_name):
        if tile_name not in self.ned_13_index:
            raise ValueError(f'Invalid tile name {tile_name}')

        url = self.TEMPLATE.format(e=tile_name)
        filename = f'{tile_name}.tif'
        dem_dir = self.get_dem_dir()
        path = Path(dem_dir, filename)

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        

    def get_ned13_for_bounds(self, bounds):
        north_min = int(math.floor(bounds[1]))
        north_max = int(math.ceil(bounds[3]))
        west_min = int(math.floor(-1 * bounds[2]))
        west_max = int(math.ceil(-1 * bounds[0]))

        for n in range(north_min + 1, north_max + 1):
            # Added 1 to ranges because we need the top corner value whereas
            # range() defaults to lower
            for w in range(west_min + 1, west_max + 1):
                tile = f"n{n}w{w:03}"
                if tile in self.ned_13_index:
                    self.ned_13_tiles.append(tile)
                else:
                    pass

        # Check temporary dir for these tiles
        cached_tiles = self.list_ned13s()

        fetch_tiles = [tile for tile in self.ned_13_tiles if tile not in cached_tiles]

        for tile_name in fetch_tiles:
            self.fetch_ned_tile(tile_name=tile_name)

    def list_ned13s(self):
        dem_dir = self.get_dem_dir()
        return [Path(tif).stem for tif in dem_dir.glob('*.tif') if Path(tif).stem in self.ned_13_index]
```
**NOTE:** `ned_13_index.json` file contains the index of all the DEM files available in the NED database. You can download the DEM files by providing the tile name can be found [here](https://github.com/TaskarCenterAtUW/TDEI-python-lib-osw-inclination/blob/main/ned_13_index.json)

## License
This project is licensed under the MIT License. See the [LICENSE](https://github.com/TaskarCenterAtUW/TDEI-python-lib-osw-inclination/blob/main/LICENSE) file for details