"""
Tests for pydupfinder.pentode_fi.size
"""
from unittest.mock import patch

import pydupfinder.pentode_fi.size


def test_megabyte_suffix() -> None:
    """
    Test that megabyte suffix works.
    """
    three_megs = 3 * 1024 * 1024
    with patch("pydupfinder.pentode_fi.size.click.Context") as mock_ctx_class:
        with patch(
            "pydupfinder.pentode_fi.size.click.Parameter"
        ) as mock_param_class:
            mocked_context = mock_ctx_class()
            mocked_parameter = mock_param_class()
            assert three_megs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3m"
            )
            assert three_megs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3M"
            )
            assert three_megs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3 m"
            )
            assert three_megs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3 M"
            )
            assert three_megs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3	m"
            )
            assert three_megs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3	M"
            )


def test_gigabyte_suffix() -> None:
    """
    Test that gigabyte suffix works.
    """
    three_gigs = 3 * 1024 * 1024 * 1024
    with patch("pydupfinder.pentode_fi.size.click.Context") as mock_ctx_class:
        with patch(
            "pydupfinder.pentode_fi.size.click.Parameter"
        ) as mock_param_class:
            mocked_context = mock_ctx_class()
            mocked_parameter = mock_param_class()
            assert three_gigs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3g"
            )
            assert three_gigs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3G"
            )
            assert three_gigs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3 g"
            )
            assert three_gigs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3 G"
            )
            assert three_gigs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3	g"
            )
            assert three_gigs == pydupfinder.pentode_fi.size.parse_size(
                mocked_context, mocked_parameter, "3	G"
            )
