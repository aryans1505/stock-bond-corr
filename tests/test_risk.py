import numpy as np
import pandas as pd
import pytest

from sbc import risk
from test_portfolio import synthetic


def test_forecast_at_month_end_ignores_later_data():
    rets = synthetic(n=900)
    full = risk.trailing_forecasts(rets, windows=(252,), horizon=60)
    cut = risk.trailing_forecasts(rets.iloc[:-100], windows=(252,), horizon=60)
    common = cut.index[cut["fc_252d"].notna()]
    pd.testing.assert_series_equal(full.loc[common, "fc_252d"], cut.loc[common, "fc_252d"])
    pd.testing.assert_series_equal(full.loc[common, "corr_252d"], cut.loc[common, "corr_252d"])


def test_realised_window_starts_the_day_after_the_forecast():
    rets = synthetic(n=400)
    fc = risk.trailing_forecasts(rets, windows=(63,), horizon=20)
    t = fc.index[5]
    i = rets.index.get_loc(t)
    fut = rets.iloc[i + 1:i + 21]
    expected = (fut @ np.array([0.6, 0.4])).std() * np.sqrt(252)
    assert fc.loc[t, "realised"] == pytest.approx(expected)
    # the last month-ends have no full horizon ahead of them
    assert np.isnan(fc["realised"].iloc[-1])


def test_forecast_matches_closed_form_from_trailing_moments():
    rets = synthetic(n=300)
    fc = risk.trailing_forecasts(rets, windows=(252,), horizon=10)
    t = fc.index[fc["fc_252d"].notna()][0]
    i = rets.index.get_loc(t)
    past = rets.iloc[i + 1 - 252:i + 1]
    se, sb = past.iloc[:, 0].std() * np.sqrt(252), past.iloc[:, 1].std() * np.sqrt(252)
    rho = past.iloc[:, 0].corr(past.iloc[:, 1])
    closed = np.sqrt(0.36 * se**2 + 0.16 * sb**2 + 0.48 * rho * se * sb)
    assert fc.loc[t, "fc_252d"] == pytest.approx(closed)


def test_diversification_ratio_is_one_when_perfectly_correlated():
    assert risk.diversification_ratio(0.2, 0.08, 1.0) == pytest.approx(1.0)
    assert risk.diversification_ratio(0.2, 0.08, -0.4) > risk.diversification_ratio(0.2, 0.08, 0.4)


def test_components_add_up():
    idx = pd.bdate_range("2022-01-03", periods=5)
    comp = pd.DataFrame({"nominal": [1.5, 1.6, 1.7, 1.65, 1.8], "real": [-1.0, -0.9, -0.85, -0.9, -0.7]}, index=idx)
    comp["breakeven"] = comp["nominal"] - comp["real"]
    d = comp.diff().dropna()
    assert np.allclose(d["real"] + d["breakeven"], d["nominal"])
