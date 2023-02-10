"""
Tests for pydupfinder.pentode_fi.memory.
"""
from typing import Optional
from unittest.mock import NonCallableMock, patch

from click import BadParameter
import pytest

import pydupfinder.pentode_fi.memory


@pytest.mark.parametrize(
    "given,expected",
    (
        (None, None),
        ("7.5%", 1288490188),
        ("14.6 %", 2508260900),
        ("28.7	%", 4930622455),
    ),
)
def test_parsing_memory_limit(
    given: Optional[str], expected: Optional[int]
) -> None:
    """
    Test that memory limit is parsed correctly if given as percentage
    of the total memory.
    """
    with patch(
        "pydupfinder.pentode_fi.memory.psutil.virtual_memory"
    ) as virtual:
        virtual.return_value = NonCallableMock()
        virtual.return_value.total = 17179869184
        assert expected == pydupfinder.pentode_fi.memory.parse_memory_limit(
            NonCallableMock(), NonCallableMock(), given
        )


@pytest.mark.parametrize("given", ("blah %", "-20%", "142%"))
def test_invalid_value(given: Optional[str]) -> None:
    """
    Test that invalid value is rejected.
    """
    with pytest.raises(BadParameter):
        _: Optional[int] = pydupfinder.pentode_fi.memory.parse_memory_limit(
            NonCallableMock(), NonCallableMock(), given
        )
