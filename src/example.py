import os

from osw_incline import OSWIncline


PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PARENT_DIR, 'tests/assets')


def test_incline():
    dem_files = [f'{ASSETS_DIR}/dems/n48w123.tif']
    nodes_file = f'{ASSETS_DIR}/medium/wa.seattle.graph.nodes.geojson'
    edges_file = f'{ASSETS_DIR}/medium/wa.seattle.graph.edges.geojson'
    incline = OSWIncline(dem_files=dem_files, nodes_file=nodes_file, edges_file=edges_file, debug=True)
    result = incline.calculate()
    print(result)




if __name__ == '__main__':
    test_incline()

