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
