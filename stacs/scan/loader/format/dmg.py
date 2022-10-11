"""Provides an Apple Disk Image (DMG) parser and extractor.

SPDX-License-Identifier: BSD-3-Clause
"""

import bz2
import lzma
import os
import plistlib
import struct
import zlib
from collections import namedtuple
from typing import List

from pydantic import BaseModel, Extra, Field
from stacs.scan.exceptions import FileAccessException, InvalidFileException

# Structures names and geometry are via "Demystifying the DMG File Format"
# by Jonathan Levin (http://newosxbook.com/).
DMG_HEADER_MAGIC = b"koly"
DMG_HEADER = ">4sIIIQQQQQII16sII128sQQ120sII128sIQIII"
DMG_HEADER_MAGIC_SZ = len(DMG_HEADER_MAGIC)
DMG_HEADER_SZ = struct.calcsize(DMG_HEADER)

DMG_BLOCK_TABLE_MAGIC = b"mish"
DMG_BLOCK_TABLE = ">4sIQQQIIIIIIIIII128sI"
DMG_BLOCK_TABLE_MAGIC_SZ = len(DMG_BLOCK_TABLE_MAGIC)
DMG_BLOCK_TABLE_SZ = struct.calcsize(DMG_BLOCK_TABLE)

DMG_BLOCK_CHUNK = ">I4sQQQQ"
DMG_BLOCK_CHUNK_SZ = struct.calcsize(DMG_BLOCK_CHUNK)

DMGHeader = namedtuple(
    "DMGHeader",
    [
        "signature",
        "version",
        "header_size",
        "flags",
        "running_data_fork_offset",
        "data_fork_offset",
        "data_fork_length",
        "rsrc_fork_offset",
        "rsrc_fork_length",
        "segment_number",
        "segment_count",
        "segment_id",
        "data_checksum_type",
        "data_checksum_size",
        "data_checksum",
        "xml_offset",
        "xml_length",
        "reserved_1",
        "checksum_Type",
        "checksum_Size",
        "checksum",
        "image_variant",
        "sector_count",
        "reserved_2",
        "reserved_3",
        "reserved_4",
    ],
)
DMGBlockTable = namedtuple(
    "DMGBlockTable",
    [
        "signature",
        "version",
        "sector_number",
        "sector_count",
        "data_offset",
        "buffers_needed",
        "block_descriptors",
        "reserved_1",
        "reserved_2",
        "reserved_3",
        "reserved_4",
        "reserved_5",
        "reserved_6",
        "checksum_ype",
        "checksum_ize",
        "checksum",
        "chunk_count",
    ],
)
DMGBlockChunk = namedtuple(
    "DMGBlockChunk",
    [
        "type",
        "comment",
        "sector_number",
        "sector_count",
        "compressed_offset",
        "compressed_length",
    ],
)


class DMGBlock(BaseModel, extra=Extra.forbid):
    """Expresses a DMG block entry and its chunks."""

    name: str
    chunks: List[DMGBlockChunk] = Field([])


class DMG:
    """Provides an Apple Disk Image (DMG) parser and extractor."""

    def __init__(self, filepath: str):
        self.archive = filepath

        try:
            with open(self.archive, "rb") as fin:
                # DMG metadata is at the end of the file.
                fin.seek(-DMG_HEADER_SZ, 2)

                # Ensure the provided file is actually a DMG.
                if fin.read(DMG_HEADER_MAGIC_SZ) != DMG_HEADER_MAGIC:
                    raise InvalidFileException("File does not appear to be a DMG")

                # Rewind and attempt to read in header.
                fin.seek(-DMG_HEADER_MAGIC_SZ, 1)
                self._header = DMGHeader._make(
                    struct.unpack(DMG_HEADER, fin.read(DMG_HEADER_SZ))
                )

                # Read the XML property list.
                fin.seek(self._header.xml_offset, 0)
                self._plist = plistlib.loads(fin.read(self._header.xml_length))
        except OSError as err:
            raise FileAccessException(f"Unable to read archive: {err}")

    def _parse_blocks(self) -> List[DMGBlock]:
        """Recursively parse blocks and their associated chunks."""
        candidates = []

        # Read the BLKX entries from the resource-fork section of the plist.
        for entry in self._plist.get("resource-fork", {}).get("blkx", []):
            data = entry.get("Data")
            name = entry.get("Name")

            block = DMGBlock(name=name)
            table = DMGBlockTable._make(
                struct.unpack(DMG_BLOCK_TABLE, data[0:DMG_BLOCK_TABLE_SZ])
            )

            # Extract all blocks and their associated chunks from the encoded "Data"
            # inside of the extracted plist.
            start = DMG_BLOCK_TABLE_SZ

            for _ in range(0, table.chunk_count):
                end = start + DMG_BLOCK_CHUNK_SZ
                block.chunks.append(
                    DMGBlockChunk._make(struct.unpack(DMG_BLOCK_CHUNK, data[start:end]))
                )
                start = end

            candidates.append(block)

        return candidates

    def extract(self, destination):
        """Extract all blocks from the DMG to the optional destination directory."""
        parent = os.path.basename(self.archive)

        try:
            os.makedirs(destination, exist_ok=True)
        except OSError as err:
            raise FileAccessException(
                f"Unable to create directory during extraction: {err}"
            )

        # Process each chunk inside of each block. A DMG has multiple blocks, and a
        # block has N chunks.
        for idx, block in enumerate(self._parse_blocks()):
            output = os.path.join(destination, f"{parent}.{idx}.blob")

            for chunk in block.chunks:
                # Skip Ignored, Comment, and Last blocks (respectively).
                if chunk.type in [0x00000002, 0x7FFFFFFE, 0xFFFFFFFF]:
                    continue

                try:
                    with open(self.archive, "rb") as fin, open(output, "ab") as fout:
                        fin.seek(chunk.compressed_offset)

                        # 0x80000005 - Zlib.
                        if chunk.type == 0x80000005:
                            fout.write(
                                zlib.decompress(fin.read(chunk.compressed_length))
                            )

                        # 0x80000005 - BZ2.
                        if chunk.type == 0x80000006:
                            fout.write(
                                bz2.decompress(fin.read(chunk.compressed_length))
                            )

                        # 0x80000005 - LZMA.
                        if chunk.type == 0x80000008:
                            fout.write(
                                lzma.decompress(fin.read(chunk.compressed_length))
                            )

                        # 0x00000000 - Zero Fill.
                        if chunk.type == 0x00000000:
                            fout.write(b"\x00" * chunk.compressed_length)
                            continue
                except (OSError, lzma.LZMAError, ValueError) as err:
                    raise InvalidFileException(err)
