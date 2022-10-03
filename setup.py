"""STACS Setup.

SPDX-License-Identifier: BSD-3-Clause
"""

import os

try:
    from pybind11.setup_helpers import Pybind11Extension
except ImportError:
    from setuptools import Extension as Pybind11Extension

from setuptools import find_namespace_packages, setup

# Explicitly pull in the contents of our package's __about__ file due to constraints on
# the previous STACS structure.
__uri__ = None
__title__ = None
__author__ = None
__version__ = None

path = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(path, "stacs/scan/__about__.py")).read())

# For PyPi to use the contents of README.md
long_description = open(os.path.join(path, "README.md")).read()

ext_modules = [
    Pybind11Extension(
        "stacs.native.archive",
        ["stacs/native/archive/src/archive.cpp"],
        libraries=["archive"],
    ),
]

setup(
    name=__title__,
    description="Static Token And Credential Scanner.",
    packages=find_namespace_packages(include=["stacs.*"]),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=__uri__,
    version=__version__,
    ext_modules=ext_modules,
    setup_requires=[
        "pybind11",
    ],
    extras_require={
        "development": [
            "tox",
            "black",
            "flake8",
            "isort",
            "pybind11",
        ]
    },
    install_requires=[
        "click==8.1.3",
        "yara-python==4.2.3",
        "pydantic==1.10.2",
        "colorama==0.4.5",
        "zstandard==0.18.0",
    ],
)
