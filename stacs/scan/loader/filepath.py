"""Defines a file path loader for STACS.

SPDX-License-Identifier: BSD-3-Clause
"""

import hashlib
import logging
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from stacs.scan.constants import ARCHIVE_FILE_SEPARATOR, CHUNK_SIZE
from stacs.scan.exceptions import FileAccessException
from stacs.scan.loader import archive
from stacs.scan.model.manifest import Entry

logger = logging.getLogger(__name__)


def metadata(filepath: str, overlay: str = None) -> Entry:
    """Generates a hash and determines the mimetype of the input file."""
    md5 = hashlib.md5()
    mime = None

    # Read the file in chunks.
    try:
        with open(filepath, "rb") as fin:
            while chunk := fin.read(CHUNK_SIZE):
                md5.update(chunk)

                # Only attempt to determine the filetype on the first chunk.
                if not mime and fin.tell() <= CHUNK_SIZE:
                    mime = archive.get_mimetype(chunk)
    except OSError as err:
        raise FileAccessException(f"Unable to open file at {filepath}: {err}")

    return Entry(
        path=filepath,
        md5=md5.hexdigest(),
        mime=mime,
        overlay=overlay,
    )


def walker(path: str, skip_on_eacces: bool) -> List[str]:
    """Recursively walk a file path, returning a list of all files."""
    entries = []

    # TODO: Would moving walker to a generator yield a performance increase, or lead to
    #       higher disk contention due to the hasher running at the same time?
    try:
        with os.scandir(path) as scan:
            for handle in scan:
                try:
                    # Recurse on directories, but not symlinks.
                    if handle.is_dir() and not handle.is_symlink():
                        entries.extend(walker(handle.path, skip_on_eacces))

                    # Track files, but not symlinks.
                    if handle.is_file() and not handle.is_symlink():
                        entries.append(handle.path)
                except PermissionError:
                    if not skip_on_eacces:
                        raise
                except OSError:
                    # This is usually due to too many levels of symlinks. However, other
                    # cases are likely with a large enough input.
                    continue
    except NotADirectoryError:
        entries.append(path)

    return list(set(entries))


def qualify(path: str) -> str:
    """Add the scheme to a file path, if required."""
    if path.startswith("/"):
        return f"file://{path}"
    else:
        return path


def finder(
    path: str,
    cache: str,
    workers: int = 10,
    skip_on_eacces: bool = True,
) -> List[Entry]:
    """Processes the input path, returning a list of all files and their hashes."""
    entries = []
    futures = dict()

    # Run the metadata enumerator in a thread pool as we're likely to be I/O bound.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(metadata, file): file for file in walker(path, skip_on_eacces)
        }

        # A loop and counter is used here to ensure that additional work which may be
        # submitted during the 'final loop' isn't accidentally ignored.
        while True:
            complete = 0
            for future in as_completed(futures):
                complete += 1

                try:
                    result = future.result()
                except FileAccessException:
                    if not skip_on_eacces:
                        raise

                # Track the result and then remove the future from the initial futures
                # list so that these results aren't returned again next iteration.
                entries.append(result)
                del futures[future]

                # Check it the file was found to be an archive, and if so, unpack it.
                handler = archive.MIME_TYPE_HANDLERS.get(result.mime, {}).get("handler")
                if not handler:
                    continue

                # Remove any existing previously unpacked files, then unpack the archive
                # and submit extracted files back into the queue. This is to allow for
                # easy recursive unpacking of nested archives.
                destination = os.path.join(cache, archive.path_hash(result.path))
                shutil.rmtree(destination, ignore_errors=True)

                handler(result.path, destination)
                for file in walker(destination, skip_on_eacces):
                    # The overlay path is a 'virtual' path that is constructed based on
                    # the archive the file appears inside of, and the path of the file
                    # inside of the archive. However, as archives may be nested, we need
                    # to check whether we already have an overlay and, if set, use that
                    # value instead.
                    if result.overlay:
                        parent = result.overlay
                    else:
                        parent = result.path

                    overlay = (
                        f"{parent}"
                        f"{ARCHIVE_FILE_SEPARATOR}"
                        f"{re.sub(rf'^{destination}/?', '', file)}"
                    )

                    # Submit back to the pool for processing.
                    submission = pool.submit(metadata, file, overlay=overlay)
                    futures[submission] = file

            if complete == 0:
                break

    return entries
