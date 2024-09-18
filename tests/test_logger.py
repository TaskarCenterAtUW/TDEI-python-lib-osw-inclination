import logging
import unittest
from src.osw_incline.logger import Logger
from unittest.mock import patch, MagicMock


class TestLogger(unittest.TestCase):

    @patch('logging.basicConfig')
    @patch('logging.getLogger')
    def test_configure_logger(self, mock_get_logger, mock_basic_config):
        # Reset the Logger's internal logger to None
        Logger.logger = None

        # Mock the logger instance
        mock_logger_instance = mock_get_logger.return_value

        # Call configure_logger
        logger = Logger.configure_logger()

        # Ensure logging.basicConfig was called with the correct level and format
        mock_basic_config.assert_called_once_with(
            format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            level=logging.INFO
        )

        # Ensure getLogger was called with 'OSW INCLINATION'
        mock_get_logger.assert_any_call('OSW INCLINATION ')
        mock_get_logger.assert_any_call('rasterio')

        # Ensure rasterio logger's level is set to WARNING
        mock_logger_instance.setLevel.assert_any_call(logging.WARNING)

    @patch('logging.getLogger')
    def test_logger_singleton(self, mock_get_logger):
        # Reset the Logger's internal logger to None
        Logger.logger = None

        # Call configure_logger twice
        Logger.configure_logger()
        Logger.configure_logger()

        # Ensure getLogger is called only once for 'OSW INCLINATION'
        mock_get_logger.assert_any_call('OSW INCLINATION ')
        mock_get_logger.assert_any_call('rasterio')

        # Check that getLogger('OSW INCLINATION ') is only called once
        self.assertEqual(mock_get_logger.call_count, 2)

    @patch.object(Logger, 'configure_logger')
    def test_info_logging(self, mock_configure_logger):
        # Mock the logger instance
        mock_logger_instance = MagicMock()
        mock_configure_logger.return_value = mock_logger_instance

        # Call the info method
        Logger.info('Test Info Message')

        # Assert that the info method was called with the correct message
        mock_logger_instance.info.assert_called_once_with('Test Info Message', stacklevel=2)

    @patch.object(Logger, 'configure_logger')
    def test_error_logging(self, mock_configure_logger):
        # Mock the logger instance
        mock_logger_instance = MagicMock()
        mock_configure_logger.return_value = mock_logger_instance

        # Call the error method
        Logger.error('Test Error Message')

        # Assert that the error method was called with the correct message
        mock_logger_instance.error.assert_called_once_with('Test Error Message', stacklevel=2)

    @patch.object(Logger, 'configure_logger')
    def test_warning_logging(self, mock_configure_logger):
        # Mock the logger instance
        mock_logger_instance = MagicMock()
        mock_configure_logger.return_value = mock_logger_instance

        # Call the warning method
        Logger.warning('Test Warning Message')

        # Assert that the warning method was called with the correct message
        mock_logger_instance.warning.assert_called_once_with('Test Warning Message', stacklevel=2)

    @patch.object(Logger, 'configure_logger')
    def test_debug_logging(self, mock_configure_logger):
        # Mock the logger instance
        mock_logger_instance = MagicMock()
        mock_configure_logger.return_value = mock_logger_instance

        # Call the debug method
        Logger.debug('Test Debug Message')

        # Ensure logger was reconfigured to DEBUG level
        mock_logger_instance.debug.assert_called_once_with('Test Debug Message', stacklevel=2)


if __name__ == '__main__':
    unittest.main()
