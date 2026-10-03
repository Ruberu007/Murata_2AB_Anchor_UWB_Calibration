import numpy as np
from uwb_cal.analysis.phase import unwrap_phase, zero_offset
from uwb_cal.analysis.statistics import filter_mask


def test_wrap_and_original():
    original = [160,170,178,-179,-170]
    assert np.allclose(unwrap_phase(original), [160,170,178,181,190])
    assert original[-1] == -170
    assert np.allclose(unwrap_phase([170, np.nan, -170]), [170,np.nan,-170], equal_nan=True)


def test_zero_offset_filter():
    values = np.array([-42,-41.7,-41.5,-41.6,100])
    mask = filter_mask(values)
    assert not mask[-1]
    assert abs(zero_offset(values[mask])+41.65) < .01
    assert filter_mask([1,1,1,10]).tolist() == [True,True,True,False]
    assert filter_mask([1,2,3,100], "IQR", 1.5).tolist() == [True,True,True,False]
