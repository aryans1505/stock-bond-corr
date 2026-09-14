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
