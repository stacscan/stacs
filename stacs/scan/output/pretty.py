import base64
from typing import List

from colorama import Fore, init
from stacs.scan import helper, model
from stacs.scan.__about__ import __version__
from stacs.scan.constants import ARCHIVE_FILE_SEPARATOR
from stacs.scan.model.finding import Sample


def generate_file_tree(virtual_path: str) -> str:
    """Returns a tree layout to the virtual path."""
    tree = str()
    parts = virtual_path.split(ARCHIVE_FILE_SEPARATOR)

    for index, part in enumerate(parts):
        # Add some style. Print a package / box before each archive, and a document
        # before the file.
        if (index + 1) == len(parts):
            emoji = "📄"
        else:
            emoji = "📦"

        tree += f"{' ' * (index * 4)}`-- {emoji} {part}\n"

    return tree.rstrip()


def generate_sample(sample: Sample):
    """Return a plain-text and text formatted sample."""
    # Ensure the sample is nicely base64 encoded if binary, rather than slapping three
    # already base64'd strings together.
    raw = bytearray()
    if sample.binary:
        raw.extend(bytearray(base64.b64decode(sample.before)))
        raw.extend(bytearray(base64.b64decode(sample.finding)))
        raw.extend(bytearray(base64.b64decode(sample.after)))

        return str(base64.b64encode(raw), "utf-8")

    return "".join([sample.before, sample.finding, sample.after])


def render(findings: List[model.finding.Entry], pack: model.pack.Format) -> str:
    """Render a 'pretty' output to the console for human consumption."""
    init()

    # Find all unsuppressed findings, and track them separately.
    results = {}
    unsuppressed = 0

    for finding in findings:
        # Check for suppressions.
        if finding.ignore is not None and finding.ignore.ignored:
            continue

        # Track it.
        unsuppressed += 1

        if results.get(finding.path) is None:
            results[finding.path] = []

        # Extract location appropriately.
        location = None
        if finding.location.line:
            location = f"line {finding.location.line}"
        else:
            location = f"{finding.location.offset}-bytes"

        # Generates all strings for presentation right away.
        results[finding.path].append(
            {
                "tree": generate_file_tree(finding.path),
                "path": finding.path.split(ARCHIVE_FILE_SEPARATOR)[-1],
                "rule": finding.source.reference,
                "text": finding.source.description,
                "location": location,
                "sample": generate_sample(finding.sample),
            }
        )

    # Provide a summary.
    print(helper.banner(version=__version__))

    if findings == 0:
        print("✨ " + Fore.GREEN + "No unsuppressed findings! Great work! ✨\n")
        return

    # Render out the findings.
    print(
        f"{Fore.RED}🔥 There were {unsuppressed} unsuppressed findings in "
        f"{len(results)} files 🔥\n"
    )

    for candidate in results:
        filepath = candidate.split(ARCHIVE_FILE_SEPARATOR)[0]
        count = len(results[candidate])

        if ARCHIVE_FILE_SEPARATOR in candidate:
            print(f"{Fore.RED}❌ {count} finding(s) inside of file {filepath} (Nested)")
        else:
            print(f"{Fore.RED}❌ {count} finding(s) inside of file {filepath}")

        for finding in results[candidate]:
            print()
            helper.printi(f"{Fore.YELLOW}Reason   : {finding['text']}")
            helper.printi(f"{Fore.YELLOW}Rule Id  : {finding['rule']}")
            helper.printi(f"{Fore.YELLOW}Location : {finding['location']}\n\n")
            helper.printi(f"{Fore.YELLOW}Filetree:\n\n")
            helper.printi(
                finding["tree"],
                prefix=f"    {Fore.RESET}|{Fore.BLUE}",
            )
            print()
            helper.printi(f"{Fore.YELLOW}Sample:\n\n")
            helper.printi(
                f"... {finding['sample']} ...",
                prefix=f"    {Fore.RESET}|{Fore.BLUE}",
            )
            print()

        print(f"\n{Fore.RESET}{'-' * 78}\n")
