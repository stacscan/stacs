"""STACS Setup.

SPDX-License-Identifier: BSD-3-Clause
"""

import os

from setuptools import find_namespace_packages, setup

# Explicitly pull in the contents of our package's __about__ file due to constraints on
# the previous STACS structure.
__uri__ = None
__title__ = None
__version__ = None

about_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "stacs/scan/__about__.py",
)
exec(open(about_file).read())

# Defer to setupmeta.
setup(
    name=__title__,
    setup_requires="setupmeta",
    description="Static Token And Credential Scanner.",
    packages=find_namespace_packages(include=["stacs.*"]),
    url=__uri__,
    version=__version__,
)
