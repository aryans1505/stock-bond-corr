# Lab notebook

Newest entry at the bottom. Hypotheses, dead ends, and plots that changed my mind.

## 14 Sep 2026

Decisions made today, before any code:

- The project is about the stock-bond correlation and 60/40 risk, not a curve PCA (that's a textbook exercise) and not a central-bank event study (a flatmate already has one).
- Bank markets and risk roles come first, asset management second. So leg 3 is about rates and risk models, not risk parity.
- US first. UK (BoE spot curves, Sep 2022 gilts) comes once the US result exists.
- Bond returns get built from Treasury yields so the sample starts in 1990, not 2002 when IEF launched. IEF is the check that the construction is right.

Data checks (from India, so network is patchy):

- FRED's CSV endpoint timed out on every series I tried (DGS10, DFII10, T10YIE, DTB3). Not going to depend on it.
- The US Treasury daily par yield CSV works per year without a key. 1990s files have 3m/6m/1y/2y/3y/5y/7y/10y/30y. Real yields are a separate file, 2003 onwards. Breakeven = nominal - real.
- Yahoo: ^SP500TR from 1988, SPY from 1993, IEF from Jul 2002, ^TNX (10y yield) from 1962 for a cross-check, IGLT.L from 2008 for the UK later.
- Bank of England yield curve page loads. Haven't tried parsing the xlsx archive yet.

Things I expect to bite later: Yahoo back-adjusts Adj Close so a refreshed download won't hash the same; Treasury and Yahoo holidays differ; 2y yield only from 1990 in the Treasury files.

Evening: `python -m sbc fetch` ran end to end, 66 files, about ten minutes on hotel wifi. Par curve is 9181 rows from 2 Jan 1990 to 11 Sep 2026 with 14 tenors once the 1-2-4 month bills appear in later years. Real curve 5928 rows from 2 Jan 2003. One day has a blank 10y and 2y in the par file, need to find which and decide whether to forward-fill or drop. Hashes are in `data/SNAPSHOT.md`. CI went green on the first push.

Later, bond returns from yields. The blank row is 2010-10-11, Columbus Day, bond market shut; dropped in `load_treasury`.

First version of `constant_maturity_returns`: buy yesterday's 10y par bond, reprice at today's 10y par yield, add yesterday's yield as accrual over the calendar days. Against IEF Adj Close, Jul 2002 to Sep 2026: yield-derived 10y 2.98% a year vs IEF 3.44%, so 45 bps a year short, daily correlation 0.961, monthly 0.985. A 7y/10y blend was 59 bps short with monthly correlation 0.989. Wrong direction: IEF charges 15 bps, so it should be the one lagging.

Suspect roll-down. IEF's bonds age along an upward-sloping curve; my bond is sold and rebought at 10y every day so it never rolls. Duration around 8 times a 7y-10y slope of a few bps per year of maturity comes out near the gap. Second version reprices the bond at the yield for maturity minus one day, interpolated between the 7y and 10y tenors. That flipped the gap to +366 bps a year, which is far too big. Something is being counted twice; the coupon accrual is the obvious suspect since the fractional-maturity price is a dirty price. TODO: check `price` on a par bond aged one day.

Checked: `price(0.05, 0.05, 9.997)` is 1.000148, so the one-day-aged par bond is already worth par plus a day of coupon. The explicit `+ coupon * dt` was the double count. Removed it.

After the fix, Jul 2002 to Sep 2026: 10y 3.77% a year vs IEF 3.44%, 33 bps ahead; 7y/10y blend 29 bps ahead with monthly correlation 0.990 and 1.80% tracking error; 10y alone monthly correlation 0.985, daily 0.961. IEF's 15 bps fee explains about half the gap and the rest is IEF holding a ladder rather than one on-the-run bond, plus the Treasury 3:30pm marks against a 4pm ETF close for the daily noise. Going with the 10y series as the bond leg (one tenor, easy to explain) and keeping the blend as a robustness check. Tolerance for the same-quantity test: annualised gap inside 50 bps and monthly correlation above 0.97.

Full sample 1990-2026 for the 10y: 5.46% a year, 7.45% vol, worst day -2.75% on 17 Mar 2020. Calendar 2022: -16.51% vs IEF -15.16%, the 10y has more duration.

Tests: two of the five new bond tests failed on the first run and both were my expectations being wrong, not the code. Accrual compounds at the semiannual yield (1% smaller than y times dt over a day), and a 25 bp bump leaves a third-order term of 2e-6 that a 1e-6 tolerance catches. Fixed the tests, not the code.

First correlation figure (`figures/rolling_corr.png`). Panel is S&P 500 total return and the 10y series on the equity calendar, 9239 days from Jan 1990. Bond returns on bond-only days get compounded into the next common day rather than dropped.

Correlation by era, daily / monthly:
- 1990-1999: +0.27 / +0.35
- 2000-2020: -0.38 / -0.34
- 2021: -0.11 / +0.12
- 2022: +0.17 / +0.59
- 2023-Sep 2026: +0.04 / +0.47

So the "flip" is much bigger in monthly returns than in daily ones. Daily 2022 is only +0.17 even though both assets fell most of the year; the monthly number is +0.59. Worth understanding before leaning on either: daily correlation is dragged towards zero by day-to-day noise and by the Treasury 3:30pm marks against a 4pm equity close.

Timing of the flip, which is the real-time question for leg 3: the 63d daily correlation first went positive on 25 Feb 2021, the 252d on 23 Nov 2021, and the 36m monthly not until 31 Aug 2022, by which point the 60/40 had already had most of its bad year. The 36m peaked at +0.68 in Dec 2024 and is +0.40 now. Its low was -0.75 in Jan 2013.

Dead end for the day: none, but the daily-vs-monthly gap is a question I did not expect and need to answer, not just report.

60/40 (monthly rebalanced, weights drift inside the month). Variance split into equity, bond and correlation terms, daily returns:

- 2000-2020: corr -0.38, correlation term -22.1% of 60/40 variance, 60/40 vol 10.9%, max drawdown -32.1% (9 Mar 2009).
- 2022: corr +0.17, correlation term +8.4%, 60/40 vol 15.8%, drawdown -21.7% at the trough on 14 Oct 2022, calendar-year return -17.2%.
- 2008 alone: corr -0.44, term -19.4%, equity vol 41%, 60/40 vol 21.5%.
- 1994, the year people compare 2022 to: corr +0.63, term +34.6% of variance, but equity vol was only 9.8% so the 60/40 lost 8.7% peak to trough.
- 1990s as a whole: +0.27, term +13.5%.

On monthly returns the same split is: 2000-2020 corr -0.34 and term -24.8%; 2022 corr +0.59 and term +24.2%, 60/40 vol 16.5%. So the headline "the correlation term went from about -25% of 60/40 variance to about +25%" holds at the monthly horizon and is much weaker (-22% to +8%) at the daily one. Twelve monthly observations for 2022 is a small sample and the number needs saying with that attached.

Why daily and monthly differ so much in 2022. Checked lead-lag: in 2022 the correlation of today's equity return with tomorrow's bond return is +0.08, against 0.00 either side in 2000-2020, so some of it is bonds catching up a day late (the Treasury 3:30pm mark and the 4pm equity close is one candidate). Weekly returns give +0.22 and monthly +0.59. Most of the gap is not a one-day lag then; it is that in 2022 both assets were repricing the same slow-moving thing, the path of Fed rates, so the shared move shows up over weeks and months while day-to-day moves stayed mostly idiosyncratic. In 2000-2020 the daily, weekly and monthly numbers agree (-0.38, -0.34, -0.34), which fits the growth-shock story where both assets react on the same day.

Monthly-rebalanced 60/40 vol is within 0.2 points of the fixed-weight mix vol in every window except 2008 (21.5% vs 22.9%), where drifting weights cut equity exposure as stocks fell.

Leg 3a, what moved the 10y in each episode (`results/real_breakeven.csv`). Real yield is the Treasury TIPS 10y, breakeven is nominal minus real, so the three changes add up by construction.
- 2022: nominal +225 bp, real +255 bp, breakeven -30 bp. The whole move and more was real yields; inflation expectations ended the year lower. Monthly correlation of equity returns with the change in real yields -0.82, with breakevens +0.59.
- 2008: nominal -166 bp, real +55 bp, breakeven -221 bp. Deflation scare: breakevens collapsed, and equities moved with them (+0.68 monthly). Real yields spiked in Oct 2008 on TIPS illiquidity and there is a visible blip in the figure.
- 2020: nominal -95, real -114, breakeven +19. Equities moved with real yields (-0.63) and breakevens (+0.84).
- 2003-2020 overall: equity vs real -0.08 monthly, vs breakeven +0.49. So the normal relationship is "equities like rising inflation expectations, are indifferent to real yields", and 2022 was the year real yields took over as the thing equities feared.
Daily correlations are all much weaker and some flip sign (equity vs real is +0.20 in 2003-2020 daily and -0.08 monthly). Same horizon story as before; quoting the monthly ones with n attached.

Leg 3b, the trailing-window risk model (`results/trailing_forecasts.csv`, `risk_model_key_dates.csv`). At every month-end, 60/40 vol implied by the trailing 1y and 10y daily covariance, against realised vol over the next 252 trading days. Forecast uses data through t, realised starts at t+1, tested.
- End 2021: 1y model said 8.0% (its correlation was already -0.11), 10y model said 9.2% (correlation -0.37). Realised 2022: 15.7%, correlation +0.17, drawdown -21%. Ratio to the 10y model 1.72, the 92nd percentile of all month-ends since 2000.
- How much of the 2022 miss was the correlation: plug the realised 2022 vols (equity 24.1%, bond 10.5%) into the model's assumed correlation and you get 13.5% (10y window) or 14.6% (1y window). So of the 6.5 points the 10y model missed by, 4.3 were vol levels and 2.2 were the correlation flip. Not the headline I expected; the flip was real but the bigger error was assuming 2012-2021 vol levels.
- End 2007 and end 2019 were bigger misses (22.9% and 19.3% realised against 10.5% and 8.0%) and in both the correlation came in more negative than assumed, so it helped. Same calculation gives 23.9% and 19.4% with assumed correlations, above what actually happened. 2022 is the only one of the three year-ends where the correlation made the model's error worse.
- Diversification ratio (weighted vols over portfolio vol): the 10y model assumed 1.35 at end 2021; 2022 delivered 1.19.

Figures: `figures/real_breakeven.png`, `figures/vol_forecast_vs_realised.png`. The second one makes the point on its own: a 1y window is just the last spike shifted right by a year, and a 10y window barely moves.

UK leg, same day. The BoE archive was the dead end I expected, but a small one: one zip of eight workbooks by period, sheet called "4. nominal spot curve" until 2004 and "4. spot curve" from 2005, header row found by its "years:" label, tenors 0.5 to 25y until 2015 and to 40y from Jan 2016, one workbook starting with a "Refresh" row instead of a date. `load_boe_spot` handles all of that; 12055 days from Jan 1979.

BoE publishes spot (zero) rates, not par yields, so I derive a semiannual par yield from the spots at each 0.5y tenor: par = 2 (1 - d_T) / sum d_i. The terminology page only says the instantaneous forwards are continuously compounded; I took the spots as continuous too. Checked the alternative: annual compounding moves the IGLT gap from 28 to 30 bp, so it doesn't matter for anything here. After that the gilt returns use the exact same `constant_maturity_returns` as the Treasuries, which is the point.

Checks against ETFs, using Close plus the listed dividend because Yahoo's Adj Close for .L tickers ignores the distributions it lists (ISF.L adjusted and unadjusted returns differ by 3 bps a year over 2009-2026, which cannot be right for a 3.5%-yielding index):
- 10y gilt vs IGLT.L (all maturities) May 2013 to Sep 2026: 28 bps a year ahead, monthly correlation 0.919. IGLT is longer than 10y; a 10y/20y blend is 4 bps off with monthly correlation 0.956. Using the 10y for the panel to match the US and noting the blend.
- FTSE 100 price plus nothing vs ISF.L total return, Mar 2013 to Sep 2026: ISF earns 3.85% a year more, net of its 7 bp fee. So a flat 3.5% accrual on the FTSE All-Share price index is slightly conservative. Correlations don't depend on it at all; the UK 60/40 return and drawdown do.

UK results (FTSE All-Share 60 / 10y gilt 40, monthly rebalanced, from 1990):
- Monthly correlation: 1990s +0.36, 2000-2020 -0.18, 2021-2026 +0.51, 2022 +0.79 with the correlation term 42.9% of 60/40 variance. Daily 2022 is -0.02 (!), the horizon effect again but starker.
- The UK never had the clean negative regime the US did: 2000-2020 is -0.18 against -0.34, the 252d daily correlation was back above zero in Apr 2014 and the 36m in Jun 2015. Gilts were a weaker hedge for a UK investor all along.
- 2022: UK 60/40 -8.8% for the year, drawdown -16.4% at the trough on 12 Oct 2022, against the US -17.2% and -21.7%. Not because gilts did better (gilt vol 13.2% against 10.5% for Treasuries) but because the FTSE All-Share held up: equity vol 16.5% against 24.2%, and the index was roughly flat on the year with energy and miners in it.
- Full-sample UK 60/40 max drawdown -25.2% on 3 Mar 2009.
- 2008 has daily correlation -0.45 and monthly +0.19. Twelve months. Reporting both.

Sep 2022, 30y spot gilt (BoE only publishes 30y from 2016; the 25y goes back to 1979): 22 Sep +18 bp, 23 Sep (mini-budget) +22, 26 Sep +41, 27 Sep +50, then 28 Sep (BoE announces gilt purchases) -113 bp. Z-scores against the trailing year's daily standard deviation, using data through the previous day: 2.7, 3.3, 6.0, 6.8, then -14.3. The 28 Sep move is the largest in the 25y series since 1980 (z 13.5); the 27 Sep move has only four larger days in 46 years. Since 2017 there have been 34 days with |z| > 3 on the 30y, which says more about how fat the tails are than about any one of them.
