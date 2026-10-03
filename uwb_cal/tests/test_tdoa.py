import pytest
from uwb_cal.analysis.tdoa import decode_signed_tdoa


@pytest.mark.parametrize("raw,expected", [(0,0),(1,1),(10,10),(2**40-1,2**40-1),(2**40,-2**40),(2**41-1,-1),(2**41-2,-2),(2199023255524,-28),(2199023255379,-173),(-2,-2)])
def test_signed(raw, expected):
    assert decode_signed_tdoa(raw) == expected


def test_invalid_and_other_width():
    assert decode_signed_tdoa(255, bits=8) == -1
    with pytest.raises(ValueError): decode_signed_tdoa(2**41)
    with pytest.raises(ValueError): decode_signed_tdoa(0, 1)
