"""Define helpers commonly used throughout STACS.

SPDX-License-Identifier: BSD-3-Clause
"""
from typing import List

import colorama
from stacs.scan.constants import ARCHIVE_FILE_SEPARATOR
from stacs.scan.exceptions import NoParentException


def generate_virtual_path(
    finding: "Finding",  # noqa: F821
    artifacts: "List[Artifact]",  # noqa: F821
):
    """Generate a virtual path for an input file."""
    virtual_path = finding.filepath

    try:
        parent = artifacts[finding.artifact].parent

        while True:
            name = artifacts[parent].filepath
            virtual_path = f"{name}{ARCHIVE_FILE_SEPARATOR}{virtual_path}"

            parent = artifacts[parent].parent
    except NoParentException:
        return virtual_path


def printi(string, indent: int = 4, prefix: str = None):
    """Super janky wrapper to print something indented."""
    for line in string.splitlines():
        if prefix:
            print(f"{prefix}", end="")

        print(f"{' ' * indent}" + line)


def banner(version: str) -> str:
    """Returns a STACS console banner."""
    banner = colorama.Fore.BLUE
    banner += rf"""
    ______________   ___________
   / ___/_  __/   | / ____/ ___/
   \__ \ / / / /| |/ /    \__ \
  ___/ // / / ___ / /___ ___/ /
 /____//_/ /_/  |_\____//____/

       STACS version {version}
    """
    return banner
