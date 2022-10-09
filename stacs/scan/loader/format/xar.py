"""Provides an eXtensible ARchive parser and extrator.

SPDX-License-Identifier: BSD-3-Clause
"""

import os
import struct
import xml.etree.ElementTree as ET
import zlib
from collections import namedtuple
from typing import List

from stacs.scan.constants import CHUNK_SIZE
from stacs.scan.exceptions import FileAccessException, InvalidFileException

XAR_MAGIC = b"xar!"
XAR_HEADER = ">4sHHQQI"
XAR_HEADER_SZ = struct.calcsize(XAR_HEADER)

# via xar/include/xar.h.in
XARHeader = namedtuple(
    "XARHeader",
    [
        "magic",
        "size",
        "version",
        "toc_length_compressed",
        "toc_length_uncompressed",
        "cksum_alg",
    ],
)

XAREntry = namedtuple(
    "XAREntry",
    [
        "length",
        "offset",
        "size",
        "encoding",
        "archived_cksum_kind",
        "archived_cksum",
        "path",
        "name",
        "kind",
    ],
)


class XAR:
    """Provides an eXtensible ARchive Format parser and extrator."""

    def __init__(self, filepath: str):
        self.archive = filepath

        try:
            with open(self.archive, "rb") as fin:
                # Ensure the provided file is actually a XAR.
                if fin.read(4) != XAR_MAGIC:
                    raise InvalidFileException("File does not appear to be a XAR")

                # Rewind and attempt to read in header.
                fin.seek(0)
                self._header = XARHeader._make(
                    struct.unpack(XAR_HEADER, fin.read(XAR_HEADER_SZ))
                )

                # Read and decompress the table-of-contents.
                fin.seek(self._header.size)

                self._toc = ET.fromstring(
                    str(
                        zlib.decompress(fin.read(self._header.toc_length_uncompressed)),
                        "utf-8",
                    )
                )
        except zlib.error as err:
            raise InvalidFileException(f"Unable to read table-of-contents: {err}")
        except OSError as err:
            raise FileAccessException(f"Unable to read archive: {err}")

    def _parse_entries(self, root, directory="") -> List[XAREntry]:
        """Recursively parse entries from the table-of-contents."""
        candidates = []

        # Strip any slashes, only using the last path component.
        kind = root.find(".type").text
        name = root.find(".name").text.split("/")[-1]
        path = os.path.join(directory, name)

        # Recurse for directories
        if kind == "directory":
            for element in root.findall(".//file"):
                candidates.extend(self._parse_entries(element, directory=path))

        if kind == "file":
            size = int(root.find(".//data/size").text)
            length = int(root.find(".//data/length").text)
            offset = int(root.find(".//data/offset").text)
            encoding = root.find(".//data/encoding").get("style")
            archived_cksum = root.find(".//data/archived-checksum").text
            archived_cksum_kind = root.find(".//data/archived-checksum").get("style")

            candidates.append(
                XAREntry(
                    length,
                    offset,
                    size,
                    encoding,
                    archived_cksum,
                    archived_cksum_kind,
                    path,
                    name,
                    kind,
                )
            )

        return candidates

    def entries(self) -> List[XAREntry]:
        """Return a list of entries in this XAR."""
        candidates = []

        for entry in self._toc.findall("./toc/file"):
            candidates.extend(self._parse_entries(entry))

        return candidates

    def extract(self, destination):
        """Extract all entries from the XAR to the optional destination directory."""
        # Offset must be adjusted by the size of the ToC and the header. This is as the
        # offset is from the first byte AFTER the header and compressed ToC.
        header_size = self._header.size + self._header.toc_length_compressed

        for entry in self.entries():
            parent = os.path.dirname(os.path.join(destination, entry.path))

            try:
                os.makedirs(parent, exist_ok=True)
            except OSError as err:
                raise FileAccessException(
                    f"Unable to create directory during extraction: {err}"
                )

            # Check whether a decompressor should be used.
            decompressor = None

            if entry.encoding == "application/x-gzip":
                decompressor = zlib.decompressobj(wbits=zlib.MAX_WBITS | 32).decompress

            # Perform extraction.
            # TODO: No decompression or integrity checking is performed today, nor are
            # ownership and modes followed.
            remaining = entry.length

            try:
                with open(self.archive, "rb") as fin:
                    with open(os.path.join(destination, entry.path), "wb") as fout:
                        fin.seek(header_size + entry.offset)

                        # Read all data in chunks to not balloon memory when processing
                        # large files.
                        while remaining > 0:
                            delta = remaining - CHUNK_SIZE
                            if delta < 0:
                                read_length = remaining
                            else:
                                read_length = CHUNK_SIZE

                            # Use a decompressor, if required.
                            if decompressor:
                                fout.write(decompressor(fin.read(read_length)))
                            else:
                                fout.write(fin.read(read_length))

                            remaining -= read_length
            except (OSError, zlib.error) as err:
                raise InvalidFileException(err)
