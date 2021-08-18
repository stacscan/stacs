"""Tests the STACS filepath loader."""

import os
import unittest


class STACSLoaderFilepathTestCase(unittest.TestCase):
    """Tests the STACS filepath loader."""

    def setUp(self):
        """Ensure the application is setup for testing."""
        self.fixtures_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures/"
        )

    def tearDown(self):
        """Ensure everything is torn down between tests."""
        pass
