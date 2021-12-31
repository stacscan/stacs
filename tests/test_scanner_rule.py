"""Tests the STACS Scanner Rule module."""

import os
import unittest

import stacs.scan


class STACSScannerRuleTestCase(unittest.TestCase):
    """Tests the STACS Scanner Rule module."""

    def setUp(self):
        """Ensure the application is setup for testing."""
        self.fixtures_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures/findings/"
        )

    def tearDown(self):
        """Ensure everything is torn down between tests."""
        pass

    def test_generate_sample(self):
        """Ensures that samples are correctly generated."""
        reduced_after_finding = stacs.scan.model.manifest.Entry(
            path=os.path.join(self.fixtures_path, "001.txt")
        )
        reduced_before_finding = stacs.scan.model.manifest.Entry(
            path=os.path.join(self.fixtures_path, "002.txt")
        )
        only_finding = stacs.scan.model.manifest.Entry(
            path=os.path.join(self.fixtures_path, "003.txt")
        )
        sufficent_before_after_finding = stacs.scan.model.manifest.Entry(
            path=os.path.join(self.fixtures_path, "004.txt")
        )

        # Check that the correct number of bytes were extracted before and after the
        # respective findings.
        context = stacs.scan.scanner.rules.generate_sample(
            reduced_after_finding,
            191,  # Offset.
            40,  # Size.
        )
        self.assertEqual(len(context.before), 20)
        self.assertEqual(len(context.finding), 40)
        self.assertEqual(len(context.after), 1)

        context = stacs.scan.scanner.rules.generate_sample(
            reduced_before_finding,
            3,  # Offset.
            40,  # Size.
        )
        self.assertEqual(len(context.before), 3)
        self.assertEqual(len(context.finding), 40)
        self.assertEqual(len(context.after), 20)

        context = stacs.scan.scanner.rules.generate_sample(
            only_finding,
            0,  # Offset.
            40,  # Size.
        )
        self.assertEqual(len(context.before), 0)
        self.assertEqual(len(context.finding), 40)
        self.assertEqual(len(context.after), 0)

        context = stacs.scan.scanner.rules.generate_sample(
            sufficent_before_after_finding,
            137,  # Offset.
            40,  # Size.
        )
        self.assertEqual(len(context.before), 20)
        self.assertEqual(len(context.finding), 40)
        self.assertEqual(len(context.after), 20)
