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

    Takes into acount letter suffices. The number before the suffix can
    be a decimal fraction.

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
        parsed = int(float(val) * multiplier)
    except ValueError:
        raise click.BadParameter(  # pylint: disable=raise-missing-from
            f"Cannot parse size '{value}'."
        )
    if parsed <= 0:
        raise click.BadParameter(
            f"Got value '{value}'. It must be strictly positive."
        )
    return parsed


def human_readable_number(number: int, digits: int = 2) -> str:
    """
    Convert number to human readable format.

    If number is more than or equal to a half of a kilo (mega, giga)
    it is presented as a decimal fraction with the given number of
    digits after the decimal separator and a Ki (Mi, Gi) suffix.

    :param number: number to convert
    :param digits: the number of digits after the decimal separator.
    :returns: the string reprosentation of the size.
    """
    next_unit = 1024
    half_ki = 512
    half_mi = half_ki * next_unit
    half_gi = half_mi * next_unit
    adjusted: float
    if number < half_ki:
        adjusted = number
        units = ""
    elif number < half_mi:
        adjusted = number / next_unit
        units = "Ki"
    elif number < half_gi:
        adjusted = number / next_unit / next_unit
        units = "Mi"
    else:
        adjusted = number / next_unit / next_unit / next_unit
        units = "Gi"

    return f"{round(adjusted, ndigits=digits)}{units}"
