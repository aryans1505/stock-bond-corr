import numpy as np
import pandas as pd
import pytest

from sbc import uk


def flat_spot(rate, days=5, max_tenor=25.0):
    idx = pd.bdate_range("2020-01-01", periods=days)
    tenors = np.arange(0.5, max_tenor + 0.5, 0.5)
    return pd.DataFrame(rate, index=idx, columns=tenors)


def test_par_yield_on_a_flat_continuous_curve():
    # a flat continuously compounded spot s prices a par bond at the semiannual rate 2(e^{s/2} - 1)
    par = uk.par_from_spot(flat_spot(4.0), 10)
    assert np.allclose(par, 2 * (np.exp(0.04 / 2) - 1) * 100)


def test_par_yield_on_a_flat_annual_curve():
    par = uk.par_from_spot(flat_spot(4.0), 10, continuous=False)
    assert np.allclose(par, 2 * ((1.04) ** 0.5 - 1) * 100)


def test_par_uses_only_tenors_up_to_maturity():
    spot = flat_spot(4.0)
    spot.loc[:, spot.columns > 10] = 9.0  # garbage beyond 10y must not matter
    par = uk.par_from_spot(spot, 10)
    assert np.allclose(par, 2 * (np.exp(0.02) - 1) * 100)


def test_z_score_uses_trailing_std_through_the_previous_day(monkeypatch):
    rng = np.random.default_rng(1)
    idx = pd.bdate_range("2015-01-01", periods=400)
    spot = pd.DataFrame({30.0: 2 + rng.normal(0, 0.05, 400).cumsum()}, index=idx)
    monkeypatch.setattr(uk.data, "load_boe_spot", lambda: spot)
    z = uk.long_gilt_moves(30.0, window=50)
    dy = spot[30.0].diff() * 100
    t = idx[100]
    expected = dy[t] / dy.loc[:idx[99]].iloc[-50:].std()
    assert z.loc[t, "z"] == pytest.approx(expected)
    # changing the future must not change today's z
    spot2 = spot.copy()
    spot2.iloc[101:] += 5
    monkeypatch.setattr(uk.data, "load_boe_spot", lambda: spot2)
    assert uk.long_gilt_moves(30.0, window=50).loc[t, "z"] == pytest.approx(expected)
