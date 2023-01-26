"""
Command processor.
"""

import hashlib
from collections import defaultdict
from functools import partial
from pathlib import Path
import sqlite3
from typing import DefaultDict, List, Optional, Set

import click
from click_option_group import MutuallyExclusiveOptionGroup

LIMITS = MutuallyExclusiveOptionGroup(
    "Limits", help="Limits for found duplicates"
)


def _create_cache(cache: Path) -> None:
    """
    Create cache database for files' checksums.

    Makes sure there is a database containg table FILES with columns FILE
    (absolute path to file) and CHECKSUM.

    :param cache: Path to the database.
    """
    with sqlite3.connect(cache) as con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS files "
            "(file TEXT PRIMARY KEY, checksum TEXT);"
        )


def _get_checksum_from_cache(
    sqlite_cache: Path, file_path: Path
) -> Optional[str]:
    """
    Return cached checksum for file, if it does exist.

    :param sqlite_cache: The path to SQLite databse with cached checksums.
    :param file_path: The absolute path to file to find checksum for.
    :returns: Cached checksum, if found in the cache, None otherwise.
    """
    with sqlite3.connect(f"file:{sqlite_cache}?mode=ro", uri=True) as con:
        res = con.execute(
            "SELECT checksum FROM files WHERE file = ?;", (str(file_path),)
        ).fetchone()
        return res[0] if res else None


def _store_checksum_in_cache(
    sqlite_cache: Path, file_path: Path, file_hash: str
):
    """
    Store checksum for file in the cache.

    Writes a row to SQLite table 'files' mapping the given file to the given
    checksum.

    """
    with sqlite3.connect(sqlite_cache) as con:
        con.execute(
            "INSERT INTO files VALUES(:path, :checksum);",
            {"path": str(file_path), "checksum": file_hash},
        )


def calculated_checksum(file_path: Path) -> str:
    """
    Return hexdigest of md5 hash of the file with the given path.

    :param file_path: The absolute path to the file.
    :param cache: The path to the database containing cache with hashes, to
                  store the calculated checksum in.
    :returns: Hexdigest of md5 sum of the given file.
    """
    with file_path.open(mode="rb") as file:
        file_bytes = file.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()

    return file_hash


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
@click.option(
    "--reset-cache",
    "-r",
    "reset_cache",
    is_flag=True,
    default=False,
    help="Remove database, caching checksums",
)
def cli(  # pylint: disable=too-many-statements,too-many-branches,too-many-locals
    path: str, at_least: Optional[int], max_size: int, reset_cache: bool
):
    """
    Find duplicate files.
    """
    app_dir = Path(click.get_app_dir("Pydupfinder"))
    app_dir.mkdir(parents=True, exist_ok=True)
    database = app_dir / "cache.sqlite"
    if reset_cache:
        database.unlink(missing_ok=True)
    _create_cache(database)
    cached_checksum = partial(_get_checksum_from_cache, database)
    store_checksum = partial(_store_checksum_in_cache, database)

    real_path = Path(path).resolve()
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

    # The following dictionary maps file size to the set of files with this
    # size
    files_by_size: DefaultDict[int, Set[Path]] = defaultdict(set)

    # The following generator has all the files in the given directory
    stage1_files = (p for p in real_path.rglob("*") if p.is_file())

    # Stage 1: we are going through all the files, finding their sizes
    click.echo(click.style("Determining file sizes...", fg="blue"))
    found_files = 0
    for file_path in stage1_files:
        found_files += 1
        if found_files % 10000 == 0:
            click.echo(click.style(f"Found: {found_files}", fg="green"))
        try:
            stat = file_path.stat()
        except Exception:  # pylint: disable=broad-except
            bad_files.append(str(file_path))
            continue
        size = stat.st_size
        files_by_size[size].add(file_path)
    click.echo(click.style(f"Found: {found_files}", fg="green"))

    click.echo(
        click.style(
            f"\nFound {len(files_by_size)} sizes and {len(bad_files)} "
            "non-accessible files.",
            fg="blue",
        )
    )

    if bad_files:
        click.echo(
            click.style(
                "The inaccessible files:\n{'\n'.join(bad_files)}", fg="red"
            )
        )

    # Stage 2: finding potential duplicates, i.e. sets of files of the same
    # size. This operation does not cause OneDrive download.
    click.echo(
        click.style(
            "Finding the sets of the files with the same size...", fg="blue"
        )
    )
    for size in files_by_size.copy().keys():
        if len(files_by_size[size]) == 1:
            # If there is only one file of the given size, we are not
            # interested in it
            del files_by_size[size]
    stage2_sizes = sorted(files_by_size.keys(), reverse=True)
    click.echo(
        click.style(f"{len(stage2_sizes)} potential duplicates.", fg="blue")
    )

    # Determine the size of a progressbar
    length = at_least or max_size
    if length is None:
        # If no limits are given, we are to process all files
        length = 0
        for size, files in files_by_size.items():
            length += size * len(files)

    # So far we did not find any duplicates and did not checksum any files
    found_dups = 0
    total_size_checksummed = 0

    # Stage 3: comparing checksums
    with click.progressbar(
        length=length, label="Checksumming files"
    ) as stage3_pb:  # pyright: ignore
        for size in stage2_sizes:
            if at_least and (found_dups >= at_least):
                # If there is a limit on the number of duplicates found, and we
                # have reached it, stop.
                break

            # Take the files of the given size
            files = files_by_size[size]
            # The following dictionary maps checksum to a set of files with
            # this checksum.
            hashes_of_files: DefaultDict[
                Optional[str], Set[Path]
            ] = defaultdict(set)
            # Find the cached checksums
            for file in files:
                ch_cs = cached_checksum(file)
                hashes_of_files[ch_cs].add(file)
            # Now calculate checksums of other files, if there are other files
            # and size is not too big
            for file in hashes_of_files[None]:
                # We are iterating through a set of files with no cached
                # checksum.
                if max_size and total_size_checksummed + size > max_size:
                    # We cannot checksum due to the limit on the total size of
                    # files checksummed => done with this size
                    break
                # The next line calculates the checksum of the current file.
                # This operation requires the file content => triggers OneDrive
                # download.
                cal_cs = calculated_checksum(file)
                total_size_checksummed += size
                store_checksum(file, cal_cs)
                hashes_of_files[cal_cs].add(file)
                if max_size:
                    # If there is a limit on the total size of files
                    # checksummed, update the progressbar
                    stage3_pb.update(size)  # pyright: ignore
            # Remove files we ignored because of size limitation
            del hashes_of_files[None]

            dups = 0
            # Check if there are any duplicates.
            for identical in hashes_of_files.values():
                dups = len(identical)
                if dups == 1:
                    # Only one file in this checksum group => not a duplicate
                    continue
                # We have some duplicates
                found_dups += dups
                duplicate_files = "\n".join(str(p) for p in identical)
                click.echo(
                    click.style(
                        f"\nFound {dups} duplicates:\n{duplicate_files}",
                        fg="blue",
                    )
                )
            if at_least and dups:
                # If there is a limit on the number of duplicates found, update
                # the progressbar
                stage3_pb.update(dups)  # pyright: ignore
            elif not max_size:
                # If there were no limits, update the progressbar with the
                # total size
                stage3_pb.update(size * len(files))  # pyright: ignore

        stage3_pb.update(length)  # pyright: ignore


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
