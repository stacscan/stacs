"""Implements a rules based scanner for STACS.

SPDX-License-Identifier: BSD-3-Clause
"""

import base64
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import yara
from stacs.scan.constants import CHUNK_SIZE, WINDOW_SIZE
from stacs.scan.exceptions import FileAccessException, InvalidFormatException
from stacs.scan.loader import archive
from stacs.scan.model import finding, manifest, pack


def is_binary(target: manifest.Entry) -> bool:
    """Attempts to determine if a target file is binary."""
    # This is a bit false positive prone, as some "application" mime types are text.
    # However, as we only support a finite number of formats, we should be safe to do
    # this (for now!)
    binary_types = (
        "application",
        "image",
        "audio",
        "video",
    )
    if target.mime and target.mime.startswith(binary_types):
        return True

    # Otherwise, we'll try and read some data as text and see. This could fail if a
    # binary contained readable text for 10 * CHUNK_SIZE.
    try:
        with open(target.path, "r") as fin:
            for _ in range(0, 10):
                fin.read(CHUNK_SIZE)
    except UnicodeDecodeError:
        return True

    # Define to text.
    return False


def generate_sample(target: manifest.Entry, offset: int, size: int) -> finding.Sample:
    """Generates a sample for a finding."""
    binary = is_binary(target)

    before = bytes()
    after = bytes()
    entry = bytes()

    try:
        # Make sure we don't try and read past the beginning and end of the file.
        target_sz = os.stat(target.path).st_size

        if offset - WINDOW_SIZE < 0:
            before_sz = offset
            before_offset = 0
        else:
            before_sz = WINDOW_SIZE
            before_offset = offset - before_sz

        if offset + WINDOW_SIZE > target_sz:
            after_sz = target_sz - offset
            after_offset = after_sz
        else:
            after_sz = WINDOW_SIZE
            after_offset = offset + after_sz

        with open(target.path, "rb") as fin:
            # Seek to and read in the context before.
            fin.seek(before_offset)
            before = fin.read(before_sz)

            # Read the finding match itself. We have this already from yara, but we're
            # already here so we may as well.
            fin.seek(offset)
            entry = fin.read(size)

            # Seek to and read in the context after the finding.
            fin.seek(after_offset)
            after = fin.read(after_sz)
    except OSError as err:
        raise FileAccessException(err)

    if binary:
        return finding.Sample(
            window=WINDOW_SIZE,
            before=base64.b64encode(before),
            after=base64.b64encode(after),
            finding=base64.b64encode(entry),
            binary=binary,
        )
    else:
        return finding.Sample(
            window=WINDOW_SIZE,
            before=str(before, "utf-8"),
            after=str(after, "utf-8"),
            finding=str(entry, "utf-8"),
            binary=binary,
        )


def generate_location(target: manifest.Entry, offset: int) -> finding.Location:
    """Generates a location for a finding."""
    # If the file is binary, we can't generate a line number so we already have the data
    # we need.
    if is_binary(target):
        return finding.Location(offset=offset)

    # Attempt to generate a line number for the finding.
    bytes_read = 0
    line_number = 0
    try:
        with open(target.path, "r") as fin:
            # Read in chunks, counting the number of newline characters up to the chunk
            # which includes the finding.
            while bytes_read < offset:
                bytes_read += CHUNK_SIZE

                if bytes_read > offset:
                    line_number += fin.read(offset).count("\n")
                else:
                    line_number += fin.read(CHUNK_SIZE).count("\n")
    except OSError as err:
        raise FileAccessException(err)

    return finding.Location(offset=offset, line=line_number)


def generate_findings(target: manifest.Entry, match: yara.Match) -> List[finding.Entry]:
    """Attempts to create findings based on matches inside of the target file."""
    findings = []

    # Generate a new finding entry for each matched string. This is in order to ensure
    # that multiple findings in the same file are listed separately - as they may be
    # different credentials.
    for offset, _, entry in match.strings:
        location = generate_location(target, offset)
        sample = generate_sample(target, offset, len(entry))

        # Add on information about the origin of the finding (that's us!)
        source = finding.Source(
            module=__name__,
            reference=match.meta.get("name", "UNKNOWN"),
            version=match.meta.get("version", "UNKNOWN"),
            description=match.meta.get("description"),
        )
        findings.append(
            finding.Entry(
                md5=target.md5,
                path=target.overlay if target.overlay else target.path,
                confidence=match.meta.get("accuracy", 50),
                source=source,
                sample=sample,
                location=location,
            )
        )

    return findings


def matcher(target: manifest.Entry, ruleset: yara.Rules) -> List[finding.Entry]:
    findings = []

    for match in ruleset.match(target.path):
        findings.extend(generate_findings(target, match))

    return findings


def run(
    targets: List[manifest.Entry],
    pack: pack.Format,
    workers: int = 10,
    skip_on_eacces: bool = True,
) -> List[finding.Entry]:
    """
    Executes the rules based matcher on all input files, returning a list of finding
    Entry objects.
    """
    findings = []

    # Load and compile all YARA rules up front.
    namespaces = dict()

    for rule in pack.pack:
        namespace = hashlib.md5(bytes(rule.path, "utf-8")).hexdigest()
        namespaces[namespace] = rule.path

    try:
        ruleset = yara.compile(filepaths=namespaces)
    except yara.Error as err:
        raise InvalidFormatException(err)

    # Run the matcher in a thread pool as we're likely to be I/O bound.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = []

        # Reject any input files which are supported archives. This is as we should have
        # unpacked versions of these to process, which allows matching the specific file
        # with a finding, rather than a finding on an archive.
        #
        # NOTE: Credentials stuffed into metadata of supported archive formats which
        #       support archive metadata (such as Zip's "Extra") will not be found.
        #
        for target in targets:
            if target.mime not in archive.MIME_TYPE_HANDLERS:
                futures.append(pool.submit(matcher, target, ruleset))

        for future in as_completed(futures):
            try:
                findings.extend(future.result())
            except FileAccessException:
                if not skip_on_eacces:
                    raise

    return findings
