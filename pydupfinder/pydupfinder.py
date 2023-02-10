"""
Command processor.
"""

from pathlib import Path
from typing import Optional

import click
from click_option_group import MutuallyExclusiveOptionGroup


from pydupfinder.pentode_fi.body import find_duplicates
from pydupfinder.pentode_fi.number import parse_size

LIMITS = MutuallyExclusiveOptionGroup(
    "Limits", help="Limits for found duplicates"
)


@click.command()
@click.argument("path", type=click.Path(exists=True))
@LIMITS.option(  # type: ignore
    "--minimal-number-of-duplicates",
    "-n",
    "min_duplicates",
    help="Find AT LEAST that many duplicates if there are enough duplicates.",
    type=click.IntRange(min=2),
)
@LIMITS.option(  # type: ignore
    "--max-total-size-of-checksummed files",
    "-t",
    "max_total_size",
    help="Calculate checksums for AT MOST this total size of files.",
    callback=parse_size,
)
@click.option(
    "--reset-checksum-cache",
    "-r",
    "reset_checksum_cache",
    is_flag=True,
    default=False,
    help="Remove database, caching checksums",
)
def duplicate_finder(
    path: str,
    min_duplicates: Optional[int],
    max_total_size: int,
    reset_checksum_cache: bool,
):
    """
    Find duplicate files.
    """
    real_path = Path(path).resolve()
    click.echo(
        click.style(
            f"Pydupfinder started, searching for duplicates in '{path}'.",
            fg="green",
        )
    )
    if max_total_size:
        click.echo(
            click.style(
                f"Checksumming at most {max_total_size} bytes.", fg="green"
            )
        )
    if min_duplicates:
        click.echo(
            click.style(
                f"Trying to find at least {min_duplicates} duplicates.",
                fg="green",
            )
        )
    if reset_checksum_cache:
        click.echo(click.style("Checksum cache will be reset.", fg="green"))
    find_duplicates(
        real_path, min_duplicates, max_total_size, reset_checksum_cache
    )
