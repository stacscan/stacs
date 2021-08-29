"""Defines a SARIF output handler for STACS.

SPDX-License-Identifier: BSD-3-Clause
"""

import base64
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from stacs.scan import __about__, model
from stacs.scan.constants import ARCHIVE_FILE_SEPARATOR

# Only one SARIF version will be supported at a time.
SARIF_VERSION = "2.1.0"
SARIF_SCHEMA_URI = "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json"
SARIF_URI_BASE_ID = "STACSROOT"


def confidence_to_level(confidence: int) -> str:
    """Maps the confidence of a finding to a SARIF level."""
    if confidence < 70:
        return "warning"
    else:
        return "error"


def render_artifact(path: str, parent: Optional[int] = None) -> Dict[str, Any]:
    """Create a new artifact entry."""
    artifact = {
        "location": {
            "uri": path,
            "uriBaseId": SARIF_URI_BASE_ID,
        },
    }

    if parent is not None:
        artifact["parentIndex"] = parent

    return artifact


def path_in_artifacts(path: str, artifacts: List[Dict[str, Any]], parent) -> int:
    """Checks if a path exists in the artifacts list."""
    for index, artifact in enumerate(artifacts):
        if path == artifact["location"]["uri"]:
            # Short circuit if we both don't have a parent.
            if artifact.get("parentIndex", None) is None and parent is None:
                return index

            # Check common ancestry.
            try:
                their_parent = artifact.get("parentIndex", None)
                our_parent = parent

                while True:
                    if our_parent == their_parent:
                        their_parent = artifacts[their_parent]["parentIndex"]
                        our_parent = artifacts[our_parent]["parentIndex"]
                    else:
                        break
            except KeyError:
                # We're good all the way back to the root.
                return index

    return None


def add_artifact(
    root: str,
    finding: model.finding.Entry,
    artifacts: List[Dict[str, Any]],
) -> Tuple[int, List[Dict[str, Any]]]:
    """Generates SARIF artifact entires for findings (SARIF v2.1.0 Section 3.24)."""
    parent = None

    for real_path in finding.path.split(ARCHIVE_FILE_SEPARATOR):
        # Strip the scan directory root from the path for Base URIs to work properly.
        path = re.sub(rf"^{root}", "", real_path).lstrip("/")

        # Check if the path already exists.
        new_parent = path_in_artifacts(path, artifacts, parent)
        if new_parent is not None:
            parent = new_parent
            continue

        artifacts.append(render_artifact(path, parent))
        parent = len(artifacts) - 1

    # Add metadata to this entry, if missing.
    artifacts[parent]["hashes"] = {
        "md5": finding.md5,
    }
    return (parent, artifacts)


def render(
    root: str, findings: List[model.finding.Entry], pack: model.pack.Format
) -> str:
    """Renders down a SARIF document for STACS findings."""
    rules = []
    results = []
    artifacts = []

    # Generate a result (SARIF v2.1.0 Section 3.27) for each finding.
    for finding in findings:
        # Suppressions (SARIF v2.1.0 Section 3.27.23) are used to track findings where
        # there is an "ignore" set - via ignore list.
        suppressions = []

        # Create an artifactContent (SARIF v2.1.0 Section 3.3) entry to track the sample
        # of the finding.
        context_content = {}
        artifact_content = {}

        if finding.sample.binary:
            artifact_content["binary"] = finding.sample.finding
            # Unencode and then re-encode the sample into a single B64 string to provide
            # context.
            context_content["binary"] = str(
                base64.b64encode(
                    base64.b64decode(finding.sample.before)
                    + base64.b64decode(finding.sample.finding)
                    + base64.b64decode(finding.sample.after)
                ),
                "utf-8",
            )
        else:
            artifact_content["text"] = finding.sample.finding
            context_content["text"] = (
                finding.sample.before + finding.sample.finding + finding.sample.after
            )

        # Create a new contextRegion (SARIF v2.1.0 Section 3.29.5) to provide contextual
        # information about the finding, but do not include the byte or line number
        # offset.
        context = {"snippet": context_content}

        # Create a new region (SARIF v2.1.0 Section 3.30) to track the location of the
        # finding and the sample.
        region = {
            "byteOffset": finding.location.offset,
            "snippet": artifact_content,
        }

        # Line numbers are optional, as the input file may be binary.
        if finding.location.line:
            region["startLine"] = finding.location.line

        # Add a new artifact for this finding, or retrieve the location of the existing.
        index, artifacts = add_artifact(root, finding, artifacts)

        # Strip the scan directory root from the path, as the we're using the reference
        # from originalUriBaseIds (SARIF v2.1.0 Section 3.14.14) to allow "portability".
        path = finding.path.split(ARCHIVE_FILE_SEPARATOR)[-1]
        relative_path = re.sub(rf"^{root}", "", path).lstrip("/")

        # Pin the artifact location back to a physical location (SARIF v2.1.0 Section
        # 3.28.3).
        physical_location = {
            "physicalLocation": {
                "region": region,
                "contextRegion": context,
                "artifactLocation": {
                    "uri": relative_path,
                    "index": index,
                    "uriBaseId": SARIF_URI_BASE_ID,
                },
            },
        }

        # Generate a new Rule entry, if required (SARIF v2.1.0 Section 3.49).
        rule = None

        for candidate in rules:
            if finding.source.reference == candidate.get("id"):
                rule = candidate
                break

        if not rule:
            # Add the description from the original rule pack entry into the Rule for
            # easy tracking.
            rule = {
                "id": finding.source.reference,
                "shortDescription": {
                    "text": finding.source.description,
                },
            }
            rules.append(rule)

        # Add a Suppression entry if this finding was marked as "Ignored", along with
        # the reason (justification) from the original ignore list.
        if finding.ignore is not None and finding.ignore.ignored:
            suppressions.append(
                {
                    "kind": "external",
                    "status": "accepted",
                    "justification": finding.ignore.reason,
                }
            )

        # Track the finding (Result).
        results.append(
            {
                "message": rule.get("shortDescription"),
                "level": confidence_to_level(finding.confidence),
                "ruleId": finding.source.reference,
                "locations": [
                    physical_location,
                ],
                "suppressions": suppressions,
            }
        )

    # Add a toolComponent (SARIF v2.1.0 Section 3.19), and bolt it all together.
    tool = {
        "driver": {
            "name": __about__.__title__.upper(),
            "rules": rules,
            "version": __about__.__version__,
            "downloadUri": __about__.__uri__,
            "informationUri": __about__.__uri__,
        },
    }
    run = {
        "tool": tool,
        "results": results,
        "artifacts": artifacts,
        "originalUriBaseIds": {
            SARIF_URI_BASE_ID: {
                "uri": f"file://{root.rstrip('/')}/",
            },
        },
    }
    sarif = {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA_URI,
        "runs": [
            run,
        ],
    }

    # Return a stringified JSON representation of the SARIF document.
    return json.dumps(sarif)
