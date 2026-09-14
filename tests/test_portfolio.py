import numpy as np
import pandas as pd
import pytest

from sbc import portfolio


def synthetic(n=600, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    return pd.DataFrame({
        "sp500_tr": rng.normal(0.0004, 0.012, n),
        "ust10y_tr": rng.normal(0.0002, 0.005, n),
    }, index=idx)


def test_refuses_price_series():
    rets = synthetic().rename(columns={"ust10y_tr": "ust10y_price"})
    with pytest.raises(ValueError):
        portfolio.fixed_mix(rets, {"sp500_tr": 0.6, "ust10y_price": 0.4})


def test_weights_reset_after_month_end_and_drift_inside_it():
    rets = synthetic()
    _, held = portfolio.fixed_mix(rets)
    month = rets.index.to_period("M")
    first_of_month = np.r_[True, month[1:] != month[:-1]]
    assert np.allclose(held[first_of_month], [0.6, 0.4])
    inside = ~first_of_month
    assert not np.allclose(held[inside], [0.6, 0.4])
    assert np.allclose(held.sum(axis=1), 1)


def test_weights_on_day_t_do_not_depend_on_later_data():
    rets = synthetic()
    _, full = portfolio.fixed_mix(rets)
    _, cut = portfolio.fixed_mix(rets.iloc[:-40])
    pd.testing.assert_frame_equal(full.loc[cut.index], cut)


def test_variance_terms_sum_to_fixed_weight_variance():
    rets = synthetic()
    d = portfolio.decompose_variance(rets)
    mix = 0.6 * rets["sp500_tr"] + 0.4 * rets["ust10y_tr"]
    assert d["total"] == pytest.approx(mix.var() * 252, rel=1e-9)
    assert d["eq_term"] + d["bond_term"] + d["corr_term"] == pytest.approx(d["total"])


def test_zero_bond_vol_leaves_only_the_equity_term():
    rets = synthetic()
    rets["ust10y_tr"] = 0.0
    d = portfolio.decompose_variance(rets)
    assert d["bond_term"] == 0 and np.isnan(d["corr"])
    assert d["eq_term"] == pytest.approx(0.36 * rets["sp500_tr"].var() * 252)


def test_max_drawdown_simple_path():
    port = pd.Series([0.1, -0.5, 0.2, 0.0])
    assert portfolio.max_drawdown(port) == pytest.approx(-0.5)
