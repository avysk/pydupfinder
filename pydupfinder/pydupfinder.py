"""
Command processor.
"""

from collections import defaultdict
import hashlib
import os
from typing import DefaultDict, List, Optional

import click
from click_option_group import MutuallyExclusiveOptionGroup


LIMITS = MutuallyExclusiveOptionGroup(
    "Limits", help="Limits for found duplicates"
)


def _file_hash(fname: str) -> str:
    """
    Return hexdigest of md5 hash of the file with the given path.

    :param fname: The full path to the file.
    :returns: Hexdigest of md5 sum of the given file.
    """
    with open(fname, "rb") as file:
        file_bytes = file.read()
        return hashlib.md5(file_bytes).hexdigest()


def _parse_size(
    _ctx: click.Context,  # pyright: ignore
    _param: click.Parameter,  # pyright: ignore
    value: Optional[str],
) -> Optional[int]:
    """
    Return the value of max-size option as a string.

    Takes into acount letter suffices.

    :param _ctx: Click Context. Unused.
    :param _param: Click Parameter. Unused.
    :param value: Option value as a string.
    :returns: Option value as a number.
    :raise click.BadParameter: Exception raised if the option value cannot be
                               parsed or is non-strictly positive, to signal
                               click that the option value is not valid.
    """
    if value is None:
        return None
    if value == "":
        raise click.BadParameter(f"Cannot parse size '{value}'.")
    multiplier = {
        "k": 1024,
        "K": 1024,
        "m": 1024 * 1024,
        "M": 1024 * 1024,
        "g": 1024 * 1024 * 1024,
        "G": 1024 * 1024 * 1024,
    }.get(value[-1], 1)
    val = value
    for suffix in ["k", "m", "g"]:
        val = val.removesuffix(suffix.lower())
        val = val.removesuffix(suffix.upper())
    val = val.rstrip()
    try:
        parsed = int(val) * multiplier
        if parsed <= 0:
            raise click.BadParameter(
                f"Got value '{value}'. It must be strictly positive."
            )
        return parsed
    except ValueError:
        raise click.BadParameter(  # pylint: disable=raise-missing-from
            f"Cannot parse size '{value}'."
        )


@click.command()
@click.argument("path", type=click.Path(exists=True))
@LIMITS.option(  # type: ignore
    "--at-least",
    "-a",
    "at_least",
    help="Find AT LEAST that many duplicates if there are enough duplicates.",
    type=click.IntRange(min=2),
)
@LIMITS.option(  # type: ignore
    "--max-size",
    "-m",
    "max_size",
    help="Calculate checksums for AT MOST this total size of files.",
    callback=_parse_size,
)
def cli(  # pylint: disable=too-many-statements,too-many-branches,too-many-locals
    path: str, at_least: Optional[int], max_size: int
):
    """
    Main entry point.
    """
    click.echo(
        click.style(
            f"Pydupfinder started, searching for duplicates in '{path}'.",
            fg="green",
        )
    )
    if max_size is not None:
        click.echo(
            click.style(f"Checksumming at most {max_size} bytes.", fg="green")
        )
    if at_least is not None:
        click.echo(
            click.style(
                f"Trying to find at least {at_least} duplicates.", fg="green"
            )
        )

    bad_files: List[str] = []
    files_by_size: DefaultDict[int, List[str]] = defaultdict(list)
    stage1_files = os.walk(path)
    with click.progressbar(
        stage1_files, label="Finding files"
    ) as stage1_files_pb:  # pyright: ignore
        dirname: str
        fnames: List[str]
        for dirname, _, fnames in stage1_files_pb:  # pyright: ignore
            for file in fnames:
                fname = os.path.join(dirname, file)
                try:
                    stat = os.stat(fname)
                except Exception:  # pylint: disable=broad-except
                    bad_files.append(fname)
                    continue
                size = stat.st_size
                files_by_size[size].append(fname)

    click.echo(
        click.style(
            f"Found {len(files_by_size)} sizes and {len(bad_files)} "
            "non-accessible files.",
            fg="blue",
        )
    )

    size: int
    with click.progressbar(
        files_by_size.copy().keys(), label="Finding potential duplicates"
    ) as stage2_sizes_pb:  # pyright: ignore
        for size in stage2_sizes_pb:
            if len(files_by_size[size]) == 1:
                del files_by_size[size]
    stage2_sizes = sorted(files_by_size.keys(), reverse=True)
    click.echo(
        click.style(f"{len(stage2_sizes)} potential duplicates.", fg="blue")
    )

    length = at_least or max_size
    if length is None:
        length = 0
        for size, files in files_by_size.items():
            length += size * len(files)
    found_dups = 0
    total_size_checksummed = 0
    with click.progressbar(
        length=length, label="Checksumming files"
    ) as stage3_pb:  # pyright: ignore
        for size, files in files_by_size.items():
            if at_least and (found_dups >= at_least):
                break
            if (
                max_size
                and total_size_checksummed + len(files) * size > max_size
            ):
                # Cannot checksum these files, the total size is too big
                continue

            hashes_of_files: DefaultDict[str, List[str]] = defaultdict(list)
            for file in files:
                file_hash = _file_hash(file)
                hashes_of_files[file_hash].append(file)
                total_size_checksummed += size
                if max_size:
                    stage3_pb.update(size)  # pyright: ignore

            dups = 0
            # Check if there are any duplicates.
            for _, identical in hashes_of_files.items():
                if len(identical) == 1:
                    continue
                dups = len(identical)
                found_dups += dups
                duplicate_files = "\n".join(identical)
                click.echo(
                    click.style(
                        f"Found {dups} duplicates:\n{duplicate_files}",
                        fg="blue",
                    )
                )
            if at_least and dups:
                stage3_pb.update(dups)  # pyright: ignore
            elif not max_size:
                stage3_pb.update(size)  # pyright: ignore


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
