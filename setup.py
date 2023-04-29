"""Setup required for pybind11 built native code only."""

import os
import platform
import subprocess
from typing import List

from pybind11.setup_helpers import Pybind11Extension
from setuptools import setup

ext_modules = [
    Pybind11Extension(
        "stacs.native.archive",
        ["stacs/native/archive/src/archive.cpp"],
        libraries=["archive"],
    ),
]


def run(command: List[str]):
    """Run a command, returning the output as a string or an exception on failure."""
    result = subprocess.run(command, capture_output=True, check=True)
    return str(result.stdout, "utf-8").strip()


# macOS requires a bit of special handling to ensure that the - likely - brew installed
# libarchive is discoverable. The macOS built-in libarchive is no good, as it's too
# old.
if platform.system() == "Darwin":
    libarchive = run(["brew", "--cellar", "libarchive"])
    libarchive_headers = run(["find", libarchive, "-name", "include", "-type", "d"])
    libarchive_pkgconfig = run(["find", libarchive, "-name", "pkgconfig", "-type", "d"])

    # Setup the environment for the build.
    os.environ["LDFLAGS"] = f"-L{libarchive_headers}"
    os.environ["PKG_CONFIG"] = libarchive_pkgconfig
    os.environ["CPPFLAGS"] = " ".join(
        [
            os.environ.get("CPPFLAGS", ""),
            "-std=c++11",
            f"-I{libarchive_headers}",
        ]
    )

setup(ext_modules=ext_modules, packages=[])
