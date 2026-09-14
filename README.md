# stock-bond-corr

## Question

Since 1990, how much of a US 60/40 portfolio's risk has come from the correlation between stocks and bonds? What happened to that when the correlation turned positive in 2022, and what would a risk model built on trailing data have told an investor at the time? Then the same for the UK, including the gilt move in September 2022.

## Answer so far (as of 14 Sep 2026)

Only the correlation itself so far, no portfolio numbers yet.

![rolling correlation](figures/rolling_corr.png)

Using monthly returns, the S&P 500 and a 10y Treasury had a correlation of +0.35 in the 1990s, -0.34 over 2000-2020, +0.59 in 2022 and +0.47 since. In daily returns the same eras are +0.27, -0.38, +0.17 and +0.04, so the 2022 flip shows up much more clearly at the monthly horizon, which I don't yet have an explanation for.

The flip was visible in a 63-day daily correlation from Feb 2021 and in a 252-day one from Nov 2021. A 36-month monthly correlation did not turn positive until Aug 2022.

## How I got there

- Bond returns are built from the Treasury 10y par yield, 1990 onwards: each day the bond bought at par the day before is repriced at the par yield for its now slightly shorter maturity (`sbc/bonds.py`). Checked against IEF over 2002-2026: 33 bps a year ahead of the ETF, monthly return correlation 0.985. IEF's 15 bps fee is about half of that gap.
- Equity is the S&P 500 total return index from Yahoo.
- Correlations in `sbc/regimes.py`; the dated working notes are in `notes/LOG.md`.

## Changelog

- 14 Sep 2026: repo created, question written down, data sources checked. Bond returns from yields, IEF check, first correlation figure.
