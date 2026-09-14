import numpy as np
import pandas as pd

from sbc import data, portfolio


def yield_components():
    """10y nominal par yield split into the TIPS real yield and the breakeven, 2003 on.

    Percent, Treasury calendar. breakeven = nominal - real, so the three daily
    changes add up by construction.
    """
    nominal = data.load_treasury("par")[10.0].rename("nominal")
    real = data.load_treasury("real")[10.0].rename("real")
    df = pd.concat([nominal, real], axis=1, sort=True).dropna()
    df["breakeven"] = df["nominal"] - df["real"]
    return df


def equity_on(index):
    # S&P 500 total return compounded onto another calendar (here the Treasury one)
    level = data.load_yahoo("^SP500TR")
    return level.reindex(index, method="ffill").pct_change().rename("sp500_tr")


def component_table(comp, eq, windows):
    """Per window: total change in each yield in bp, share of nominal-change variance
    from real vs breakeven, and the correlation of equity returns with each."""
    d = comp.diff()
    rows = []
    for name, (a, b) in windows.items():
        dw, cw, ew = d.loc[a:b], comp.loc[a:b], eq.loc[a:b]
        m = ((1 + ew).resample("ME").prod() - 1)
        cm = cw.resample("ME").last().diff()
        v_n = dw["nominal"].var()
        rows.append(pd.Series({
            "d_nominal_bp": (cw["nominal"].iloc[-1] - cw["nominal"].iloc[0]) * 100,
            "d_real_bp": (cw["real"].iloc[-1] - cw["real"].iloc[0]) * 100,
            "d_breakeven_bp": (cw["breakeven"].iloc[-1] - cw["breakeven"].iloc[0]) * 100,
            "real_var_share": dw["real"].var() / v_n,
            "breakeven_var_share": dw["breakeven"].var() / v_n,
            "cross_share": 2 * dw["real"].cov(dw["breakeven"]) / v_n,
            "eq_corr_real_d": ew.corr(dw["real"]),
            "eq_corr_breakeven_d": ew.corr(dw["breakeven"]),
            "eq_corr_real_m": m.corr(cm["real"]),
            "eq_corr_breakeven_m": m.corr(cm["breakeven"]),
        }, name=name))
    return pd.DataFrame(rows)


def trailing_forecasts(rets, windows=(252, 2520), horizon=252, target=portfolio.TARGET):
    """At each month-end, 60/40 vol implied by the trailing covariance of daily returns,
    against the vol actually realised over the next `horizon` trading days.

    The forecast at month-end t uses returns up to and including t. The realised
    number uses t+1 .. t+horizon, so the two never share a day.
    """
    cols = list(target)
    w = np.array([target[c] for c in cols])
    r = rets[cols]
    month_ends = r.groupby(r.index.to_period("M")).tail(1).index
    rows = []
    for t in month_ends:
        i = r.index.get_loc(t)
        row = {}
        for win in windows:
            if i + 1 < win:
                row[f"fc_{win}d"] = np.nan
                row[f"corr_{win}d"] = np.nan
                continue
            past = r.iloc[i + 1 - win:i + 1]
            cov = past.cov().to_numpy() * 252
            row[f"fc_{win}d"] = np.sqrt(w @ cov @ w)
            row[f"corr_{win}d"] = past.iloc[:, 0].corr(past.iloc[:, 1])
        fut = r.iloc[i + 1:i + 1 + horizon]
        if len(fut) == horizon:
            fp = fut @ w
            row["realised"] = fp.std() * np.sqrt(252)
            row["realised_corr"] = fut.iloc[:, 0].corr(fut.iloc[:, 1])
            row["realised_dd"] = portfolio.max_drawdown(fp)
        else:
            row["realised"] = row["realised_corr"] = row["realised_dd"] = np.nan
        rows.append(pd.Series(row, name=t))
    return pd.DataFrame(rows)


def diversification_ratio(vol_e, vol_b, corr, target=portfolio.TARGET):
    # weighted sum of vols over portfolio vol; 1 means no diversification at all
    we, wb = target["sp500_tr"], target["ust10y_tr"]
    port = np.sqrt(we**2 * vol_e**2 + wb**2 * vol_b**2 + 2 * we * wb * corr * vol_e * vol_b)
    return (we * vol_e + wb * vol_b) / port
