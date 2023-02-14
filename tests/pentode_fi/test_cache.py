"""
Tests for pydupfinder.pentode_fi.cache.
"""
from pathlib import Path
from unittest.mock import NonCallableMock

from pydupfinder.pentode_fi.cache import (
    _get_checksum_from_cache,  # pyright: ignore
    _store_checksum_in_cache,  # pyright: ignore
    cache_functions,
)


def test_cache_function() -> None:
    """
    Test that cache functions context manager returns expected
    functions.
    """


def test_get_checksum_from_cache() -> None:
    """
    Test that the proper command is passed to the database and the
    first result is returned.
    """
    mocked_cache = NonCallableMock()
    ret_val = mocked_cache.execute.return_value  # pyright: ignore
    ret_val.fetchone.return_value = ["foo"]  # pyright: ignore
    assert "foo" == _get_checksum_from_cache(mocked_cache, Path("barbaz"))
