"""Defines types to assist with reporting findings.

SPDX-License-Identifier: BSD-3-Clause
"""

from pydantic import BaseModel, Extra, Field


class Location(BaseModel, extra=Extra.forbid):
    """Defines data associated with a location of a finding."""

    line: int = Field(
        None,
        title="The line number which contains the finding.",
    )
    offset: int = Field(
        None,
        title="The offset from the start of the file of the finding (in bytes).",
    )


class Source(BaseModel, extra=Extra.forbid):
    """Defines data associated with the source of a finding."""

    module: str = Field(
        title="The STACS module which generated the finding.",
    )
    description: str = Field(
        None,
        title="A description of the finding",
    )
    reference: str = Field(
        title="A reference to the element which generated the finding."
    )
    version: str = Field(
        None,
        title="The version of the element which generated the finding.",
    )


class Sample(BaseModel, extra=Extra.forbid):
    """The content and context of a finding."""

    window: int = Field(
        title="The number of bytes before and after a finding included in the sample.",
    )
    before: str = Field(
        title="The contents of N bytes before the finding.",
    )
    after: str = Field(
        title="The contents of N bytes after the finding.",
    )
    finding: str = Field(
        title="The contents of the finding.",
    )
    binary: bool = Field(
        title="Indicates that the finding was binary and is base64 encoded."
    )


class Ignore(BaseModel, extra=Extra.forbid):
    """Defines the ignore schema of a finding."""

    ignored: bool = Field(
        False,
        title="Whether the finding should be ignored due to allow list.",
    )
    reason: str = Field(
        title="The reason to ignore the finding.",
    )


class Entry(BaseModel, extra=Extra.forbid):
    """Defines the schema of a finding."""

    path: str = Field(
        title="The path to the file.",
    )
    md5: str = Field(
        title="The MD5 sum of the file.",
    )
    confidence: float = Field(
        None,
        title="The confidence of the finding.",
    )
    location: Location = Field(
        None,
        title="The location of the finding in the input file.",
    )
    sample: Sample = Field(
        None,
        title="Information relating to the content of the finding.",
    )
    source: Source = Field(
        None,
        title="Information about the source of the finding.",
    )
    ignore: Ignore = Field(
        None,
        title="Information about whether the entry should be ignored.",
    )
