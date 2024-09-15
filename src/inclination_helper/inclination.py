import os
import json
import time
from pathlib import Path
from src.config import Settings
from python_ms_core import Core
from urllib.parse import urlparse
from shapely.geometry import shape
from src.inclination_helper.osm_graph import OSMGraph
from src.inclination_helper.dem_processor import DEMProcessor
from src.inclination_helper.dem_downloader import DEMDownloader
from src.inclination_helper.utils import get_unique_id, unzip, create_zip

from src.logger import Logger


class Inclination:
    _config = Settings()

    def __init__(self, file_path=None, storage_client=None, prefix=None):
        self.core = Core()
        if storage_client:
            self.storage_client = storage_client
        else:
            self.storage_client = self.core.get_storage_client()
        self.container_name = self._config.event_bus.container_name
        self.download_dir = self._config.get_download_directory()
        is_exists = os.path.exists(self.download_dir)
        self.file_path = file_path
        # self.file_path = 'https://tdeisamplestorage.blob.core.windows.net/tdei-storage-test/geojson_renton_hth.zip'
        self.prefix = get_unique_id() if not prefix else prefix
        parsed_url = urlparse(self.file_path)
        file_name = parsed_url.path.split('/')[-1]
        base_name, extension = os.path.splitext(file_name)
        self.updated_file_name = f'{base_name}_added_inclination{extension}'
        self.root_path = os.path.join(os.getcwd(), 'src')
        if not is_exists:
            os.makedirs(self.download_dir)

    def calculate(self):
        downloaded_file_path = self.download_file(self.file_path)
        unzip_files, all_files = unzip(zip_file=downloaded_file_path, output=os.path.join(self.download_dir, self.prefix))
        with open(f'{self.root_path}/ned_13_index.json') as f:
            ned_13_index = json.load(f)['tiles']
        dem_downloader = DEMDownloader(ned_13_index=ned_13_index, workdir=self.download_dir)
        graph_nodes_path = Path(unzip_files['nodes'])
        graph_edges_path = Path(unzip_files['edges'])

        with open(graph_edges_path, 'r') as edge_file:
            EDGE_FILE = json.load(edge_file)

        Logger.info(f'No of edges: {len(EDGE_FILE["features"])} to be processed')
        for feature in EDGE_FILE['features']:
            dem_downloader.get_ned13_for_bounds(bounds=shape(feature['geometry']).bounds)

        osm_graph = OSMGraph.from_geojson(
            nodes_path=graph_nodes_path,
            edges_path=graph_edges_path
        )

        tile_sets = dem_downloader.list_ned13s()

        start_time = time.time()
        dem_processor = DEMProcessor(osm_graph=osm_graph, tile_sets=tile_sets, workdir=self.download_dir)
        dem_processor.process(
            nodes_path=graph_nodes_path,
            edges_path=graph_edges_path
        )

        end_time = time.time()
        time_taken = end_time - start_time
        Logger.info(f'Entire processing took: {time_taken} seconds')

        zip_file_path = create_zip(files=all_files, zip_file_path=os.path.join(self.download_dir, f'{self.prefix}/{self.updated_file_name}'))
        return zip_file_path

    def download_file(self, file_path: str) -> str:
        file = self.storage_client.get_file_from_url(container_name=self.container_name, full_url=file_path)
        try:
            if file.file_path:
                file_path = os.path.basename(file.file_path)
                unique_directory = os.path.join(self.download_dir, self.prefix)
                if not os.path.exists(unique_directory):
                    os.makedirs(unique_directory)
                local_download_path = os.path.join(unique_directory, file_path)
                with open(local_download_path, 'wb') as blob:
                    blob.write(file.get_stream())
                return local_download_path
            else:
                raise Exception('File not found')
        except Exception as err:
            raise err
