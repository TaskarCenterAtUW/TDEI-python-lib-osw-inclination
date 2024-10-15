import gc
import time
from typing import List
from pathlib import Path
from .logger import Logger
from .osm_graph import OSMGraph
from .version import __version__
from .dem_processor import DEMProcessor


class OSWIncline:
    def __init__(self, dem_files: List[str], nodes_file: str, edges_file: str, debug=False):
        self.dem_files = dem_files
        self.nodes_file = nodes_file
        self.edges_file = edges_file
        self.debug = debug
        if self.debug:
            Logger.debug('Debug mode is enabled')

    def calculate(self, skip_existing_tags=False, batch_processing=False):
        try:
            if self.debug:
                Logger.debug('Starting calculation process')
            graph_nodes_path = Path(self.nodes_file)
            graph_edges_path = Path(self.edges_file)

            osm_graph = OSMGraph.from_geojson(
                nodes_path=graph_nodes_path,
                edges_path=graph_edges_path
            )

            start_time = time.time()
            dem_processor = DEMProcessor(osm_graph=osm_graph, dem_files=self.dem_files, debug=self.debug)
            dem_processor.process(
                nodes_path=graph_nodes_path,
                edges_path=graph_edges_path,
                skip_existing_tags=skip_existing_tags,
                batch_processing=batch_processing
            )

            # Delete osm_graph and dem_processor to force garbage collection
            osm_graph.clean()
            del osm_graph, dem_processor
            gc.collect()

            end_time = time.time()
            time_taken = end_time - start_time
            if self.debug:
                Logger.info(f'Entire processing took: {time_taken} seconds')
            return True
        except Exception as e:
            if self.debug:
                Logger.error(f'Error processing DEM files: {e}')
            raise Exception(f'Error processing DEM files: {e}')
        finally:
            gc.collect()


OSWIncline.__version__ = __version__
