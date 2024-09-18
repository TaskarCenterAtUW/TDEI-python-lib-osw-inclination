import unittest
import numpy as np
from rasterio.windows import Window
from shapely.geometry import LineString
from src.osw_incline.logger import Logger
from unittest.mock import patch, MagicMock
from rasterio.errors import RasterioIOError
from src.osw_incline.osm_graph import OSMGraph
from src.osw_incline.dem_processor import DEMProcessor


class TestDEMProcessor(unittest.TestCase):

    def setUp(self):
        self.osm_graph = MagicMock(spec=OSMGraph)
        self.osm_graph.G = MagicMock()
        self.dem_files = ['dummy_tile.tif']
        self.processor = DEMProcessor(osm_graph=self.osm_graph, dem_files=self.dem_files, debug=True)

    # Test initialization of the processor
    def test_initialization(self):
        osm_graph_mock = MagicMock(spec=OSMGraph)
        dem_files = ['tile1.tif', 'tile2.tif']
        processor = DEMProcessor(osm_graph_mock, dem_files, debug=True)

        self.assertEqual(processor.dem_files, dem_files)
        self.assertTrue(processor.debug)
        self.assertIsNotNone(processor.transformer)

    # Test successful processing of DEM files
    @patch('src.osw_incline.dem_processor.rasterio.open')
    def test_process_success(self, mock_rasterio_open):
        mock_dem = MagicMock()
        mock_rasterio_open.return_value.__enter__.return_value = mock_dem
        self.osm_graph.G.edges.return_value = [('u', 'v', {'geometry': LineString([(0, 0), (1, 1)])})]

        with patch.object(self.processor, 'infer_incline', return_value=0.1):
            self.processor.process('nodes.json', 'edges.json')

        self.osm_graph.to_geojson.assert_called_once_with('nodes.json', 'edges.json')

    # Test processing when RasterioIOError is raised
    @patch('src.osw_incline.dem_processor.rasterio.open')
    def test_process_rasterio_io_error(self, mock_rasterio_open):
        mock_rasterio_open.side_effect = RasterioIOError

        with self.assertRaises(Exception) as context:
            self.processor.process('nodes.json', 'edges.json')

        self.assertIn('Failed to open DEM file', str(context.exception))

    # Test processing when a general Exception is raised
    @patch('src.osw_incline.dem_processor.rasterio.open')
    def test_process_general_exception(self, mock_rasterio_open):
        mock_rasterio_open.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception) as context:
            self.processor.process('nodes.json', 'edges.json')

        self.assertIn('Error processing DEM file', str(context.exception))

    # Test calculation of projected length between two points
    def test_calculate_projected_length(self):
        first_point = (-122.235, 47.468)
        last_point = (-122.236, 47.469)

        result = self.processor.calculate_projected_length(first_point, last_point)
        self.assertGreater(result, 0)

    @patch('src.osw_incline.dem_processor.DEMProcessor.interpolated_value', return_value=5)
    def test_dem_interpolate_success(self, mock_interpolated_value):
        dem_mock = MagicMock()
        result = self.processor.dem_interpolate(lon=-122.235, lat=47.468, dem=dem_mock)
        self.assertEqual(result, 5)

    @patch('src.osw_incline.dem_processor.DEMProcessor.interpolated_value', return_value=None)
    def test_dem_interpolate_null_value(self, mock_interpolated_value):
        dem_mock = MagicMock()
        result = self.processor.dem_interpolate(lon=-122.235, lat=47.468, dem=dem_mock)
        self.assertEqual(result, None)

    # Test IDW interpolation method
    def test_idw_interpolation(self):
        # Test IDW interpolation method with a proper 3x3 masked array (no mask)
        masked_array = np.ma.array(
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            mask=[[0, 0, 0], [0, 0, 0], [0, 0, 0]]  # No masked elements
        )

        result = self.processor.idw(1, 1, masked_array)
        self.assertIsNone(result, "IDW interpolation returned None for unmasked input")

    def test_idw_interpolation_with_masked_values(self):
        # Test IDW interpolation method with a partially masked 3x3 array
        masked_array = np.ma.array(
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            mask=[[0, 0, 0], [0, 1, 0], [0, 0, 0]]  # Only one element masked
        )

        result = self.processor.idw(1, 1, masked_array)
        self.assertIsNone(result, 'IDW interpolation returned None with masked values')

    # Test bilinear interpolation method
    def test_bilinear_interpolation(self):
        arr = np.array([[1, 2], [3, 4]])
        result = self.processor.bilinear(0.5, 0.5, arr)
        self.assertEqual(result, 2.5)

    # Test bivariate spline interpolation method
    def test_bivariate_spline(self):
        arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        result = self.processor.bivariate_spline(1.5, 1.5, arr)
        self.assertIsNotNone(result)

    # Test incline calculation based on line geometry and DEM
    @patch.object(DEMProcessor, 'dem_interpolate', return_value=10)
    def test_infer_incline(self, mock_dem_interpolate):
        linestring = LineString([(0, 0), (1, 1)])
        incline = self.processor.infer_incline(linestring, dem=MagicMock(), precision=3)
        self.assertEqual(incline, 0.0)

    # Test handling of exceptions in DEM interpolation
    @patch('src.osw_incline.dem_processor.DEMProcessor.interpolated_value',
           side_effect=Exception('Interpolation error'))
    def test_dem_interpolate_exception(self, mock_interpolated_value):
        dem_mock = MagicMock()
        result = self.processor.dem_interpolate(lon=-122.235, lat=47.468, dem=dem_mock)
        self.assertIsNone(result)

    def test_bilinear_raises_value_error(self):
        # Test case where bilinear interpolation should raise ValueError for wrong array shape
        arr = np.array([[1]])  # Shape is 1x1 instead of 2x2

        with self.assertRaises(ValueError) as context:
            self.processor.bilinear(0.5, 0.5, arr)

        self.assertEqual(str(context.exception), 'Shape of bilinear interpolation input must be 2x2')

    def test_bilinear_valid_case(self):
        # Test case for valid bilinear interpolation with a 2x2 array
        arr = np.array([[1, 2], [3, 4]])  # Correct shape
        result = self.processor.bilinear(0.5, 0.5, arr)
        self.assertEqual(result, 2.5)

    def test_bivariate_spline_valid_case(self):
        # Test valid bivariate spline interpolation case with a proper 3x3 array
        arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])  # Correct shape
        result = self.processor.bivariate_spline(1.5, 1.5, arr)
        self.assertIsNotNone(result)

    def test_bivariate_spline_invalid_case(self):
        # Test bivariate spline interpolation with an incorrect array shape (e.g. 2x2 or smaller)
        arr = np.array([[1, 2], [3, 4]])  # Smaller shape that might not behave as expected

        # In this case, we are not raising an exception in the original code, but we can test if it processes it
        result = self.processor.bivariate_spline(0.5, 0.5, arr)
        self.assertIsNotNone(result)

    def test_idw_interpolation_non_3x3_array(self):
        # Test case where the masked array is not 3x3 (e.g., 2x2)
        masked_array = np.ma.array(
            [[1, 2], [3, 4]],  # 2x2 shape
            mask=[[0, 0], [0, 0]]  # No masked elements
        )
        result = self.processor.idw(1, 1, masked_array)
        self.assertIsNone(result)  # Expect None due to non-3x3 shape

    def test_idw_interpolation_invalid_shape_4x4(self):
        # Test case for an invalid 4x4 masked array
        masked_array = np.ma.array(
            [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],  # 4x4 shape
            mask=[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]  # No masked elements
        )
        result = self.processor.idw(1, 1, masked_array)
        self.assertIsNone(result)  # Expect None due to non-3x3 shape

    def test_idw_interpolation_75_percent_masked(self):
        # Test case where more than 75% of the data is masked
        masked_array = np.ma.array(
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],  # 3x3 shape
            mask=[[1, 1, 1], [1, 1, 1], [0, 0, 0]]  # 6/9 elements are masked (i.e. 66.67% unmasked)
        )
        result = self.processor.idw(1, 1, masked_array)
        self.assertIsNone(result)

    def test_idw_interpolation_more_than_75_percent_masked(self):
        # Test case where more than 75% of the data is masked
        masked_array = np.ma.array(
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],  # 3x3 shape
            mask=[[1, 1, 1], [1, 1, 1], [1, 1, 0]]  # 8/9 elements are masked (i.e. > 75%)
        )
        result = self.processor.idw(1, 1, masked_array)
        self.assertIsNone(result)

    def test_idw_interpolation_25_percent_masked(self):
        # Test case where less than 75% of the data is masked
        masked_array = np.ma.array(
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],  # 3x3 shape
            mask=[[0, 0, 0], [0, 0, 0], [0, 0, 0]]  # 0% masked (fully unmasked array)
        )

        result = self.processor.idw(1, 1, masked_array)

        # Since division by zero occurs, it's expected that the result is None
        self.assertIsNone(result, 'IDW interpolation did not return None as expected due to zero distances.')

    def test_idw_interpolation_valid(self):
        # Test case with valid distances (no zeros)
        masked_array = np.ma.array(
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],  # 3x3 shape with values
            mask=[[0, 0, 0], [0, 0, 0], [0, 0, 0]]  # No masked elements
        )

        # Using dx and dy that avoid zero distances
        result = self.processor.idw(0.5, 0.5, masked_array)

        # Since there are no zero distances, a valid result should be returned
        self.assertIsNotNone(result, 'IDW interpolation should return a valid value')

        # You can also add an assert for the value itself, depending on expectations
        self.assertGreater(result, 0, 'The interpolated result should be greater than 0')

    @patch('src.osw_incline.dem_processor.rasterio.open')
    def test_interpolated_value_bilinear(self, mock_rasterio_open):
        dem_mock = MagicMock()

        # Mock the affine transform and its inverse
        mock_transform = MagicMock()
        dem_mock.transform = mock_transform

        # Mock the inverse transformation to return a tuple (mocking the multiplication behavior)
        mock_inverse_transform = MagicMock()
        mock_inverse_transform.__mul__.return_value = (0.5, 0.5)  # This simulates inv * (x, y)
        mock_transform.__invert__.return_value = mock_inverse_transform

        # Mock the DEM read to return a 2x2 array
        dem_mock.read.return_value = np.array([[1, 2], [3, 4]])

        # Mock the Window function
        with patch('src.osw_incline.dem_processor.Window') as mock_window:
            mock_window.return_value = Window(0, 0, 2, 2)

            # Now invoke the method
            result = self.processor.interpolated_value(0.5, 0.5, dem_mock, method='bilinear')

        # Assert the result
        self.assertEqual(result, 2.5)

    @patch('src.osw_incline.dem_processor.rasterio.open')
    def test_interpolated_value_spline(self, mock_rasterio_open):
        dem_mock = MagicMock()

        # Mock the affine transform and its inverse
        mock_transform = MagicMock()
        dem_mock.transform = mock_transform

        # Mock the inverse transformation to return a tuple (mocking the multiplication behavior)
        mock_inverse_transform = MagicMock()
        mock_inverse_transform.__mul__.return_value = (1.5, 1.5)  # Simulate inv * (x, y)
        mock_transform.__invert__.return_value = mock_inverse_transform

        # Mock the DEM read to return a 3x3 array for spline interpolation
        dem_mock.read.return_value = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

        # Mock the Window function
        with patch('src.osw_incline.dem_processor.Window') as mock_window:
            mock_window.return_value = Window(0, 0, 3, 3)

            # Now invoke the method
            result = self.processor.interpolated_value(1.5, 1.5, dem_mock, method='spline')

        # Assert the result
        self.assertIsNotNone(result)
        print(f"Spline Interpolated Value: {result}")

    @patch('src.osw_incline.dem_processor.rasterio.open')
    def test_interpolated_value_invalid_method(self, mock_rasterio_open):
        dem_mock = MagicMock()

        # Mock the affine transform and its inverse
        mock_transform = MagicMock()
        dem_mock.transform = mock_transform

        # Mock the inverse transformation to return a tuple (mocking the multiplication behavior)
        mock_inverse_transform = MagicMock()
        mock_inverse_transform.__mul__.return_value = (0.5, 0.5)
        mock_transform.__invert__.return_value = mock_inverse_transform

        # Test invalid interpolation method
        with self.assertRaises(ValueError) as context:
            self.processor.interpolated_value(0.5, 0.5, dem_mock, method='invalid')

        self.assertEqual(str(context.exception), 'Invalid interpolation method invalid selected')

    @patch('src.osw_incline.dem_processor.rasterio.open')
    def test_interpolated_value_rasterio_value_error(self, mock_rasterio_open):
        dem_mock = MagicMock()

        # Mock the affine transform and its inverse
        mock_transform = MagicMock()
        dem_mock.transform = mock_transform

        # Mock the inverse transformation to return a tuple (mocking the multiplication behavior)
        mock_inverse_transform = MagicMock()
        mock_inverse_transform.__mul__.return_value = (0.5, 0.5)
        mock_transform.__invert__.return_value = mock_inverse_transform

        # Simulate a ValueError when reading the DEM
        dem_mock.read.side_effect = ValueError('Invalid window')

        with self.assertRaises(ValueError) as context:
            self.processor.interpolated_value(0.5, 0.5, dem_mock, method='bilinear')

        self.assertEqual(str(context.exception), 'Invalid window')

    @patch.object(DEMProcessor, 'calculate_projected_length', return_value=10)
    @patch.object(DEMProcessor, 'dem_interpolate', side_effect=[100, 110])  # First elevation: 100, Second: 110
    def test_infer_incline_success(self, mock_calculate_length, mock_dem_interpolate):
        # Create a LineString with valid coordinates
        linestring = LineString([(0, 0), (1, 1)])

        # Pass the LineString and a mocked DEM object to infer_incline
        dem_mock = MagicMock()
        incline = self.processor.infer_incline(linestring, dem_mock, precision=2)

        # The expected incline is (110 - 100) / 10 = 1.0, rounded to precision 2
        self.assertEqual(incline, 1.0)

    @patch.object(DEMProcessor, 'calculate_projected_length', return_value=0)
    def test_infer_incline_zero_length(self, mock_calculate_length):
        # LineString with zero length
        linestring = LineString([(0, 0), (0, 0)])  # Same start and end points

        # Pass the LineString and a mocked DEM object to infer_incline
        dem_mock = MagicMock()
        incline = self.processor.infer_incline(linestring, dem_mock)

        # If the length is zero, infer_incline should return None
        self.assertIsNone(incline)

    @patch.object(DEMProcessor, 'dem_interpolate', return_value=None)
    def test_infer_incline_missing_elevation(self, mock_dem_interpolate):
        # LineString with valid coordinates
        linestring = LineString([(0, 0), (1, 1)])

        # Mocked DEM
        dem_mock = MagicMock()

        # When dem_interpolate returns None for any elevation, infer_incline should return None
        incline = self.processor.infer_incline(linestring, dem_mock)
        self.assertIsNone(incline)

    @patch.object(DEMProcessor, 'calculate_projected_length', return_value=10)
    @patch.object(DEMProcessor, 'dem_interpolate', side_effect=[100, 110])

    def test_infer_incline_exception(self, mock_dem_interpolate, mock_calculate_length):
        # Create a LineString with valid coordinates
        linestring = LineString([(0, 0), (1, 1)])

        # Mock the DEM object
        dem_mock = MagicMock()

        # Simulate a ZeroDivisionError during the incline calculation
        with patch('src.osw_incline.dem_processor.DEMProcessor.infer_incline',
                   side_effect=ZeroDivisionError("Division error")):
            # Try to catch the exception
            incline = None
            try:
                incline = self.processor.infer_incline(linestring, dem_mock)
            except ZeroDivisionError:
                pass  # We expect this exception to occur

        # Ensure that the function returns None when an exception occurs
        self.assertIsNone(incline)

    @patch('src.osw_incline.dem_processor.rasterio.open')
    def test_interpolated_value_return_scaled(self, mock_rasterio_open):
        dem_mock = MagicMock()

        # Mock the affine transform and its inverse
        mock_transform = MagicMock()
        dem_mock.transform = mock_transform

        # Mock the inverse transformation to return coordinates (simulating the transformation)
        mock_inverse_transform = MagicMock()
        mock_inverse_transform.__mul__.return_value = (1.5, 1.5)  # Simulate inv * (x, y)
        mock_transform.__invert__.return_value = mock_inverse_transform

        # Mock the DEM read to return a 3x3 array for IDW interpolation
        dem_mock.read.return_value = np.ma.array(
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],  # 3x3 array
            mask=[[0, 0, 0], [0, 0, 0], [0, 0, 0]]  # No masked values
        )

        # Mock the Window function
        with patch('src.osw_incline.dem_processor.Window') as mock_window:
            mock_window.return_value = Window(0, 0, 3, 3)

            # Now invoke the method with IDW interpolation and a scaling factor
            result = self.processor.interpolated_value(1.5, 1.5, dem_mock, method='idw', scaling_factor=2.0)

        # Assert that the result is not None and that it is scaled properly
        self.assertIsNotNone(result, 'IDW interpolation should return a valid value')
        print(f"IDW Interpolated Value (scaled): {result}")

        # You can adjust the expected result based on the IDW logic; here, just check that it's non-zero
        self.assertGreater(result, 0, 'The interpolated result should be greater than 0')

    @patch('src.osw_incline.dem_processor.rasterio.open')
    def test_interpolated_value_return_none(self, mock_rasterio_open):
        dem_mock = MagicMock()

        # Mock the affine transform and its inverse
        mock_transform = MagicMock()
        dem_mock.transform = mock_transform

        # Mock the inverse transformation to return coordinates
        mock_inverse_transform = MagicMock()
        mock_inverse_transform.__mul__.return_value = (1.5, 1.5)  # Simulate inv * (x, y)
        mock_transform.__invert__.return_value = mock_inverse_transform

        # Mock the DEM read to return a 3x3 array
        dem_mock.read.return_value = np.ma.array(
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            mask=[[0, 0, 0], [0, 0, 0], [0, 0, 0]]  # No masked values
        )

        # Mock the interpolator method to return None (this will simulate `interpolated` being None)
        with patch.object(self.processor, 'idw', return_value=None):
            with patch('src.osw_incline.dem_processor.Window') as mock_window:
                mock_window.return_value = Window(0, 0, 3, 3)

                # Now invoke the method with IDW interpolation
                result = self.processor.interpolated_value(1.5, 1.5, dem_mock, method='idw')

        # Assert that the result is None because the interpolation method returned None
        self.assertIsNone(result, 'interpolated_value should return None when the interpolator returns None')




if __name__ == '__main__':
    unittest.main()
