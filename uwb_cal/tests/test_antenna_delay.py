import pandas as pd
import pytest
from uwb_cal.analysis.antenna_delay import analyze_range, SPEED_OF_LIGHT


def test_range_bias():
    r = analyze_range(pd.DataFrame(dict(true_distance_m=[1,1,2,2,5,5], measured_distance_m=[1.1,1.1,2.1,2.1,5.1,5.1])))
    assert r["bias_m"] == pytest.approx(.1)
    assert r["correction_m"] == pytest.approx(-.1)
    assert r["slope"] == pytest.approx(1)
    assert r["intercept_m"] == pytest.approx(.1)
    assert r["delay_ps"] == pytest.approx(.1/SPEED_OF_LIGHT*1e12)


def test_no_ranges():
    with pytest.raises(ValueError, match="Measured distance is missing"):
        analyze_range(pd.DataFrame(dict(true_distance_m=[2], measured_distance_m=[None])))
