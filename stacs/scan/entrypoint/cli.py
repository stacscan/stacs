"""Defines the primary STACS CLI entrypoint.

SPDX-License-Identifier: BSD-3-Clause
"""

import logging
import os
import sys

import click
import stacs


@click.command()
@click.version_option()
@click.option(
    "--debug",
    is_flag=True,
    help="Increase verbosity of logs for debugging",
)
@click.option(
    "--rule-pack",
    help="The path to the rule pack to load.",
    default="~/.stacs/pack.json",
)
@click.option(
    "--ignore-list",
    help="The path to the ignore list to load (if required).",
)
@click.option(
    "--cache-directory",
    help="The path to use as a cache - used when unpacking archives.",
    default=stacs.scan.constants.CACHE_DIRECTORY,
)
@click.argument("path")
def main(
    debug: bool,
    rule_pack: str,
    ignore_list: str,
    cache_directory: str,
    path: str,
) -> None:
    """STACS - Static Token And Credential Scanner."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s - %(process)d - [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger("stacs")

    # Expand the input path.
    path = os.path.abspath(os.path.expanduser(path))

    # Load the rule pack.
    logger.info(f"Attempting to load rule pack from {rule_pack}")
    try:
        pack = stacs.scan.model.pack.from_file(rule_pack)
    except stacs.scan.exceptions.STACSException as err:
        logger.error(f"Unable to load rule pack: {err}")
        sys.exit(-1)

    # Load the ignore list.
    ignored = []
    if ignore_list:
        logger.info(f"Attempting to load ignore list from {ignore_list}")
        try:
            ignored = stacs.scan.model.ignore_list.from_file(ignore_list)
        except stacs.scan.exceptions.STACSException as err:
            logger.error(f"Unable to load ignore list: {err}")
            sys.exit(-1)

    # Generate a list of candidate files to scan.
    logger.info(f"Attempting to get a list of files to scan from {path}")
    try:
        targets = stacs.scan.loader.filepath.finder(path, cache_directory)
    except stacs.scan.exceptions.STACSException as err:
        logger.error(f"Unable to generate file list: {err}")
        sys.exit(-2)

    # Submit files for analysis.
    logger.info(f"Found {len(targets)} files for analysis")

    findings = []
    for scanner in stacs.scan.scanner.__all__:
        try:
            findings.extend(getattr(stacs.scan.scanner, scanner).run(targets, pack))
        except stacs.scan.exceptions.InvalidFormatException as err:
            logger.error(f"Unable to load a rule in scanner {scanner}: {err}")
            continue

    # Filter findings by allow list.
    if ignored:
        findings = stacs.scan.filter.ignore_list.process(findings, ignored)

    # Generate SARIF and output to STDOUT.
    logger.info("Generating SARIF from findings")
    try:
        sarif = stacs.scan.output.sarif.render(path, findings, pack)
    except stacs.scan.exceptions.STACSException as err:
        logger.error(f"Unable to generate SARIF: {err}")
        sys.exit(-3)

    # TODO: Add file output as an option.
    logger.info(f"Found {len(findings)} findings")
    print(sarif)
