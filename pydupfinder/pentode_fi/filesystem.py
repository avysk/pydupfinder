"""
The functions for performing file operations.
"""
from collections import defaultdict
import hashlib
from pathlib import Path
from typing import DefaultDict, Dict, Generator, Set, Tuple

from pydupfinder.pentode_fi.interface import report_found_files


def checksum(file_path: Path) -> str:
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

    # to do we can get an exception here
    return file_hash


def _find_files_in_path(path: Path) -> Generator[Path, None, None]:
    """
    Generate files in the given path.

    :path: The path to search files in.
    :returns: Generator object, yielding Path objects for found files.
    """
    return (p for p in path.rglob("*") if p.is_file())


def files_in_a_dir(path: Path) -> Tuple[Dict[int, Set[Path]], Set[Path]]:
    """
    Find sizes of files in the given directory.

    :param path: The directory to process.
    :returns: The tuple of dictionary, mapping the sizes to the set of
              Path objects, representing the files of this size, and
              the set of Path objects, representing the files, for
              which  the size could not be detrmined.
    """
    files_by_size: DefaultDict[int, Set[Path]] = defaultdict(set)
    bad_files: Set[Path] = set()

    files_found = 0
    for file_path in _find_files_in_path(path):
        files_found += 1
        report_found_files(files_found)
        try:
            stat = file_path.stat()
        except Exception:  # pylint: disable=broad-except
            bad_files.add(file_path)
            continue
        files_by_size[stat.st_size].add(file_path)

    report_found_files(files_found, unconditionally=True)

    return (files_by_size, bad_files)
