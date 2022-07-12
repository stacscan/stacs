"""Defines the primary STACS CLI entrypoint.

SPDX-License-Identifier: BSD-3-Clause
"""

import logging
import os
import shutil
import sys
import time
from types import TracebackType
from typing import Callable, List

import click
import stacs


def unlink_error(function: Callable, path: str, exc_info: TracebackType):
    """Provides a mechanism to better handle failures to delete files after a run.

    Currently, this just logs out. In future we should look to fix the permissions on
    the path / parent and call func(path) to attempt the deletion again. However, we'll
    need to ensure that path is actually part of the cache directory. So for now, we
    log.
    """
    logger = logging.getLogger("stacs")
    logger.warning(f"Unable to remove {path}")


@click.command()
@click.version_option()
@click.option(
    "--debug",
    is_flag=True,
    help="Increase verbosity of logs for debugging",
)
@click.option(
    "--pretty",
    help="Display outputs in a human-readable tree, rather than SARIF.",
    is_flag=True,
)
@click.option(
    "--threads",
    help="The number of threads to use when processing files",
    default=10,
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
    "--skip-unprocessable",
    help="Skip unprocessable / corrupt archives with a warning.",
    is_flag=True,
)
@click.option(
    "--cache-directory",
    help="The path to use as a cache - used when unpacking archives.",
    default=stacs.scan.constants.CACHE_DIRECTORY,
)
@click.argument("paths", nargs=-1, required=True)
def main(
    debug: bool,
    pretty: bool,
    threads: int,
    rule_pack: str,
    ignore_list: str,
    skip_unprocessable: bool,
    cache_directory: str,
    paths: List[str],
) -> None:
    """STACS - Static Token And Credential Scanner."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s - %(process)d - [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger("stacs")
    logger.info(f"STACS running with {threads} threads")

    # Licenses.
    for project, urls in stacs.scan.constants.EXTERNAL_LICENSES.items():
        logger.info(f"STACS uses {project} (licenses may be found at {' '.join(urls)})")

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
            logger.debug(f"Loaded {len(ignored.ignore)} suppressions from ignore list.")
        except stacs.scan.exceptions.STACSException as err:
            logger.error(f"Unable to load ignore list: {err}")
            sys.exit(-1)

    # Append a timestamp to the cache directory to reduce the chance of collisions.
    cache_directory = os.path.join(cache_directory, str(int(time.time_ns() / 1000)))
    try:
        os.mkdir(cache_directory)
        logger.info(f"Using cache directory at {cache_directory}")
    except OSError as err:
        logger.error(f"Unable to create cache directory at {cache_directory}: {err}")
        sys.exit(-2)

    # Generate a list of candidate files to scan.
    targets = []

    for path in paths:
        path = os.path.abspath(os.path.expanduser(path))
        logger.info(f"Attempting to get a list of files to scan from {path}")
        try:
            targets.extend(
                stacs.scan.loader.filepath.finder(
                    path,
                    cache_directory,
                    skip_on_corrupt=skip_unprocessable,
                    workers=threads,
                )
            )
        except stacs.scan.exceptions.STACSException as err:
            logger.error(f"Unable to generate file list: {err}")
            sys.exit(-2)

    # Submit files for analysis.
    logger.info(f"Found {len(targets)} files for analysis")

    findings = []
    for scanner in stacs.scan.scanner.__all__:
        try:
            findings.extend(
                getattr(stacs.scan.scanner, scanner).run(targets, pack, workers=threads)
            )
        except stacs.scan.exceptions.InvalidFormatException as err:
            logger.error(f"Unable to load a rule in scanner {scanner}: {err}")
            continue

    # Filter findings by allow list.
    if ignored:
        findings = stacs.scan.filter.ignore_list.process(findings, ignored)

    # Clean-up cache directory.
    shutil.rmtree(cache_directory, onerror=unlink_error)

    # Determine the correct exit status based on whether there were unsuppressed
    # findings.
    exit_code = 0

    for finding in findings:
        if not finding.ignore:
            exit_code = stacs.scan.constants.EXIT_CODE_UNSUPPRESSED

    # Pretty print, if requested.
    if pretty:
        logger.info("Generating 'pretty' output from findings")
        stacs.scan.output.pretty.render(findings, pack)
        sys.exit(exit_code)

    # Default to SARIF output to STDOUT.
    logger.info("Generating SARIF from findings")
    try:
        sarif = stacs.scan.output.sarif.render(path, findings, pack)
    except stacs.scan.exceptions.STACSException as err:
        logger.error(f"Unable to generate SARIF: {err}")
        sys.exit(-3)

    # TODO: Add file output as an option.
    logger.info(f"Found {len(findings)} findings")
    print(sarif)
