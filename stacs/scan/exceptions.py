"""STACS Exceptions.

SPDX-License-Identifier: BSD-3-Clause
"""


class STACSException(Exception):
    """The most generic form of exception raised by STACS."""


class FileAccessException(STACSException):
    """Indicates an error occured while attempting to access a file."""


class InvalidFileException(STACSException):
    """Indicates the format of a file did not match what was expected."""


class InvalidFormatException(STACSException):
    """Indicates that the format of a rule did not match what was expected."""


class IgnoreListException(STACSException):
    """Indicates an invalid ignore list was provided."""


class NotImplementedException(STACSException):
    """Indicates that the requested method has not been implemented."""
