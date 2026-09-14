import numpy as np
import pandas as pd


def price(coupon, y, maturity, freq=2):
    # price per 1 of face for a bond paying `coupon` (annual rate) `freq` times a year,
    # discounted at yield `y` compounded `freq` times a year. Fractional maturities are
    # handled by discounting the whole cash-flow strip by the fractional first period.
    n = int(np.ceil(maturity * freq - 1e-9))
    frac = maturity * freq - (n - 1)  # length of the first period in periods, (0, 1]
    k = np.arange(n) + frac
    disc = (1 + y / freq) ** -k
    return coupon / freq * disc.sum() + disc[-1]


def constant_maturity_returns(curve, maturity, lower, freq=2):
    """Daily total return of holding the on-the-run par bond and rolling it every day.

    Each day you own the bond bought yesterday at par (coupon = yesterday's par yield at
    `maturity`). Today it has aged by the calendar days elapsed, so it is repriced at
    the par yield for that slightly shorter maturity, interpolated between the `lower`
    tenor and `maturity`. That interpolation is the roll-down; without it the series
    lags IEF by about half a percent a year (see LOG, 14 Sep).
    `curve` is the par DataFrame in percent with tenor columns in years.
    """
    y = curve[[lower, maturity]].dropna() / 100
    dates = pd.Series(y.index, index=y.index)
    dt = dates.diff().dt.days / 365
    coupon = y[maturity].shift(1)
    # yield for maturity - dt, linear between the two tenors
    slope = (y[maturity] - y[lower]) / (maturity - lower)
    y_aged = y[maturity] - slope * dt
    out = pd.Series(np.nan, index=y.index)
    for t in y.index[1:]:
        out[t] = price(coupon[t], y_aged[t], maturity - dt[t], freq) - 1 + coupon[t] * dt[t]
    return out.rename(f"ust{int(maturity)}y_tr")


def duration_convexity(y, maturity, freq=2, bump=1e-4):
    # modified duration and convexity of a par bond, by bumping the yield
    p0 = price(y, y, maturity, freq)
    up = price(y, y + bump, maturity, freq)
    dn = price(y, y - bump, maturity, freq)
    dur = -(up - dn) / (2 * bump) / p0
    conv = (up + dn - 2 * p0) / bump**2 / p0
    return dur, conv
