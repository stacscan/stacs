"""Defines types to assist with loading and processing of rule packs.

SPDX-License-Identifier: BSD-3-Clause
"""

import json
import os
from typing import List

from pydantic import BaseModel, Extra, Field
from stacs.exceptions import STACSException


class Entry(BaseModel, extra=Extra.forbid):
    """Defines the schema of an allow."""

    module: str = Field(
        "rules",
        title="Which module the rules are for.",
    )
    path: str = Field(
        None,
        title="The path of a the module's rule to load.",
    )


class Format(BaseModel, extra=Extra.forbid):
    """Defines the schema of the rule pack."""

    include: List[str] = Field(
        [],
        title="Define a list of additional packs to include.",
    )
    pack: List[Entry] = Field(
        [],
        title="A list of pack entries.",
    )


def from_file(filename: str) -> Format:
    """Load a pack from file, returning a rendered down and complete pack."""
    parent_file = os.path.abspath(os.path.expanduser(filename))
    parent_path = os.path.dirname(os.path.abspath(os.path.expanduser(filename)))

    # Load the parent pack, and then recurse as needed to handle includes.
    try:
        with open(parent_file, "r") as fin:
            parent_pack = Format(**json.load(fin))

        # Roll over the pack and ensure any entries are fully qualified.
        for index, entry in enumerate(parent_pack.pack):
            if not entry.path.startswith("/"):
                # Resolve the path.
                qualified = Entry(
                    path=os.path.join(parent_path, entry.path),
                    module=entry.module,
                )

                # Swap the entry with one that's fully qualified.
                del parent_pack.pack[index]
                parent_pack.pack.insert(index, qualified)
    except (OSError, json.JSONDecodeError) as err:
        raise STACSException(err)

    # Recursively load included packs, adding results to the loaded pack.
    for file in parent_pack.include:
        child_pack = from_file(os.path.join(parent_path, file))
        parent_pack.pack.extend(child_pack.pack)

    # Finally strip the included packs from the entry, as these have been resolved,
    # returning the loaded pack to the caller.
    parent_pack.include = []
    return parent_pack
