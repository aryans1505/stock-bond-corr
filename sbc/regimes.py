import numpy as np
import pandas as pd

from sbc import bonds, data


def daily_returns(start="1990-01-01"):
    """Daily total returns of the S&P 500 and a 10y Treasury on the equity calendar.

    Columns end in _tr so the portfolio code can refuse price-only series later.
    Bond returns are computed on the Treasury calendar first, then compounded onto
    equity trading days, so a bond-only day (Columbus Day, Veterans Day) rolls into
    the next day both markets are open instead of being dropped.
    """
    eq = data.load_yahoo("^SP500TR").pct_change().rename("sp500_tr")
    par = data.load_treasury("par")
    bond = bonds.constant_maturity_returns(par, 10, 7).dropna()
    bond_index = (1 + bond).cumprod()
    bond_on_eq = bond_index.reindex(eq.index, method="ffill").pct_change()
    out = pd.concat([eq, bond_on_eq], axis=1, sort=True).loc[start:].dropna()
    return out


def rolling_corr(rets, windows=(63, 252)):
    out = {}
    for w in windows:
        out[f"corr_{w}d"] = rets.iloc[:, 0].rolling(w).corr(rets.iloc[:, 1])
    return pd.DataFrame(out)


def monthly_corr(rets, window=36):
    m = (1 + rets).resample("ME").prod() - 1
    return m.iloc[:, 0].rolling(window).corr(m.iloc[:, 1]).rename(f"corr_{window}m")


def plot_rolling_corr(rc, mc, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(rc.index, rc["corr_63d"], lw=0.6, color="0.7", label="63 trading days")
    ax.plot(rc.index, rc["corr_252d"], lw=1.2, color="C0", label="252 trading days")
    ax.plot(mc.index, mc, lw=1.4, color="C3", label="36 months, monthly returns")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylim(-1, 1)
    ax.set_title("Correlation of S&P 500 and 10y Treasury total returns")
    ax.legend(loc="lower left", frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
