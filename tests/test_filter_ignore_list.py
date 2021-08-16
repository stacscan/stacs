"""Tests the STACS allow list filter."""

import os
import unittest

import stacs


class STACSFilterAllowListTestCase(unittest.TestCase):
    """Tests the STACS allow list filter."""

    def setUp(self):
        """Ensure the application is setup for testing."""
        self.fixtures_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures/ignore_list/"
        )

    def tearDown(self):
        """Ensure everything is torn down between tests."""
        pass

    def test_by_path(self):
        """Validate whether path filters are working."""
        # Use the same fixture for all branches.
        finding = stacs.model.finding.Entry(
            path="/a/a",
            md5="fa19207ef28b6a97828e3a22b11290e9",
            location=stacs.model.finding.Location(
                offset=300,
            ),
            source=stacs.model.finding.Source(
                module="stacs.scanner.rules",
                reference="SomeRule",
            ),
        )

        # Define ignores which should correctly be ignored.
        hits = [
            # Path matches, no other constraint.
            stacs.model.ignore_list.Entry(path="/a/a", reason="Test"),
            # Path matches, reference matches.
            stacs.model.ignore_list.Entry(
                path="/a/a", reason="Test", references=["SomeRule", "OtherRule"]
            ),
            # Path matches, offset matches.
            stacs.model.ignore_list.Entry(path="/a/a", reason="Test", offset=300),
        ]

        # Path differs.
        miss = stacs.model.ignore_list.Entry(path="/a/b", reason="Test")
        self.assertEqual(stacs.filter.ignore_list.by_path(finding, miss), False)

        # Path matches, reference differs.
        miss = stacs.model.ignore_list.Entry(
            path="/a/a", reason="Test", references=["OtherRule"]
        )
        self.assertEqual(stacs.filter.ignore_list.by_path(finding, miss), False)

        # Path matches, offset differs.
        miss = stacs.model.ignore_list.Entry(path="/a/a", reason="Test", offset=1234)
        self.assertEqual(stacs.filter.ignore_list.by_path(finding, miss), False)

        # Ensure all hit entries are matches.
        for hit in hits:
            self.assertEqual(stacs.filter.ignore_list.by_path(finding, hit), True)

    def test_by_pattern(self):
        """Validate whether pattern filters are working."""
        # Use the same fixture for all branches.
        finding = stacs.model.finding.Entry(
            path="/a/tests/a",
            md5="fa19207ef28b6a97828e3a22b11290e9",
            location=stacs.model.finding.Location(
                offset=300,
            ),
            source=stacs.model.finding.Source(
                module="stacs.scanner.rules",
                reference="SomeRule",
            ),
        )

        # Pattern matches, no other constraint.
        hit = stacs.model.ignore_list.Entry(pattern=".*/tests/.*", reason="Test")
        self.assertEqual(stacs.filter.ignore_list.by_pattern(finding, hit), True)

        # Pattern matches, reference matches.
        hit = stacs.model.ignore_list.Entry(
            pattern=".*/tests/.*",
            reason="Test",
            references=["SomeRule", "OtherRule"],
        )
        self.assertEqual(stacs.filter.ignore_list.by_pattern(finding, hit), True)

        # Pattern matches, offset matches.
        hit = stacs.model.ignore_list.Entry(
            pattern=".*/tests/.*", reason="Test", offset=300
        )
        self.assertEqual(stacs.filter.ignore_list.by_pattern(finding, hit), True)

        # Pattern differs.
        miss = stacs.model.ignore_list.Entry(pattern=r"\.shasums$", reason="Test")
        self.assertEqual(stacs.filter.ignore_list.by_pattern(finding, miss), False)

        # Pattern matches, reference differs.
        miss = stacs.model.ignore_list.Entry(
            pattern=".*/tests/.*", reason="Test", references=["OtherRule"]
        )
        self.assertEqual(stacs.filter.ignore_list.by_pattern(finding, miss), False)

        # Pattern matches, offset differs.
        miss = stacs.model.ignore_list.Entry(
            pattern=".*/tests/.*", reason="Test", offset=1234
        )
        self.assertEqual(stacs.filter.ignore_list.by_pattern(finding, miss), False)

    def test_by_hash(self):
        """Validate whether hash filters are working."""
        # Use the same fixture for all branches.
        finding = stacs.model.finding.Entry(
            path="/a/tests/a",
            md5="fa19207ef28b6a97828e3a22b11290e9",
            location=stacs.model.finding.Location(
                offset=300,
            ),
            source=stacs.model.finding.Source(
                module="stacs.scanner.rules",
                reference="SomeRule",
            ),
        )

        # Hash matches, no other constraint.
        hit = stacs.model.ignore_list.Entry(
            md5="fa19207ef28b6a97828e3a22b11290e9", reason="Test"
        )
        self.assertEqual(stacs.filter.ignore_list.by_hash(finding, hit), True)

        # Hash matches, reference matches.
        hit = stacs.model.ignore_list.Entry(
            md5="fa19207ef28b6a97828e3a22b11290e9",
            reason="Test",
            references=["SomeRule", "OtherRule"],
        )
        self.assertEqual(stacs.filter.ignore_list.by_hash(finding, hit), True)

        # Hash matches, offset matches.
        hit = stacs.model.ignore_list.Entry(
            md5="fa19207ef28b6a97828e3a22b11290e9", reason="Test", offset=300
        )
        self.assertEqual(stacs.filter.ignore_list.by_hash(finding, hit), True)

        # Hash differs.
        miss = stacs.model.ignore_list.Entry(
            md5="cf42e6f36da80658591489975bbd845b", reason="Test"
        )
        self.assertEqual(stacs.filter.ignore_list.by_hash(finding, miss), False)

        # Hash matches, reference differs.
        miss = stacs.model.ignore_list.Entry(
            md5="fa19207ef28b6a97828e3a22b11290e9",
            reason="Test",
            references=["OtherRule"],
        )
        self.assertEqual(stacs.filter.ignore_list.by_hash(finding, miss), False)

        # Hash matches, offset differs.
        miss = stacs.model.ignore_list.Entry(
            md5="fa19207ef28b6a97828e3a22b11290e9", reason="Test", offset=1234
        )
        self.assertEqual(stacs.filter.ignore_list.by_hash(finding, miss), False)
