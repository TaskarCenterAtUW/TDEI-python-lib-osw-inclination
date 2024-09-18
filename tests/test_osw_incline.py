import unittest
from pathlib import Path
from src.osw_incline import OSWIncline
from src.osw_incline.logger import Logger
from unittest.mock import patch, MagicMock
from src.osw_incline.osm_graph import OSMGraph


class TestOSWIncline(unittest.TestCase):

    def setUp(self):
        self.dem_files = ['dummy_tile.tif']
        self.nodes_file = 'nodes.json'
        self.edges_file = 'edges.json'
        self.osw_incline = OSWIncline(
            dem_files=self.dem_files,
            nodes_file=self.nodes_file,
            edges_file=self.edges_file,
            debug=True
        )

    # Test initialization of the OSWIncline class
    def test_initialization(self):
        self.assertEqual(self.osw_incline.dem_files, self.dem_files)
        self.assertEqual(self.osw_incline.nodes_file, self.nodes_file)
        self.assertEqual(self.osw_incline.edges_file, self.edges_file)
        self.assertTrue(self.osw_incline.debug)

    # Test calculate method success flow
    @patch.object(OSMGraph, 'from_geojson', return_value=MagicMock())
    @patch('src.osw_incline.dem_processor.DEMProcessor.process', return_value=None)
    @patch('time.time', side_effect=[1, 5])  # Simulate time taken for the calculation
    @patch.object(Logger, 'info')  # Mock the Logger to capture log calls
    def test_calculate_success(self, mock_logger_info, mock_time, mock_dem_processor, mock_osm_graph):
        result = self.osw_incline.calculate()

        # Check if the process was successful
        self.assertTrue(result)

        # Ensure the OSMGraph and DEMProcessor were used correctly
        mock_osm_graph.assert_called_once_with(
            nodes_path=Path(self.nodes_file),
            edges_path=Path(self.edges_file)
        )
        mock_dem_processor.assert_called_once_with(
            nodes_path=Path(self.nodes_file),
            edges_path=Path(self.edges_file)
        )

        # Check if the time taken was logged
        mock_logger_info.assert_called_once_with('Entire processing took: 4 seconds')

    # Test when OSMGraph.from_geojson raises an exception
    @patch.object(OSMGraph, 'from_geojson', side_effect=Exception("OSMGraph Error"))
    @patch.object(Logger, 'error')  # Mock the Logger to capture error log calls
    def test_calculate_osmgraph_exception(self, mock_logger_error, mock_osm_graph):
        with self.assertRaises(Exception) as context:
            self.osw_incline.calculate()

        # Check if the correct error message was logged and raised
        mock_logger_error.assert_called_once_with('Error processing DEM files: OSMGraph Error')
        self.assertIn('Error processing DEM files', str(context.exception))

    # Test when DEMProcessor.process raises an exception
    @patch.object(OSMGraph, 'from_geojson', return_value=MagicMock())
    @patch('src.osw_incline.dem_processor.DEMProcessor.process', side_effect=Exception("Processing Error"))
    @patch.object(Logger, 'error')  # Mock the Logger to capture error log calls
    def test_calculate_demprocessor_exception(self, mock_logger_error, mock_dem_processor, mock_osm_graph):
        with self.assertRaises(Exception) as context:
            self.osw_incline.calculate()

        # Ensure the error was raised and logged correctly
        mock_logger_error.assert_called_once_with('Error processing DEM files: Processing Error')
        self.assertIn('Error processing DEM files', str(context.exception))

    # Test when calculation finishes with no debug mode
    @patch.object(OSMGraph, 'from_geojson', return_value=MagicMock())
    @patch('src.osw_incline.dem_processor.DEMProcessor.process', return_value=None)
    @patch('time.time', side_effect=[1, 5])
    @patch.object(Logger, 'info')
    def test_calculate_without_debug(self, mock_logger_info, mock_time, mock_dem_processor, mock_osm_graph):
        self.osw_incline.debug = False  # Disable debug mode
        result = self.osw_incline.calculate()

        # The process should still return True
        self.assertTrue(result)

        # Since debug is off, the info logger should not be called
        mock_logger_info.assert_not_called()

    # Test when Logger.debug is called during initialization
    @patch.object(Logger, 'debug')  # Mock the Logger to capture debug log calls
    def test_debug_logging_on_initialization(self, mock_logger_debug):
        OSWIncline(
            dem_files=self.dem_files,
            nodes_file=self.nodes_file,
            edges_file=self.edges_file,
            debug=True
        )

        # Check if the debug log was called on initialization
        mock_logger_debug.assert_called_once_with('Debug mode is enabled')


if __name__ == '__main__':
    unittest.main()
