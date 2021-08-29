"""Defines types to assist with loading and processing of ignore lists.

SPDX-License-Identifier: BSD-3-Clause
"""

import json
import os
from typing import List

from pydantic import BaseModel, Extra, Field, validator
from stacs.scan.exceptions import IgnoreListException, STACSException


class Entry(BaseModel, extra=Extra.forbid):
    """Defines the schema of an ignore."""

    path: str = Field(
        None,
        title="The path of a file to ignore.",
    )
    pattern: str = Field(
        None,
        title="A pattern of the file path to ignore.",
    )
    reason: str = Field(
        title="The reason for ignoring the finding.",
    )
    md5: str = Field(
        None,
        title="The MD5 sum of the file to ignore.",
    )
    module: str = Field(
        "rules",
        title="Which module to ignore findings from.",
    )
    references: List[str] = Field(
        [],
        title=(
            "A list of references to ignore findings from, defaults to all if not set."
        ),
    )
    offset: int = Field(
        None,
        title="The offset of the specific finding to ignore.",
    )

    @validator("path", always=True)
    def exclusive_path_or_pattern(cls, value, values):
        """Ensure that either path or pattern is provided, not both."""
        if values.get("pattern") and value:
            raise IgnoreListException(
                "Either path OR pattern must be specified, not both."
            )

        if values.get("pattern") and not value and not values.get("md5"):
            raise IgnoreListException("One of pattern, path, or md5 must be set.")

        return value

    @validator("offset", "references", always=True)
    def offset_and_references_requires_module(cls, value, values):
        """Ensure that if offset or references is set, module is as well."""
        if not values.get("module"):
            raise IgnoreListException("Module must be set for this type of ignore.")

        return value

    @validator("offset", always=True)
    def offset_and_refernces_both_set(cls, value, values):
        if value and len(values.get("references")) > 0:
            raise IgnoreListException(
                "An offset cannot be combined with a list of references."
            )

        return value


class Format(BaseModel, extra=Extra.forbid):
    """Defines the schema of the ignore list."""

    include: List[str] = Field(
        [],
        title="Define a list of additional ignore lists to include.",
    )
    ignore: List[Entry] = Field(
        [],
        title="Define a list of ignore list entries.",
    )


def from_file(filename: str) -> Format:
    """Load an ignore list from file, returning a rendered down and complete list."""
    parent_file = os.path.abspath(os.path.expanduser(filename))
    parent_path = os.path.dirname(parent_file)

    # Load the parent ignore list, and then recurse as needed to handle includes.
    try:
        with open(parent_file, "r") as fin:
            parent_list = Format(**json.load(fin))

        # Roll over the include list and replace all entries with a fully qualified,
        # path, if not already set.
        for index, path in enumerate(parent_list.include):
            parent_list.include[index] = os.path.expanduser(path)
            if not path.startswith("/"):
                parent_list.include[index] = os.path.join(parent_path, path)
    except (OSError, json.JSONDecodeError) as err:
        raise STACSException(err)

    # Recursively load included ignore lists.
    for file in parent_list.include:
        child_pack = from_file(file)
        parent_list.ignore.extend(child_pack.ignore)

    # Finally strip the included ignore lists from the entry, as these have been
    # resolved, returning the loaded ignore lists to the caller.
    parent_list.include.clear()
    return parent_list
