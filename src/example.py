import os

from jinja2.ext import debug

from osw_incline import OSWIncline


PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = os.path.join(PARENT_DIR, 'downloads')


def test_incline():
    dem_files = [f'{DOWNLOADS_DIR}/dems/n48w123.tif']
    nodes_file = f'{DOWNLOADS_DIR}/geojson_renton_hth/renton_hth.nodes.geojson'
    edges_file = f'{DOWNLOADS_DIR}/geojson_renton_hth/renton_hth.edges.geojson'
    incline = OSWIncline(dem_files=dem_files, nodes_file=nodes_file, edges_file=edges_file, debug=True)
    result = incline.calculate()
    print(result)




if __name__ == '__main__':
    test_incline()

