"""Define constants commonly used throughout STACS.

SPDX-License-Identifier: BSD-3-Clause
"""

# The size of chunks to use when reading files.
CHUNK_SIZE = 65536

# The size, in bytes, of the sample window.
WINDOW_SIZE = 20

# Define the default cache directory, used to unpack archives into.
CACHE_DIRECTORY = "/tmp"

# Define the character to use when constructed paths to findings which are inside of
# archives.
ARCHIVE_FILE_SEPARATOR = "!"
