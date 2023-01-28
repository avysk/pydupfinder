"""
The main body of pydupfinder.
"""
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, Optional, Set

import click

from pydupfinder.pentode_fi.cache import cache_functions
from pydupfinder.pentode_fi.filesystem import checksum, files_in_a_dir
from pydupfinder.pentode_fi.interface import (
    final_report_found_files,
    report_bad_files,
    report_duplicates,
    report_potential_duplicates,
    start_finding_potential_duplicates,
    start_finding_sizes,
)


def find_duplicates(  # pylint: disable=too-many-locals
    path: Path,
    min_duplicates: Optional[int],
    max_total_size: int,
    reset_checksum_cache: bool,
):
    """
    Find duplicate files.

    :param path: The path to search duplicates in.
    :param min_duplicates: Find AT LEAST this many duplicates if possible.
    :param max_total_size: Checksum AT MOST this amount of bytes.
    :param reset_checksum_cache: Recreate the cache database with files'
                                 checksums, effectively removing the cache.
    """
    with cache_functions(reset_checksum_cache) as (
        cached_checksum,
        store_checksum,
    ):

        # Stage 1: we are going through all the files, finding their sizes
        start_finding_sizes()
        files_by_size, bad_files = files_in_a_dir(path)
        final_report_found_files(len(files_by_size), len(bad_files))

        report_bad_files(bad_files)

        # Stage 2: finding potential duplicates, i.e. sets of files of
        # the same size. This operation does not cause OneDrive
        # download.
        start_finding_potential_duplicates()
        files_by_size = {
            size: paths
            for size, paths in files_by_size.items()
            if len(paths) > 1
        }

        stage2_sizes = sorted(files_by_size.keys(), reverse=True)
        report_potential_duplicates(len(stage2_sizes))

        # Determine the size of a progressbar
        length = min_duplicates or max_total_size
        if length is None:
            # If no limits are given, we are to process all files
            length = 0
            for size, files in files_by_size.items():
                length += size * len(files)

        # So far we did not find any duplicates and did not checksum any
        # files
        found_dups = 0
        total_size_checksummed = 0

        # The following dictionary maps the size to a set of found
        # duplicate files of this size
        found_duplicate_files: Dict[int, Set[Path]] = {}

        # Stage 3: comparing checksums
        with click.progressbar(
            length=length,
            label="Determining files' checksums",
            item_show_func=lambda _: f"Found {found_dups} duplicates",
        ) as stage3_pb:  # pyright: ignore
            for size in stage2_sizes:
                if min_duplicates and (found_dups >= min_duplicates):
                    # If there is a limit on the number of duplicates
                    # found, and we have reached it, stop.
                    break

                # Take the files of the given size
                files = files_by_size[size]
                # The following dictionary maps checksum to a set of
                # files with this checksum.
                hashes_of_files: DefaultDict[
                    Optional[str], Set[Path]
                ] = defaultdict(set)
                # Find the cached checksums
                for file in files:
                    ch_cs = cached_checksum(file)
                    hashes_of_files[ch_cs].add(file)
                # Now calculate checksums of other files, if there are
                # other files and size is not too big
                for file in hashes_of_files[None]:
                    # We are iterating through a set of files with no
                    # cached checksum.
                    if (
                        max_total_size
                        and total_size_checksummed + size > max_total_size
                    ):
                        # We cannot checksum due to the limit on the
                        # total size of files checksummed => done with
                        # this size
                        break
                    # The next line calculates the checksum of the
                    # current file.  This operation requires the file
                    # content => triggers OneDrive download.
                    cal_cs = checksum(file)
                    total_size_checksummed += size
                    store_checksum(file, cal_cs)
                    hashes_of_files[cal_cs].add(file)
                    if max_total_size:
                        # If there is a limit on the total size of files
                        # checksummed, update the progressbar
                        stage3_pb.update(size, 1)  # pyright: ignore
                # Remove files we ignored because of size limitation
                del hashes_of_files[None]

                dups = 0
                # Check if there are any duplicates.
                for identical in hashes_of_files.values():
                    dups = len(identical)
                    if dups == 1:
                        # Only one file in this checksum group => not a
                        # duplicate
                        continue
                    # We have some duplicates
                    found_dups += dups
                    found_duplicate_files[size] = identical
                if min_duplicates and dups:
                    # If there is a limit on the number of duplicates
                    # found, update the progressbar
                    stage3_pb.update(dups, 1)  # pyright: ignore
                elif not max_total_size:
                    # If there were no limits, update the progressbar
                    # with the total size
                    stage3_pb.update(size * len(files), 1)  # pyright: ignore

    # Output found duplicate files
    report_duplicates(found_duplicate_files)
