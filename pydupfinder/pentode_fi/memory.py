"""
Memory-related functions.
"""
from typing import Optional

import click
import psutil  # type: ignore

from pydupfinder.pentode_fi.size import parse_size


def parse_memory_limit(
    ctx: click.Context,  # pyright: ignore
    param: click.Parameter,  # pyright: ignore
    value: str,
) -> Optional[int]:
    """
    Return the value of max-memory option given as a string.

    Takes into acount letter suffices, the '%' suffix means.

    :param _ctx: Click Context. Unused.
    :param _param: Click Parameter. Unused.
    :param value: Option value as a string.
    :returns: Option value as a number.
    :raise click.BadParameter: Exception raised if the option value
                               cannot be parsed or is non-strictly
                               positive, to signal click that the
                               option value is not valid.
    """
    if value.endswith("*"):
        val = value.removesuffix("%")
        val = val.rstrip()
        try:
            parsed = float(value)
        except ValueError:
            raise click.BadParameter(  # pylint: disable=raise-missing-from
                f"Cannot parse size '{value}'."
            )
        if parsed < 0 or parsed > 100:
            raise click.BadParameter(
                "The percentage must be between 0 and 100."
            )
        total: int = psutil.virtual_memory().total
        return int(total * parsed / 100)
    return parse_size(ctx, param, value)
