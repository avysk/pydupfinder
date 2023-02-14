"""
Utilities for working with cache database.
"""
from contextlib import contextmanager
from functools import partial
from pathlib import Path
import sqlite3
from typing import Generator, Optional, Tuple

import click


def _exists(conn: sqlite3.Connection, name: str) -> int:
    """
    Check if the given table exists.

    Given sqlite connection and the string, checks if the table with
    the given name does exist.

    :param conn: Connection to sqlite database.
    :param name: Check for existence of table with this name.
    :returns: Truthy value if the table exits, falsy (0) otherwise.
    """
    return int(
        conn.execute(
            "SELECT COUNT(*) FROM sql_schema WHERE type = 'table' AND "
            "name = ?",
            (name,),
        ).fetchone()[0]
    )


def _rename(conn: sqlite3.Connection, /, old_name: str, new_name: str) -> None:
    """
    Rename table in sqlite datbase.

    It is supposed that the table exists.

    :param conn: Connection to sqlite database.
    :param old_name: Old table name.
    :param new_name: New table name.
    """
    conn.execute("ALTER TABLE ?1 RENAME TO ?2", (old_name, new_name))


def _get_checksum_from_cache(
    sqlite_cache: sqlite3.Connection, file_path: Path
) -> Optional[str]:
    """
    Return cached checksum for file, if it does exist.

    :param sqlite_cache: The path to SQLite database with cached
                         checksums.
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

    Writes a row to SQLite table 'files' mapping the given file to the
    given checksum.

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
    Return a function for getting file checksum from the cache and the
    function for storing file checksum into the cache.

    Optionally recreates the cache. If there are no cached checsum for
    the file, the function returns None.

    :param reset_cache: The cache database is deleted and created again
                        (effectively clearing the cache) if set.
    :returns: a context manager, providing a tuple of functions for
              getting file checksum from the cache and for storing file
              checksum in the cache.
    """
    app_dir = Path(click.get_app_dir("Pydupfinder"))
    app_dir.mkdir(parents=True, exist_ok=True)
    database = app_dir / "cache.sqlite"
    if reset_cache:
        database.unlink(missing_ok=True)
    with sqlite3.connect(database) as conn:
        exist = _exists(conn, "files")
        if exist:
            conn.execute("DROP TABLE IF EXISTS cached_files")
            _rename(conn, old_name="files", new_name="cached_files")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS files "
            "(file TEXT PRIMARY KEY, checksum TEXT);"
        )
        conn_ro = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        yield (
            partial(_get_checksum_from_cache, conn_ro),
            partial(_store_checksum_in_cache, conn),
        )
