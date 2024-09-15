import time
import math
import requests
from pathlib import Path
from src.logger import Logger


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

        start_time = time.time()
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        end_time = time.time()
        Logger.info(f'DEM file downloading took: {end_time - start_time} seconds')

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
                    Logger.warning(f'Tile not found {tile}')
                    # FIXME Outside range - issue warning? Log?
                    pass

        # Check temporary dir for these tiles
        cached_tiles = self.list_ned13s()

        # TODO: use set operations so that the code is easier to understand
        fetch_tiles = [tile for tile in self.ned_13_tiles if tile not in cached_tiles]

        # FIXME: should split this function into two steps:
        # 1) Figure out which are missing, return these tileset names.
        # 2) CLI / GUI will display this info
        # 3) Downstream code will accept a list of these names as input for
        # fetching. Can happen async, etc.
        if fetch_tiles:
            Logger.info(f"Fetching DEM data for {fetch_tiles}...")
        # else:
        #     print("No tiles need to be fetched.")

        # Any remaining tiles must be fetched and inserted into the database
        # TODO: make this fully async, use a queue to fetch and insert via separate
        # tasks
        for tile_name in fetch_tiles:
            self.fetch_ned_tile(tile_name=tile_name)

    def list_ned13s(self):
        dem_dir = self.get_dem_dir()
        return [Path(tif).stem for tif in dem_dir.glob('*.tif') if Path(tif).stem in self.ned_13_index]
