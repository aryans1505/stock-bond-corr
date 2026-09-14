import numpy as np
import pandas as pd

from sbc import bonds, data

# FTSE All-Share on Yahoo is price only and the .L ETF adjusted closes are unusable,
# so UK equity total return = price return + a flat dividend accrual. Correlations do
# not care; the UK 60/40 level and drawdown numbers carry this assumption.
FLAT_DIVIDEND_YIELD = 0.035


def par_from_spot(spot, maturity, continuous=True):
    """Semiannual par yield (percent) implied by a spot curve on 0.5y tenors.

    par = 2 (1 - d_T) / sum d_i over the coupon dates. BoE spot rates are quoted
    continuously compounded; annual compounding is a keyword away for the check.
    """
    tenors = [t for t in spot.columns if 0 < t <= maturity and abs(t * 2 - round(t * 2)) < 1e-9]
    s = spot[tenors] / 100
    t = np.array(tenors)
    d = np.exp(-s * t) if continuous else (1 + s) ** (-t)
    par = 2 * (1 - d[maturity]) / d.sum(axis=1)
    return (par * 100).rename(f"par{int(maturity)}y")


def gilt_par_curve(maturities=(5, 7, 10, 20, 25), continuous=True):
    spot = data.load_boe_spot()
    cols = {m: par_from_spot(spot, m, continuous) for m in maturities}
    return pd.DataFrame({float(m): c for m, c in cols.items()}).dropna(how="all")


def uk_daily_returns(start="1990-01-01", dividend_yield=FLAT_DIVIDEND_YIELD):
    """FTSE All-Share (price + flat dividend accrual) and 10y gilt total returns on the
    equity calendar, same construction as the US panel."""
    px = data.load_yahoo("^FTAS", col="Close")
    days = pd.Series(px.index, index=px.index).diff().dt.days
    eq = (px.pct_change() + dividend_yield * days / 365).rename("ftas_tr")
    par = gilt_par_curve()
    gilt = bonds.constant_maturity_returns(par, 10, 7).dropna().rename("gilt10y_tr")
    gilt_index = (1 + gilt).cumprod()
    gilt_on_eq = gilt_index.reindex(eq.index, method="ffill").pct_change()
    return pd.concat([eq, gilt_on_eq], axis=1, sort=True).loc[start:].dropna()


def long_gilt_moves(tenor=30.0, window=252):
    """Daily change in the long spot yield in bp, and its z-score against the trailing
    `window` days' standard deviation (data through the previous day only)."""
    spot = data.load_boe_spot()
    y = spot[tenor].dropna()
    dy = y.diff() * 100
    z = dy / dy.rolling(window).std().shift(1)
    return pd.DataFrame({"yield": y, "change_bp": dy, "z": z})
