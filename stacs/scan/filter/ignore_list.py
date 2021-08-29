"""Defines a filter which sets the ignore flag on entries present in an ignore list.

SPDX-License-Identifier: BSD-3-Clause
"""

import re
from typing import List

from stacs.scan.exceptions import IgnoreListException
from stacs.scan.model import finding, ignore_list


def by_pattern(finding: finding.Entry, ignore: ignore_list.Entry) -> bool:
    """Process a regex ignore list entry."""
    # Short circuit if no pattern is set.
    if not ignore.pattern:
        return False

    # If there's a match on the path, check whether the ignore is for the same module.
    if re.search(ignore.pattern, finding.path):
        if ignore.module != finding.source.module:
            return False

        # Then check whether the ignore is for the particular reference.
        if ignore.references:
            if finding.source.reference in ignore.references:
                return True

            return False

        # Or check whether the ignore is for the same offest.
        if ignore.offset is not None:
            if finding.location.offset == ignore.offset:
                return True
            return False

        # In this case this is a fairly permissive ignore.
        return True

    return False


def by_path(finding: finding.Entry, ignore: ignore_list.Entry) -> bool:
    """Process a path based ignore list entry."""
    # Short circuit if no path is set.
    if not ignore.path:
        return False

    # If there's a match on the hash, check whether the ignore is for the same module.
    if ignore.path == finding.path:
        if finding.source.module != ignore.module:
            return False

        # Then check whether the ignore is for the particular reference.
        if ignore.references:
            if finding.source.reference in ignore.references:
                return True
            return False

        # Or check whether the ignore is for the same offest.
        if ignore.offset is not None:
            if finding.location.offset == ignore.offset:
                return True
            return False

        # In this case this is a fairly permissive ignore.
        return True

    return False


def by_hash(finding: finding.Entry, ignore: ignore_list.Entry) -> bool:
    """Process a hash based ignore list entry."""
    # Short circuit if no hash is set.
    if not ignore.md5:
        return False

    # If there's a match on the hash, check whether the ignore is for the same module.
    if ignore.md5 == finding.md5:
        if finding.source.module != ignore.module:
            return False

        # Then check whether the ignore is for the particular reference.
        if ignore.references:
            if finding.source.reference in ignore.references:
                return True
            return False

        # Or check whether the ignore is for the same offest.
        if ignore.offset is not None:
            if finding.location.offset == ignore.offset:
                return True
            return False

        # In this case this is a fairly permissive ignore.
        return True

    return False


def process(
    findings: List[finding.Entry],
    ignore_list: ignore_list.Format,
) -> List[finding.Entry]:
    """Processes an ignore list and marks the relevant findings as ignored."""
    filtered_findings = []

    for entry in findings:
        for ignore in ignore_list.ignore:
            try:
                if by_path(entry, ignore):
                    ignore = finding.Ignore(
                        ignored=True,
                        reason=ignore.reason,
                    )
                    entry.ignore = ignore
                    break

                if by_pattern(entry, ignore):
                    ignore = finding.Ignore(
                        ignored=True,
                        reason=ignore.reason,
                    )
                    entry.ignore = ignore
                    break

                if by_hash(entry, ignore):
                    ignore = finding.Ignore(
                        ignored=True,
                        reason=ignore.reason,
                    )
                    entry.ignore = ignore
                    break
            except re.error as err:
                raise IgnoreListException(
                    f"Error in ignore list entry '{ignore.reason}': {err}"
                )

        # Add the finding to our results, whether updated or not.
        filtered_findings.append(entry)

    return filtered_findings
