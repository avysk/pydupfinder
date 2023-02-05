import pydupfinder.pentode_fi.size


def test_megabyte_suffix():
    three_megs = 3 * 1024 * 1024
    assert three_megs == pydupfinder.pentode_fi.size.parse_size(
        None, None, "3m"
    )
    assert three_megs == pydupfinder.pentode_fi.size.parse_size(
        None, None, "3M"
    )
    assert three_megs == pydupfinder.pentode_fi.size.parse_size(
        None, None, "3 m"
    )
    assert three_megs == pydupfinder.pentode_fi.size.parse_size(
        None, None, "3 M"
    )
    assert three_megs == pydupfinder.pentode_fi.size.parse_size(
        None, None, "3	m"
    )
    assert three_megs == pydupfinder.pentode_fi.size.parse_size(
        None, None, "3	M"
    )
