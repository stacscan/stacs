"""Tests the STACS allow list model and validator."""

import json
import os
import unittest

import stacs.scan


class STACSModelAllowListTestCase(unittest.TestCase):
    """Tests the STACS allow list model and validator."""

    def setUp(self):
        """Ensure the application is setup for testing."""
        self.fixtures_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures/ignore_list/"
        )

    def tearDown(self):
        """Ensure everything is torn down between tests."""
        pass

    def test_simple(self):
        """Ensure that simple allow lists can be loaded."""
        with open(os.path.join(self.fixtures_path, "001-simple.valid.json"), "r") as f:
            stacs.scan.model.ignore_list.Format(**json.load(f))

    def test_hierarchical_loading(self):
        """Ensure that hierarchical allow lists can be loaded."""
        with open(os.path.join(self.fixtures_path, "002-project.valid.json"), "r") as f:
            stacs.scan.model.ignore_list.Format(**json.load(f))
