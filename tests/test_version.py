import unittest
from src.osw_incline.version import __version__


class TestVersion(unittest.TestCase):

    def test_version_exists(self):
        # Ensure the version variable exists
        self.assertIsNotNone(__version__)

    def test_version_format(self):
        # Ensure the version follows the format X.Y.Z where X, Y, and Z are integers
        version_parts = __version__.split('.')
        self.assertEqual(len(version_parts), 3)
        self.assertTrue(all(part.isdigit() for part in version_parts))



if __name__ == '__main__':
    unittest.main()
