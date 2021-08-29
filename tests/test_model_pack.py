"""Tests the STACS pack model and validator."""

import json
import os
import unittest

import stacs.scan


class STACSModelPackTestCase(unittest.TestCase):
    """Tests the STACS pack model and validator."""

    def setUp(self):
        """Ensure the application is setup for testing."""
        self.fixtures_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures/pack/"
        )

    def tearDown(self):
        """Ensure everything is torn down between tests."""
        pass

    def test_simple_pack(self):
        """Ensure that simple packs can be loaded."""
        with open(os.path.join(self.fixtures_path, "001-simple.valid.json"), "r") as f:
            stacs.scan.model.pack.Format(**json.load(f))
