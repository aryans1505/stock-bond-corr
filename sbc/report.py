from pathlib import Path

import numpy as np
import pandas as pd

from sbc import portfolio, regimes

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"

# eras first, then the episodes people actually ask about
WINDOWS = {
    "1990-1999": ("1990", "1999"),
    "2000-2020": ("2000", "2020"),
    "2021-2026": ("2021", "2026"),
    "1994": ("1994", "1994"),
    "2000-2002": ("2000", "2002"),
    "2008": ("2008", "2008"),
    "2013": ("2013", "2013"),
    "2020": ("2020", "2020"),
    "2022": ("2022", "2022"),
}


def decomposition_table(rets, port):
    rows = []
    for name, (a, b) in WINDOWS.items():
        d = portfolio.decompose_variance(rets.loc[a:b])
        p = port.loc[a:b]
        d["port_vol"] = p.std() * np.sqrt(252)
        d["max_dd"] = portfolio.max_drawdown(p)
        d["ann_ret"] = (1 + p).prod() ** (252 / len(p)) - 1
        d.name = name
        rows.append(d)
    cols = ["eq_vol", "bond_vol", "corr", "mix_vol", "port_vol", "corr_share", "max_dd", "ann_ret"]
    return pd.DataFrame(rows)[cols]


def monthly_decomposition_table(rets):
    # same split on monthly returns, where the 2022 flip is much larger
    m = (1 + rets).resample("ME").prod() - 1
    rows = []
    for name, (a, b) in WINDOWS.items():
        d = portfolio.decompose_variance(m.loc[a:b], periods=12)
        d.name = name
        rows.append(d)
    return pd.DataFrame(rows)[["eq_vol", "bond_vol", "corr", "mix_vol", "corr_share"]]


def drawdown_figure(port, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    level = (1 + port).cumprod()
    dd = level / level.cummax() - 1
    fig, ax = plt.subplots(figsize=(11, 3.5))
    ax.fill_between(dd.index, dd * 100, 0, color="C0", alpha=0.6)
    for label, day in [("2009-03-09", "2009-03-09"), ("2022-10-14", "2022-10-14")]:
        ax.annotate(f"{dd[day]*100:.1f}% {label}", (pd.Timestamp(day), dd[day] * 100),
                    textcoords="offset points", xytext=(6, -8), fontsize=8)
    ax.set_title("60/40 drawdown from peak, monthly rebalanced, %")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def run():
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    rets = regimes.daily_returns()
    port, _ = portfolio.fixed_mix(rets)
    rc = regimes.rolling_corr(rets)
    mc = regimes.monthly_corr(rets)
    regimes.plot_rolling_corr(rc, mc, FIGURES / "rolling_corr.png")
    pd.concat([rc, mc.reindex(rc.index, method="ffill")], axis=1).round(4).to_csv(RESULTS / "rolling_corr.csv")
    daily = decomposition_table(rets, port)
    daily.round(4).to_csv(RESULTS / "decomposition_daily.csv")
    monthly = monthly_decomposition_table(rets)
    monthly.round(4).to_csv(RESULTS / "decomposition_monthly.csv")
    drawdown_figure(port, FIGURES / "drawdown_6040.png")
    pd.set_option("display.width", 160)
    print((daily * 100).round(1).assign(corr=daily["corr"].round(2)))
    print((monthly * 100).round(1).assign(corr=monthly["corr"].round(2)))
