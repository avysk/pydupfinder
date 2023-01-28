"""
Perform interface operations.
"""
from pathlib import Path
from typing import Dict, Set

import click

from pydupfinder.pentode_fi.size import human_readable_size


def start_finding_sizes():
    """
    Inform the user that the finding sizes of the files has started.
    """
    click.echo(click.style("Determining file sizes...", fg="blue"))


def start_finding_potential_duplicates():
    """
    Inform the user that the finding of potential duplicates has
    started.
    """
    click.echo(
        click.style(
            "Finding the sets of the files with the same size...",
            fg="blue",
        )
    )


def report_found_files(files_found: int, *, unconditionally: bool = False):
    """
    Inform the user how many files were found.

    :param files_found: The number of files found.
    :returns: TODO

    """
    if unconditionally or files_found % 10000 == 0:
        click.echo(click.style(f"Found: {files_found} files", fg="green"))


def final_report_found_files(sizes_found: int, found_inaccessible_files: int):
    """
    Inform the user that the given amount of file sizes and the given
    amount of inaccessible files were found.

    :param sizes_found: The amount of different filesizes found.
    :param found_inaccessible_files: The amount of inaccessible files
                                     found.
    """
    click.echo(
        click.style(
            f"Found {sizes_found} sizes and {found_inaccessible_files} "
            "non-accessible files.",
            fg="blue",
        )
    )


def report_bad_files(bad_files: Set[Path]):
    """
    Inform the user about inaccessible files.

    Does nothing if the list of inaccessible files is empty.

    :param bad_files: The list of inaccessible files.
    """
    if not bad_files:
        return

    bad_files_names = "\n".join(str(f) for f in bad_files)

    click.echo(
        click.style(f"The inaccessible files:\n{bad_files_names}", fg="red")
    )


def report_potential_duplicates(maybe_duplicates: int):
    """
    Inform the user that the given amount of potential duplicates was
    found.

    :param maybe_duplicates: The amount of potential duplicates found.
    """
    click.echo(
        click.style(f"{maybe_duplicates} potential duplicates.", fg="blue")
    )


def report_duplicates(duplicates: Dict[int, Set[Path]]):
    """
    Inform the user about finded duplicates.

    :param duplicates: The dictionary, mapping the size to the set of
                       Path objects representing found duplicates of
                       this size. It is expected that the key-value
                       pairs corresponding to bigger sizes are added
                       first.
    """
    if not duplicates:
        click.echo(click.style("No duplicates were found.", fg="blue"))
        return
    for size, identical in reversed(duplicates.items()):
        duplicate_files = "\n".join(str(p) for p in identical)
        click.echo(
            click.style(
                f"\nFound {len(identical)} duplicates of size "
                f"{human_readable_size(size)}:\n{duplicate_files}",
                fg="blue",
            )
        )
