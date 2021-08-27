"""Defines types to assist with loading and processing of manifests.

SPDX-License-Identifier: BSD-3-Clause
"""

from typing import List
from pydantic import BaseModel, Extra, Field


class Entry(BaseModel, extra=Extra.forbid):
    """Defines the schema of a file to process."""

    path: str = Field(
        None,
        title="The path to the file on disk.",
    )
    overlay: str = Field(
        None,
        title=(
            "The overlay path of a file. This is used to generate virtual paths which "
            "provider the path to files inside of archives."
        ),
    )
    md5: str = Field(
        None,
        title="The MD5 sum of the file.",
    )
    mime: str = Field(
        None,
        title="The mimetype of the file.",
    )


class Format(BaseModel, extra=Extra.forbid):
    """Defines the schema of a manifest file."""

    files: List[Entry] = Field(
        [],
        title="A list of files to scan.",
    )
