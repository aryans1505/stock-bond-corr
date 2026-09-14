from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sbc import bonds

FIX = Path(__file__).parent / "fixtures"


def load_fixture_curve():
    df = pd.read_csv(FIX / "ust_par_2022_2023.csv", index_col="Date", parse_dates=True)
    df.columns = [float(c.split()[0]) for c in df.columns]
    return df


@pytest.mark.parametrize("c,t", [(0.01, 2), (0.05, 10), (0.08, 30), (0.03, 7)])
def test_par_bond_prices_at_par(c, t):
    assert bonds.price(c, c, t) == pytest.approx(1.0, abs=1e-12)


def test_aged_par_bond_is_worth_par_plus_one_day_of_coupon():
    # this is the dirty price; the return code must not add accrual on top of it
    one_day = 1 / 365
    assert bonds.price(0.05, 0.05, 10 - one_day) == pytest.approx(1 + 0.05 * one_day, abs=2e-5)


def test_flat_unchanged_curve_earns_carry_once():
    idx = pd.bdate_range("2024-01-01", periods=30)
    curve = pd.DataFrame({7.0: 4.0, 10.0: 4.0}, index=idx)
    r = bonds.constant_maturity_returns(curve, 10, 7).dropna()
    days = pd.Series(idx, index=idx).diff().dt.days.dropna()
    expected = 0.04 * days / 365
    assert np.allclose(r.values, expected.values, atol=3e-6)


def test_duration_convexity_match_repricing():
    y, t, dy = 0.04, 10, 0.0025
    dur, conv = bonds.duration_convexity(y, t)
    exact = bonds.price(y, y + dy, t) - 1
    taylor = -dur * dy + 0.5 * conv * dy**2
    assert exact == pytest.approx(taylor, abs=1e-6)


def test_yield_derived_10y_matches_ief_on_2022_2023():
    r = bonds.constant_maturity_returns(load_fixture_curve(), 10, 7)
    ief = pd.read_csv(FIX / "ief_adjclose_2022_2023.csv", index_col=0, parse_dates=True)
    ief = ief["Adj Close"].pct_change()
    both = pd.concat([r, ief], axis=1, sort=True).dropna()
    ann = lambda x: (1 + x).prod() ** (252 / len(x)) - 1
    gap = ann(both.iloc[:, 0]) - ann(both.iloc[:, 1])
    monthly = (1 + both).resample("ME").prod() - 1
    # tolerance set after the first look on 14 Sep 2026 (LOG): full-sample gap was 33 bps
    assert abs(gap) < 0.005
    assert monthly.iloc[:, 0].corr(monthly.iloc[:, 1]) > 0.97
