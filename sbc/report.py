from pathlib import Path

import numpy as np
import pandas as pd

from sbc import portfolio, regimes, risk, uk

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


COMPONENT_WINDOWS = {
    "2003-2020": ("2003", "2020"),
    "2008": ("2008", "2008"),
    "2020": ("2020", "2020"),
    "2022": ("2022", "2022"),
    "2023-2026": ("2023", "2026"),
}

KEY_DATES = ["2007-12-31", "2019-12-31", "2021-12-31"]


def risk_model_table(rets, fc):
    """For a few year-ends: what the trailing-window model said 60/40 vol would be, what
    happened, and how much of the miss was the correlation rather than vol levels
    (realised vols combined with the assumed correlation)."""
    rows = []
    for d in KEY_DATES:
        i = rets.index.get_loc(pd.Timestamp(d))
        fut = rets.iloc[i + 1:i + 253]
        se, sb = fut.iloc[:, 0].std() * np.sqrt(252), fut.iloc[:, 1].std() * np.sqrt(252)
        row = fc.loc[d, ["fc_252d", "corr_252d", "fc_2520d", "corr_2520d", "realised", "realised_corr", "realised_dd"]].copy()
        for win in (252, 2520):
            rho = fc.loc[d, f"corr_{win}d"]
            row[f"realised_vols_assumed_corr_{win}d"] = np.sqrt(0.36 * se**2 + 0.16 * sb**2 + 0.48 * rho * se * sb)
        row["realised_eq_vol"], row["realised_bond_vol"] = se, sb
        row.name = d
        rows.append(row)
    return pd.DataFrame(rows)


def forecast_figure(fc, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(fc.index, fc["realised"] * 100, color="k", lw=1.2, label="realised over the next 12 months")
    ax.plot(fc.index, fc["fc_252d"] * 100, color="C0", lw=1, label="trailing 1y covariance")
    ax.plot(fc.index, fc["fc_2520d"] * 100, color="C3", lw=1, label="trailing 10y covariance")
    ax.set_title("60/40 annualised vol, %: what a trailing-window model implied at each month-end vs what came next")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def real_breakeven_figure(comp, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(comp.index, comp["nominal"], color="k", lw=1, label="10y nominal")
    ax.plot(comp.index, comp["real"], color="C3", lw=1, label="10y real (TIPS)")
    ax.plot(comp.index, comp["breakeven"], color="C0", lw=1, label="breakeven")
    ax.axhline(0, color="0.5", lw=0.6)
    for a, b in [("2008", "2008"), ("2020", "2020"), ("2022", "2022")]:
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b) + pd.offsets.YearEnd(), color="0.9")
    ax.set_title("10y Treasury yield split into real yield and breakeven, %")
    ax.set_ylim(-1.9, None)
    ax.legend(frameon=False, loc="lower center", ncol=3)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def run():
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    rets = regimes.daily_returns()
    port, _ = portfolio.fixed_mix(rets)
    comp = risk.yield_components()
    components = risk.component_table(comp, risk.equity_on(comp.index), COMPONENT_WINDOWS)
    components.round(4).to_csv(RESULTS / "real_breakeven.csv")
    real_breakeven_figure(comp, FIGURES / "real_breakeven.png")
    fc = risk.trailing_forecasts(rets)
    fc.round(4).to_csv(RESULTS / "trailing_forecasts.csv")
    forecast_figure(fc, FIGURES / "vol_forecast_vs_realised.png")
    risk_model = risk_model_table(rets, fc)
    risk_model.round(4).to_csv(RESULTS / "risk_model_key_dates.csv")
    uk_rets = uk.uk_daily_returns()
    uk_port, _ = portfolio.fixed_mix(uk_rets, UK_TARGET)
    uk_daily = uk_decomposition_table(uk_rets, uk_port)
    uk_daily.round(4).to_csv(RESULTS / "uk_decomposition_daily.csv")
    uk_monthly = uk_monthly_decomposition_table(uk_rets)
    uk_monthly.round(4).to_csv(RESULTS / "uk_decomposition_monthly.csv")
    us_uk_corr_figure(rets, uk_rets, FIGURES / "us_uk_rolling_corr.png")
    gilt = uk.long_gilt_moves(30.0)
    gilt.loc["2022-09-01":"2022-10-31"].round(2).to_csv(RESULTS / "gilt30y_sep_oct_2022.csv")
    gilt_figure(gilt, FIGURES / "gilt30y_sep2022.png")
    pd.set_option("display.width", 220)
    print(components.round(2))
    print((risk_model * 100).round(1))
    print((uk_monthly * 100).round(1).assign(corr=uk_monthly["corr"].round(2)))


UK_TARGET = {"ftas_tr": 0.6, "gilt10y_tr": 0.4}


def uk_decomposition_table(rets, port):
    rows = []
    for name, (a, b) in WINDOWS.items():
        d = portfolio.decompose_variance(rets.loc[a:b], UK_TARGET)
        p = port.loc[a:b]
        d["port_vol"] = p.std() * np.sqrt(252)
        d["max_dd"] = portfolio.max_drawdown(p)
        d["ann_ret"] = (1 + p).prod() ** (252 / len(p)) - 1
        d.name = name
        rows.append(d)
    return pd.DataFrame(rows)[["eq_vol", "bond_vol", "corr", "mix_vol", "port_vol", "corr_share", "max_dd", "ann_ret"]]


def uk_monthly_decomposition_table(rets):
    m = (1 + rets).resample("ME").prod() - 1
    rows = []
    for name, (a, b) in WINDOWS.items():
        d = portfolio.decompose_variance(m.loc[a:b], UK_TARGET, periods=12)
        d.name = name
        rows.append(d)
    return pd.DataFrame(rows)[["eq_vol", "bond_vol", "corr", "mix_vol", "corr_share"]]


def us_uk_corr_figure(us, uk_rets, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(regimes.monthly_corr(us), color="C0", lw=1.3, label="US: S&P 500 vs 10y Treasury")
    ax.plot(regimes.monthly_corr(uk_rets), color="C3", lw=1.3, label="UK: FTSE All-Share vs 10y gilt")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylim(-1, 1)
    ax.set_title("36-month correlation of monthly stock and bond returns")
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def gilt_figure(gilt, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    w = gilt.loc["2022-08-01":"2022-11-30"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 5.5), sharex=True)
    a1.plot(w.index, w["yield"], color="k", lw=1.2)
    a1.set_ylabel("30y gilt spot, %")
    a2.bar(w.index, w["change_bp"], color=np.where(w["change_bp"] > 0, "C3", "C0"), width=1)
    a2.set_ylabel("daily change, bp")
    for d in ["2022-09-23", "2022-09-28"]:
        a1.axvline(pd.Timestamp(d), color="0.6", lw=0.8, ls="--")
    a1.set_title("Long gilts around the 23 Sep 2022 mini-budget and the 28 Sep BoE intervention")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
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
