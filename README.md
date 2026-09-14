# stock-bond-corr

## Question

Since 1990, how much of a US 60/40 portfolio's risk has come from the correlation between stocks and bonds? What happened to that when the correlation turned positive in 2022, and what would a risk model built on trailing data have told an investor at the time? Then the same for the UK, including the gilt move in September 2022.

## Answer so far (as of 14 Sep 2026)

US only so far. The correlation and the 60/40 split are done; the risk-model part and the UK are not.

![rolling correlation](figures/rolling_corr.png)

Using monthly returns, the S&P 500 and a 10y Treasury had a correlation of +0.35 in the 1990s, -0.34 over 2000-2020, +0.59 in 2022 and +0.47 since. In daily returns the same eras are +0.27, -0.38, +0.17 and +0.04. The 2022 flip is mostly a weeks-and-months thing: both assets were repricing the path of Fed rates, and day-to-day moves stayed largely unrelated. In 2000-2020 the daily, weekly and monthly numbers agree, which fits both assets reacting to growth news on the same day.

The flip was visible in a 63-day daily correlation from Feb 2021 and in a 252-day one from Nov 2021. A 36-month monthly correlation did not turn positive until Aug 2022.

**What it did to a 60/40** (S&P 500 / 10y Treasury, rebalanced monthly), splitting variance into an equity term, a bond term and the correlation term 2 x 0.6 x 0.4 x rho x s_e x s_b:

| window | corr (monthly) | correlation term, share of 60/40 variance | 60/40 vol | max drawdown |
|---|---|---|---|---|
| 2000-2020 | -0.34 | -24.8% | 8.6% | -32.1% (Mar 2009) |
| 2022 | +0.59 | +24.2% | 16.5% | -21.7% (14 Oct 2022) |
| 1994 | +0.73 | +33.2% | 8.3% | -8.7% |
| 1990s | +0.35 | +17.6% | 9.4% | -12.3% |

So the correlation term swung from taking about a quarter off 60/40 variance to adding about a quarter. Twelve monthly observations for 2022 is a small sample; on daily returns the same swing is -22% to +8%. The 2022 drawdown was smaller than 2008's because equity vol was 24% rather than 41%, not because bonds helped: they lost 16.5% that year.

![60/40 drawdown](figures/drawdown_6040.png)

Full tables: `results/decomposition_daily.csv`, `results/decomposition_monthly.csv`.

## How I got there

- Bond returns are built from the Treasury 10y par yield, 1990 onwards: each day the bond bought at par the day before is repriced at the par yield for its now slightly shorter maturity (`sbc/bonds.py`). Checked against IEF over 2002-2026: 33 bps a year ahead of the ETF, monthly return correlation 0.985. IEF's 15 bps fee is about half of that gap.
- Equity is the S&P 500 total return index from Yahoo.
- Correlations in `sbc/regimes.py`; the dated working notes are in `notes/LOG.md`.

## Changelog

- 14 Sep 2026: repo created, question written down, data sources checked. Bond returns from yields, IEF check, first correlation figure.
