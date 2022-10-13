"""Defines handlers for unpacking of archives.

SPDX-License-Identifier: BSD-3-Clause
"""

import bz2
import gzip
import hashlib
import logging
import lzma
import os
import shutil
import tarfile
import zipfile
import zlib
from typing import List, Tuple

import zstandard
from stacs.native import archive
from stacs.scan.constants import CHUNK_SIZE
from stacs.scan.exceptions import FileAccessException, InvalidFileException
from stacs.scan.loader.format import dmg, xar


def path_hash(filepath: str) -> str:
    """Returns a hash of the filepath, for use with unique directory creation."""
    return hashlib.md5(bytes(filepath, "utf-8")).hexdigest()


def zip_handler(filepath: str, directory: str) -> None:
    """Attempts to extract the provided zip archive."""
    log = logging.getLogger(__name__)

    try:
        os.mkdir(directory, mode=0o700)
    except OSError as err:
        raise FileAccessException(
            f"Unable to create unpack directory at {directory}: {err}"
        )

    # Attempt to unpack the zipfile to the new unpack directory.
    try:
        with zipfile.ZipFile(filepath, "r") as reader:
            try:
                reader.extractall(directory)
            except RuntimeError as err:
                # Encrypted zips (why is this not a custom exception?!)
                if "encrypted" in str(err):
                    log.warn(
                        f"Cannot process file in archive at {filepath}, skipping: {err}"
                    )
            except NotADirectoryError as err:
                # Broken filepaths inside of ZIP.
                log.warn(
                    f"Cannot process file in archive at {filepath}, skipping: {err}"
                )
            except (OSError, IndexError) as err:
                # Several conditions, but usually a corrupt / bad input zip.
                log.warn(
                    f"Cannot process file in archive at {filepath}, skipping: {err}"
                )
    except (zipfile.BadZipFile, OSError) as err:
        raise InvalidFileException(
            f"Unable to extract archive {filepath} to {directory}: {err}"
        )


def tar_handler(filepath: str, directory: str) -> None:
    """Attempts to extract the provided tarball."""
    try:
        os.mkdir(directory, mode=0o700)
    except OSError as err:
        raise FileAccessException(
            f"Unable to create unpack directory at {directory}: {err}"
        )

    # Attempt to unpack the tarball to the new unpack directory.
    try:
        with tarfile.open(filepath, "r") as reader:
            reader.extractall(directory)
    except (PermissionError, tarfile.TarError) as err:
        raise InvalidFileException(
            f"Unable to extract archive {filepath} to {directory}: {err}"
        )


def gzip_handler(filepath: str, directory: str) -> None:
    """Attempts to extract the provided gzip archive."""
    output = ".".join(os.path.basename(filepath).split(".")[:-1])

    # No dots? Just use the name as is.
    if len(output) < 1:
        output = os.path.basename(filepath)

    # Although gzip files cannot contain more than one file, we'll still spool into
    # a subdirectory under the cache for consistency.
    try:
        os.mkdir(directory, mode=0o700)
    except OSError as err:
        raise FileAccessException(
            f"Unable to create unpack directory at {directory}: {err}"
        )

    # TODO: This can likely be optimized for tgz files, as currently the file will be
    #       first processed and gunzipped, and then reprocessed to be extracted.
    try:
        with gzip.open(filepath, "rb") as fin:
            with open(os.path.join(directory, output), "wb") as fout:
                shutil.copyfileobj(fin, fout, CHUNK_SIZE)
    except gzip.BadGzipFile as err:
        raise InvalidFileException(
            f"Unable to extract archive {filepath} to {output}: {err}"
        )


def bzip2_handler(filepath: str, directory: str) -> None:
    """Attempts to extract the provided bzip2 archive."""
    output = ".".join(os.path.basename(filepath).split(".")[:-1])

    # No dots? Just use the name as is.
    if len(output) < 1:
        output = os.path.basename(filepath)

    # Like gzip, bzip2 cannot support more than a single file. Again, we'll spool into
    # a subdirectory for consistency.
    try:
        os.mkdir(directory, mode=0o700)
    except OSError as err:
        raise FileAccessException(
            f"Unable to create unpack directory at {directory}: {err}"
        )

    # TODO: This can likely be optimized for tbz files, as currently the file will be
    #       first processed and gunzipped, and then reprocessed to be extracted.
    try:
        with bz2.open(filepath, "rb") as fin:
            with open(os.path.join(directory, output), "wb") as fout:
                shutil.copyfileobj(fin, fout, CHUNK_SIZE)
    except (OSError, ValueError) as err:
        raise InvalidFileException(
            f"Unable to extract archive {filepath} to {output}: {err}"
        )


def zstd_handler(filepath: str, directory: str) -> None:
    """Attempts to extract the provided zstd archive."""
    output = ".".join(os.path.basename(filepath).split(".")[:-1])

    # No dots? Just use the name as is.
    if len(output) < 1:
        output = os.path.basename(filepath)

    # zstd does not appear to provide a native mechanism to compress multiple files,
    # and recommend 'to combine zstd with tar'.
    try:
        os.mkdir(directory, mode=0o700)
    except OSError as err:
        raise FileAccessException(
            f"Unable to create unpack directory at {directory}: {err}"
        )

    try:
        decompressor = zstandard.ZstdDecompressor()

        with open(filepath, "rb") as fin:
            with open(os.path.join(directory, output), "wb") as fout:
                decompressor.copy_stream(fin, fout, read_size=CHUNK_SIZE)
    except (OSError, ValueError, zstandard.ZstdError) as err:
        raise InvalidFileException(
            f"Unable to extract archive {filepath} to {output}: {err}"
        )


def lzma_handler(filepath: str, directory: str) -> None:
    """Attempts to extract the provided xz / lzma archive."""
    output = ".".join(os.path.basename(filepath).split(".")[:-1])

    # No dots? Just use the name as is.
    if len(output) < 1:
        output = os.path.basename(filepath)

    # Although xz files cannot contain more than one file, we'll still spool into
    # a subdirectory under the cache for consistency.
    try:
        os.mkdir(directory, mode=0o700)
    except OSError as err:
        raise FileAccessException(
            f"Unable to create unpack directory at {directory}: {err}"
        )

    try:
        with lzma.open(filepath, "rb") as fin:
            with open(os.path.join(directory, output), "wb") as fout:
                shutil.copyfileobj(fin, fout, CHUNK_SIZE)
    except lzma.LZMAError as err:
        raise InvalidFileException(
            f"Unable to extract archive {filepath} to {output}: {err}"
        )


def zlib_handler(filepath: str, directory: str) -> None:
    """Attempts to extract the provided zlib archive."""
    output = ".".join(os.path.basename(filepath).split(".")[:-1])

    # No dots? Just use the name as is.
    if len(output) < 1:
        output = os.path.basename(filepath)

    try:
        os.mkdir(directory, mode=0o700)
    except OSError as err:
        raise FileAccessException(
            f"Unable to create unpack directory at {directory}: {err}"
        )

    try:
        decompressor = zlib.decompressobj(wbits=zlib.MAX_WBITS)

        with open(filepath, "rb") as fin:
            with open(os.path.join(directory, output), "wb") as fout:
                while compressed := fin.read(CHUNK_SIZE):
                    fout.write(decompressor.decompress(compressed))
    except zlib.error as err:
        raise InvalidFileException(
            f"Unable to extract archive {filepath} to {output}: {err}"
        )


def xar_handler(filepath: str, directory: str) -> None:
    """Attempts to extract the provided XAR archive."""
    try:
        os.mkdir(directory, mode=0o700)
    except OSError as err:
        raise FileAccessException(
            f"Unable to create unpack directory at {directory}: {err}"
        )

    # Attempt to unpack the archive.
    try:
        archive = xar.XAR(filepath)
        archive.extract(directory)
    except FileAccessException as err:
        raise FileAccessException(
            f"Unable to extract archive {filepath} to {directory}: {err}"
        )
    except InvalidFileException as err:
        raise InvalidFileException(
            f"Unable to extract archive {filepath} to {directory}: {err}"
        )


def dmg_handler(filepath: str, directory: str) -> None:
    """Attempts to extract the provided DMG archive."""
    try:
        os.mkdir(directory, mode=0o700)
    except OSError as err:
        raise FileAccessException(
            f"Unable to create unpack directory at {directory}: {err}"
        )

    # Attempt to unpack the archive.
    try:
        archive = dmg.DMG(filepath)
        archive.extract(directory)
    except FileAccessException as err:
        raise FileAccessException(
            f"Unable to extract archive {filepath} to {directory}: {err}"
        )
    except InvalidFileException as err:
        raise InvalidFileException(
            f"Unable to extract archive {filepath} to {directory}: {err}"
        )


def libarchive_handler(filepath: str, directory: str) -> None:
    """Attempts to extract the provided archive with libarchive."""
    try:
        os.mkdir(directory, mode=0o700)
    except OSError as err:
        raise FileAccessException(
            f"Unable to create unpack directory at {directory}: {err}"
        )

    # Attempt to unpack the archive to the new unpack directory.
    try:
        with archive.ArchiveReader(filepath) as reader:
            for entry in reader:
                member = entry.filename
                member = member.lstrip("../")
                member = member.lstrip("./")

                if entry.filename == ".":
                    continue

                destination = os.path.join(directory, member)
                parent = os.path.dirname(destination)

                # Handle odd cases where a file was created where a directory needs to
                # be.
                if os.path.exists(parent) and os.path.isfile(parent):
                    os.unlink(parent)

                if os.path.isdir(destination):
                    continue

                # Create parent directories, as required.
                if not os.path.isdir(parent):
                    os.makedirs(parent)

                # If the entry is a directory, create it and move on.
                if entry.isdir:
                    os.makedirs(destination, exist_ok=True)
                    continue

                with open(destination, "wb") as fout:
                    while True:
                        chunk = reader.read()
                        if len(chunk) > 0:
                            fout.write(chunk)
                            continue
                        break
    except archive.ArchiveError as err:
        raise InvalidFileException(
            f"Unable to extract archive {filepath} to {directory}: {err}"
        )


def get_mimetype(chunk: bytes, start: bool) -> List[Tuple[int, str]]:
    """Attempts to locate the appropriate handler for a given file.

    This may fail if the required "magic" is at an offset greater than the CHUNK_SIZE.
    However, currently this is not an issue, but may need to be revisited later as more
    archive types are supported.

    The start flag is used to indicate whether the current chunk is from the start of
    the file, or the end of the file. Today we only support checking the first and last
    chunk.

    Returns a list of weights and MIME types as a tuple. This weight is specified by
    handlers and is used to allow "container" formats, which may contain multiple other
    files of various matching types, to "win" the match - due to a higher weight.
    """
    for name, options in MIME_TYPE_HANDLERS.items():
        offset = options["offset"]
        magic = options["magic"]

        # If looking at the last chunk, only use negative offsets. This is to prevent
        # false positives as position 0 in the last chunk is actually N bytes into the
        # file. This is especially problematic for formats with short magic numbers,
        # such as zlib.
        if not start and offset >= 0:
            continue

        # TODO: How to handle multiple matches in the same chunk? Is this this likely?
        for format in magic:
            if chunk[offset : (offset + len(format))] == format:  # noqa: E203
                return (options["weight"], name)

    return (0, None)


# Define all supported archives and their handlers. As we currently only support a small
# list of types we can just define file magic directly here, rather than use an external
# library. This removes the need for dependencies which may have other system
# dependencies - such as libmagic. It should also provide a small a speed up during
# unpacking, as we're only looking for a small number of types.
MIME_TYPE_HANDLERS = {
    "application/x-tar": {
        "weight": 1,
        "offset": 257,
        "magic": [
            bytearray([0x75, 0x73, 0x74, 0x61, 0x72]),
        ],
        "handler": tar_handler,
    },
    "application/gzip": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0x1F, 0x8B]),
        ],
        "handler": gzip_handler,
    },
    "application/x-bzip2": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0x42, 0x5A, 0x68]),
        ],
        "handler": bzip2_handler,
    },
    "application/zip": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0x50, 0x4B, 0x03, 0x04]),
            bytearray([0x50, 0x4B, 0x05, 0x06]),
            bytearray([0x50, 0x4B, 0x07, 0x08]),
        ],
        "handler": zip_handler,
    },
    "application/zlib": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0x78, 0x01]),
            bytearray([0x78, 0x5E]),
            bytearray([0x78, 0x9C]),
            bytearray([0x78, 0xDA]),
        ],
        "handler": zlib_handler,
    },
    "application/x-xz": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0xFD, 0x37, 0x7A, 0x58, 0x5A, 0x00]),
        ],
        "handler": lzma_handler,
    },
    "application/x-rpm": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0xED, 0xAB, 0xEE, 0xDB]),
        ],
        "handler": libarchive_handler,
    },
    "application/x-iso9660-image": {
        "weight": 1,
        "offset": 0x8001,
        "magic": [
            bytearray([0x43, 0x44, 0x30, 0x30, 0x31]),
        ],
        "handler": libarchive_handler,
    },
    "application/x-7z-compressed": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0x37, 0x7A, 0xBC, 0xAF, 0x27, 0x1C]),
        ],
        "handler": libarchive_handler,
    },
    "application/x-cpio": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0xC7, 0x71]),  # 070707 in octal (Little Endian).
            bytearray([0x71, 0xC7]),  # 070707 in octal (Big Endian).
            bytearray([0x30, 0x37, 0x30, 0x37, 0x30, 0x31]),  # "070701"
            bytearray([0x30, 0x37, 0x30, 0x37, 0x30, 0x32]),  # "070702"
            bytearray([0x30, 0x37, 0x30, 0x37, 0x30, 0x37]),  # "070707"
        ],
        "handler": libarchive_handler,
    },
    "application/x-xar": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0x78, 0x61, 0x72, 0x21]),
        ],
        "handler": xar_handler,
    },
    "application/vnd.ms-cab-compressed": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0x4D, 0x53, 0x43, 0x46]),
        ],
        "handler": libarchive_handler,
    },
    "application/x-archive": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0x21, 0x3C, 0x61, 0x72, 0x63, 0x68, 0x3E]),
        ],
        "handler": libarchive_handler,
    },
    "application/vnd.rar": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0x52, 0x61, 0x72, 0x21, 0x1A, 0x07]),
        ],
        "handler": libarchive_handler,
    },
    "application/zstd": {
        "weight": 1,
        "offset": 0,
        "magic": [
            bytearray([0x28, 0xB5, 0x2F, 0xFD]),
        ],
        "handler": zstd_handler,
    },
    "application/x-apple-diskimage": {
        "weight": 2,  # "container" formats are weighted higher.
        "offset": -512,
        "magic": [
            bytearray([0x6B, 0x6F, 0x6C, 0x79]),
        ],
        "handler": dmg_handler,
    },
}
