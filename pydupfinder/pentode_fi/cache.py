"""
Utilities for working with cache database.
"""
from contextlib import contextmanager
from functools import partial
from pathlib import Path
import sqlite3
from typing import Generator, Optional, Tuple

import click


def _get_checksum_from_cache(
    sqlite_cache: sqlite3.Connection, file_path: Path
) -> Optional[str]:
    """
    Return cached checksum for file, if it does exist.

    :param sqlite_cache: The path to SQLite database with cached checksums.
    :param file_path: The absolute path to file to find checksum for.
    :returns: Cached checksum, if found in the cache, None otherwise.
    """
    res = sqlite_cache.execute(
        "SELECT checksum FROM files WHERE file = ?;", (str(file_path),)
    ).fetchone()
    return res[0] if res else None


def _store_checksum_in_cache(
    sqlite_cache: sqlite3.Connection, file_path: Path, file_hash: str
) -> None:
    """
    Store checksum for file in the cache.

    Writes a row to SQLite table 'files' mapping the given file to the given
    checksum.

    """
    sqlite_cache.execute(
        "INSERT INTO files VALUES(:path, :checksum);",
        {"path": str(file_path), "checksum": file_hash},
    )


@contextmanager
def cache_functions(
    reset_cache: bool,
) -> Generator[Tuple[partial[Optional[str]], partial[None]], None, None]:
    """
    Return a function for getting file checksum from the cache and the function
    for storing file checksum into the cache.

    Optionally recreates the cache. If there are no cached checsum for the
    file, the function returns None.

    :param reset_cache: The cache database is deleted and created again
                        (effectively clearing the cache) if set.
    :returns: a context manager, providing a tuple of functions for getting
              file checksum from the cache and for storing file checksum in the
              cache.
    """
    app_dir = Path(click.get_app_dir("Pydupfinder"))
    app_dir.mkdir(parents=True, exist_ok=True)
    database = app_dir / "cache.sqlite"
    if reset_cache:
        database.unlink(missing_ok=True)
    with sqlite3.connect(database) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS files "
            "(file TEXT PRIMARY KEY, checksum TEXT);"
        )
        conn_ro = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        yield (
            partial(_get_checksum_from_cache, conn_ro),
            partial(_store_checksum_in_cache, conn),
        )
