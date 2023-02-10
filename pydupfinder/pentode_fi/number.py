"""
Utilities for working with sizes.
"""
from typing import Optional

import click


def parse_size(
    _ctx: click.Context,  # pyright: ignore
    _param: click.Parameter,  # pyright: ignore
    value: Optional[str],
) -> Optional[int]:
    """
    Return the value of max-size option given as a string.

    Takes into acount letter suffices.

    :param _ctx: Click Context. Unused.
    :param _param: Click Parameter. Unused.
    :param value: Option value as a string.
    :returns: Option value as a number.
    :raise click.BadParameter: Exception raised if the option value
                               cannot be parsed or is non-strictly
                               positive, to signal click that the
                               option value is not valid.
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
    except ValueError:
        raise click.BadParameter(  # pylint: disable=raise-missing-from
            f"Cannot parse size '{value}'."
        )
    if parsed <= 0:
        raise click.BadParameter(
            f"Got value '{value}'. It must be strictly positive."
        )
    return parsed


def human_readable_size(size: int, digits: int = 2) -> str:
    """
    Convert size to human readable format.

    If size is more than or equal to a half of a kilobyte (megabyte, gigabyte)
    it is presented as a decimal fraction with the given number of digits after
    the decimal separator and a Ki (Mi, Gi) suffix. The "B" on the end is
    always added.

    :param size: size to convert
    :param digits: the number of digits after the decimal separator.
    :returns: the string reprosentation of the size.
    """
    next_unit = 1024
    half_kib = 512
    half_mib = half_kib * next_unit
    half_gib = half_mib * next_unit
    if size < half_kib:
        adjusted = size
        units = ""
    elif size < half_mib:
        adjusted = size / next_unit
        units = "Ki"
    elif size < half_gib:
        adjusted = size / next_unit / next_unit
        units = "Mi"
    else:
        adjusted = size / next_unit / next_unit / next_unit
        units = "Gi"

    return f"{round(adjusted, ndigits=digits)}{units}B"
