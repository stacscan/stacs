"""Tests the STACS SARIF output module."""

import unittest

import stacs.scan


class STACSOutputSARIFTestCase(unittest.TestCase):
    """Tests the STACS SARIF output module."""

    def setUp(self):
        """Ensure the application is setup for testing."""
        pass

    def tearDown(self):
        """Ensure everything is torn down between tests."""
        pass

    def test_add_artifact(self):
        """Ensure that artifact entries are deduplicated by their full path."""
        findings = [
            stacs.scan.model.finding.Entry(
                path="/tmp/rootfs/etc/passwd",
                md5="b39bfc0e26a30024c76e4dcb8a1eae87",
            ),
            stacs.scan.model.finding.Entry(
                path="/tmp/rootfs/etc/passwd",
                md5="b39bfc0e26a30024c76e4dcb8a1eae87",
            ),
            stacs.scan.model.finding.Entry(
                path="/tmp/rootfs/a.tar.gz!a.tar!cred",
                md5="bf072e9119077b4e76437a93986787ef",
            ),
            stacs.scan.model.finding.Entry(
                path="/tmp/rootfs/a.tar.gz!a.tar!b_cred",
                md5="30cf3d7d133b08543cb6c8933c29dfd7",
            ),
            stacs.scan.model.finding.Entry(
                path="/tmp/rootfs/b.tar.gz!b_cred",
                md5="57b8d745384127342f95660d97e1c9c2",
            ),
            stacs.scan.model.finding.Entry(
                path="/tmp/rootfs/b.tar.gz!a.tar!cred",
                md5="787c9a8e2148e711f6e9f44696cf341f",
            ),
            stacs.scan.model.finding.Entry(
                path="/tmp/rootfs/a.tar.gz!a.tar!b.tar.gz!b.tar!pass",
                md5="d2a33790e5bf28b33cdbf61722a06989",
            ),
        ]

        # Ensure we get the expected number of artifacts in the artifacts list.
        artifacts = []
        for finding in findings:
            _, artifacts = stacs.scan.output.sarif.add_artifact(
                "/tmp/rootfs/", finding, artifacts
            )

        # Ensure findings are unfurled into the expected number of unique artifacts.
        self.assertEqual(len(artifacts), 12)
