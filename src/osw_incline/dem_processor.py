import gc
import math
import pyproj
import rasterio
import numpy as np
from typing import List
from pathlib import Path
from .logger import Logger
from .osm_graph import OSMGraph
from rasterio.windows import Window
from shapely.geometry import LineString
from scipy.interpolate import RectBivariateSpline


class DEMProcessor:

    def __init__(self, osm_graph: OSMGraph, dem_files: List[str], debug=False):
        wgs84 = pyproj.CRS('EPSG:4326')
        utm = pyproj.CRS('EPSG:32610')
        self.transformer = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True)
        self.dem_files = dem_files
        self.OG = osm_graph
        self.debug = debug

    def process(self, nodes_path, edges_path):
        gc.disable()
        for dem_file in self.dem_files:
            dem_file_path = Path(dem_file)
            if self.debug:
                Logger.debug(f'Processing DEM tile: {dem_file_path}')

            try:
                with rasterio.open(dem_file_path) as dem:
                    edges = list(self.OG.G.edges(data=True))  # Get all edges, even if fewer than batch_size
                    self._process_in_batches(edges, dem, batch_size=1000)

                self.OG.to_geojson(nodes_path, edges_path)
            except rasterio.errors.RasterioIOError:
                if self.debug:
                    Logger.error(f'Failed to open DEM file: {dem_file_path}')
                raise Exception(f'Failed to open DEM file: {dem_file_path}')
            except Exception as e:
                if self.debug:
                    Logger.error(f'Error processing DEM file: {dem_file_path}, error: {e}')
                raise Exception(f'Error processing DEM file: {dem_file_path}, error: {e}')
            finally:
                gc.collect()

        gc.disable()

    def _process_in_batches(self, edges, dem, batch_size=1000):
        # Process edges in batches
        for i in range(0, len(edges), batch_size):
            batch = edges[i:i + batch_size]
            for u, v, d in batch:
                if 'geometry' in d:
                    incline = self.infer_incline(linestring=d['geometry'], dem=dem, precision=3)
                    if incline is not None:
                        d['incline'] = incline
            # Trigger garbage collection after each batch
            gc.collect()

    def infer_incline(self, linestring, dem, precision=3):
        first_point = linestring.coords[0]
        last_point = linestring.coords[-1]

        # Dynamically calculate the length
        length = self.calculate_projected_length(first_point=first_point, last_point=last_point)

        if length == 0:
            return None

        first_elevation = self.dem_interpolate(lon=first_point[0], lat=first_point[1], dem=dem)
        second_elevation = self.dem_interpolate(lon=last_point[0], lat=last_point[1], dem=dem)

        if first_elevation is None or second_elevation is None:
            return None

        elevation_diff = second_elevation - first_elevation

        try:
            incline = elevation_diff / length
            return round(incline, precision)
        except Exception as e:
            if self.debug:
                Logger.error(f'Error calculating incline: {e}')
            return None

    def calculate_projected_length(self, first_point, last_point):
        # Convert the geographic coordinates (lon, lat) to projected (UTM) coordinates
        first_proj = self.transformer.transform(first_point[0], first_point[1])
        last_proj = self.transformer.transform(last_point[0], last_point[1])

        # Calculate the length in meters
        length = LineString([first_proj, last_proj]).length
        return length

    def dem_interpolate(self, lon, lat, dem):
        try:
            # Log the point being interpolated
            interpolated = self.interpolated_value(
                x=lon,
                y=lat,
                dem=dem,
                method='idw',
                scaling_factor=1.0
            )

            if interpolated is not None:
                return interpolated
            else:
                return None
        except Exception as e:
            if self.debug:
                Logger.error(f'Error in DEM interpolation: {e}')
        return None

    def interpolated_value(self, x, y, dem, method='idw', scaling_factor=1.0):
        """Given a point (x, y), find the interpolated value in the raster using
        bilinear interpolation.
        """
        methods = {'spline': self.bivariate_spline, 'bilinear': self.bilinear, 'idw': self.idw}

        # At this point, we assume that the input DEM is in the same crs as the
        # x y values.

        # The DEM's affine transformation: maps units along its indices to crs
        # coordinates. e.g. if the DEM is 1000x1000, maps xy values in the
        # 0-1000 range to the DEM's CRS, e.g. lon-lat
        aff = dem.transform
        # The inverse of the transform: maps values in the DEM's crs to indices.
        # Note: the output values are floats between the index integers.
        inv = ~aff

        # Get the in-DEM index coordinates
        _x, _y = inv * (x, y)

        # Extract a window of coordinates
        if method == 'bilinear':
            # Get a 2x2 window of pixels surrounding the coordinates
            dim = 2
            offset_x = math.floor(_x)
            offset_y = math.floor(_y)
        elif method in ('spline', 'idw'):
            # NOTE: 'idw' method can actually use any dim. Should allow dim to be
            # an input parameter.
            # Get a 5x5 window of pixels surrounding the coordinates
            dim = 3  # window size (should be odd)
            offset = math.floor(dim / 2.0)
            offset_x = int(math.floor(_x) - offset)
            offset_y = int(math.floor(_y) - offset)
        else:
            raise ValueError('Invalid interpolation method {} selected'.format(method))
            # FIXME: create any necessary special handling for masked vs. unmasked data
            # FIXME: bilinear interp function doesn't work with masked data
        try:
            dem_arr = dem.read(1, window=Window(offset_x, offset_y, dim, dim), masked=True)
        except ValueError as e:
            raise e

        dx = _x - offset_x
        dy = _y - offset_y

        interpolator = methods[method]

        interpolated = interpolator(dx, dy, dem_arr)

        del dem_arr
        if interpolated is None:
            return interpolated
        else:
            return scaling_factor * interpolated

    def idw(self, dx, dy, masked_array):
        if (masked_array.shape[0] != 3) or (masked_array.shape[1] != 3):
            # Received an array that isn't 3x3
            return None

        # Do not attempt interpolation if less than 25% of the data is unmasked.
        ncells = masked_array.shape[0] * masked_array.shape[1]
        if (masked_array.mask.sum() / ncells) >= 0.75:
            return None

        # TODO: save time by masking first
        # TODO: save time by precalculating squared values
        xs = np.array([[i - dx for i in range(masked_array.shape[0])]])
        ys = np.array([[i - dy for i in range(masked_array.shape[1])]])

        distances = np.sqrt((ys ** 2).T @ xs ** 2)

        distances_masked = distances[~masked_array.mask]
        values_masked = masked_array[~masked_array.mask]

        # FIXME: add distance weights? Should be distance squared or something,
        # right?
        inverse_distances = 1 / distances_masked
        weights = inverse_distances / inverse_distances.sum()
        weighted_values = np.multiply(values_masked, weights)

        value = weighted_values.sum()

        del xs, ys, values_masked, weighted_values

        if np.isnan(value):
            return None
        return value

    def bilinear(self, dx, dy, arr):
        nrow, ncol = arr.shape
        if (nrow != 2) or (ncol != 2):
            raise ValueError('Shape of bilinear interpolation input must be 2x2')
        top = dx * arr[0, 0] + (1 - dx) * arr[0, 1]
        bottom = dx * arr[1, 0] + (1 - dx) * arr[1, 1]

        return dy * top + (1 - dy) * bottom

    def bivariate_spline(self, dx, dy, arr):
        nrow, ncol = arr.shape

        ky = min(nrow - 1, 3)
        kx = min(nrow - 1, 3)

        spline = RectBivariateSpline(
            np.array(range(ncol)), np.array(range(nrow)), arr, kx=kx, ky=ky
        )
        return spline(dx, dy)[0][0]
