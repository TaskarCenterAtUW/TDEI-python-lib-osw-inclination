import os
from osw_incline import OSWIncline
from utils import download_dems, unzip_dataset, remove_unzip_dataset

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEM_DIR = os.path.join(PARENT_DIR, 'downloads/dems')
ASSETS_DIR = os.path.join(PARENT_DIR, 'tests/assets')


def test_incline():
    dem_files = [f'{DEM_DIR}/n48w123.tif']
    nodes_file = f'{ASSETS_DIR}/medium/wa.seattle.graph.nodes.geojson'
    edges_file = f'{ASSETS_DIR}/medium/wa.seattle.graph.edges.geojson'
    incline = OSWIncline(dem_files=dem_files, nodes_file=nodes_file, edges_file=edges_file, debug=True)
    result = incline.calculate()
    print(result)


if __name__ == '__main__':
    download_dems()
    unzip_dataset()
    test_incline()
    remove_unzip_dataset()
