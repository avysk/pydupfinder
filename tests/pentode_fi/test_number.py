"""
Tests for pydupfinder.pentode_fi.number
"""
from typing import Optional
from unittest.mock import NonCallableMock

from click import BadParameter
import pytest
import pydupfinder.pentode_fi.number


@pytest.mark.parametrize(
    "string_parameter,expected_value",
    (
        (None, None),
        ("12345", 12345),
        ("12345.6", 12345),
        ("2k", 2 * 1024),
        ("2 k", 2 * 1024),
        ("2	k", 2 * 1024),
        ("2K", 2 * 1024),
        ("2 K", 2 * 1024),
        ("2	K", 2 * 1024),
        ("2.5k", 2.5 * 1024),
        ("2.5 k", 2.5 * 1024),
        ("2.5	k", 2.5 * 1024),
        ("2.5K", 2.5 * 1024),
        ("2.5 K", 2.5 * 1024),
        ("2.5	K", 2.5 * 1024),
        ("3m", 3 * 1024 * 1024),
        ("3 m", 3 * 1024 * 1024),
        ("3	m", 3 * 1024 * 1024),
        ("3M", 3 * 1024 * 1024),
        ("3 M", 3 * 1024 * 1024),
        ("3	M", 3 * 1024 * 1024),
        ("3.64m", int(3.64 * 1024 * 1024)),
        ("3.64 m", int(3.64 * 1024 * 1024)),
        ("3.64	m", int(3.64 * 1024 * 1024)),
        ("3.64M", int(3.64 * 1024 * 1024)),
        ("3.64 M", int(3.64 * 1024 * 1024)),
        ("3.64	M", int(3.64 * 1024 * 1024)),
        ("4g", 4 * 1024 * 1024 * 1024),
        ("4 g", 4 * 1024 * 1024 * 1024),
        ("4	g", 4 * 1024 * 1024 * 1024),
        ("4G", 4 * 1024 * 1024 * 1024),
        ("4 G", 4 * 1024 * 1024 * 1024),
        ("4	G", 4 * 1024 * 1024 * 1024),
        ("4.75g", 4.75 * 1024 * 1024 * 1024),
        ("4.75 g", 4.75 * 1024 * 1024 * 1024),
        ("4.75	g", 4.75 * 1024 * 1024 * 1024),
        ("4.75G", 4.75 * 1024 * 1024 * 1024),
        ("4.75 G", 4.75 * 1024 * 1024 * 1024),
        ("4.75	G", 4.75 * 1024 * 1024 * 1024),
    ),
)
def test_parsing_size(string_parameter: str, expected_value: int) -> None:
    """
    Test that size parsing works.
    """
    assert expected_value == pydupfinder.pentode_fi.number.parse_size(
        NonCallableMock(), NonCallableMock(), string_parameter
    )


@pytest.mark.parametrize(
    "argument, expected_message",
    (
        ("-113m", r"^Got value '-113m'. It must be strictly positive.$"),
        ("", r"^Cannot parse size ''.$"),
        ("100kk", r"^Cannot parse size '100kk'.$"),
    ),
)
def test_size_throws_on_incorrect_parameter(
    argument: str, expected_message: str
) -> None:
    """
    Test that incorrect size argument cannot be parsed."
    """
    with pytest.raises(BadParameter, match=expected_message):
        _: Optional[int] = pydupfinder.pentode_fi.number.parse_size(
            NonCallableMock(), NonCallableMock(), argument
        )


@pytest.mark.parametrize(
    "number,expected_representation",
    (
        (511, "511"),
        (513, "0.5Ki"),
        (1355, "1.32Ki"),  # Rounding down from 1.323...
        (1360, "1.33Ki"),  # Rounding up from 1.328...
        (523456, "511.19Ki"),
        (524500, "0.5Mi"),
        (14000000, "13.35Mi"),  # Rounding down from 13.351...
        (15000000, "14.31Mi"),  # Rounding up from 14.305...
        (536789999, "511.92Mi"),
        (536999999, "0.5Gi"),
        (1204534567890, "1121.81Gi"),  # Rounding down from 1121.810...
        (1234534567890, "1149.75Gi"),  # Rounding up from 1149.749...
    ),
)
def test_human_readble_number_default_digits(
    number: int, expected_representation: str
) -> None:
    """
    Test human readable representation of size with default rounding.
    """
    assert (
        expected_representation
        == pydupfinder.pentode_fi.number.human_readable_number(number)
    )
