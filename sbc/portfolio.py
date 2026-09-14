import numpy as np
import pandas as pd

TARGET = {"sp500_tr": 0.6, "ust10y_tr": 0.4}


def _check_total_return(rets):
    bad = [c for c in rets.columns if not c.endswith("_tr")]
    if bad:
        raise ValueError(f"portfolio needs total-return series, got price-only columns {bad}")


def fixed_mix(rets, target=TARGET):
    """Daily returns of a portfolio reset to `target` weights at every month-end.

    Between rebalances the weights drift with returns. Returns (portfolio returns,
    weights held going into each day), so the weight used on day t only depends on
    data through t-1.
    """
    _check_total_return(rets)
    cols = list(target)
    w_target = np.array([target[c] for c in cols])
    r = rets[cols].to_numpy()
    month = rets.index.to_period("M")
    w = w_target.copy()
    port = np.empty(len(r))
    held = np.empty_like(r)
    for i in range(len(r)):
        held[i] = w
        port[i] = w @ r[i]
        w = w * (1 + r[i]) / (1 + port[i])
        last_day_of_month = i + 1 == len(r) or month[i + 1] != month[i]
        if last_day_of_month:
            w = w_target.copy()
    return (pd.Series(port, index=rets.index, name="port_tr"),
            pd.DataFrame(held, index=rets.index, columns=cols))


def decompose_variance(rets, target=TARGET, periods=252):
    """Split the variance of the fixed-weight mix into the three textbook terms.

    var = we^2 var_e + wb^2 var_b + 2 we wb rho s_e s_b. Annualised with `periods`
    per year (252 for daily returns, 12 for monthly).
    The identity is exact for constant weights; the monthly-rebalanced portfolio
    differs slightly because weights drift inside the month.
    """
    e, b = rets["sp500_tr"], rets["ust10y_tr"]
    we, wb = target["sp500_tr"], target["ust10y_tr"]
    se, sb = e.std() * np.sqrt(periods), b.std() * np.sqrt(periods)
    rho = e.corr(b)
    terms = {
        "eq_term": we**2 * se**2,
        "bond_term": wb**2 * sb**2,
        "corr_term": 2 * we * wb * rho * se * sb,
    }
    terms["total"] = sum(terms.values())
    terms["corr_share"] = terms["corr_term"] / terms["total"]
    terms.update(eq_vol=se, bond_vol=sb, corr=rho, mix_vol=np.sqrt(terms["total"]))
    return pd.Series(terms)


def max_drawdown(port):
    level = (1 + port).cumprod()
    return (level / level.cummax() - 1).min()
