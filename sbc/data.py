import hashlib
from datetime import date
from pathlib import Path

import pandas as pd
import requests

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# the Treasury site serves one CSV per calendar year, no key needed
UST_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all?type={kind}&field_tdr_date_value={year}&page&_format=csv"
)
UST_KINDS = {
    "par": "daily_treasury_yield_curve",       # nominal par yields, 1990 onwards
    "real": "daily_treasury_real_yield_curve",  # TIPS real yields, 2003 onwards
}

YAHOO = ["^SP500TR", "SPY", "IEF", "^TNX", "^IRX"]


def fetch_treasury(kind, years):
    RAW.mkdir(parents=True, exist_ok=True)
    for y in years:
        out = RAW / f"ust_{kind}_{y}.csv"
        r = requests.get(UST_URL.format(year=y, kind=UST_KINDS[kind]), timeout=60,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        out.write_bytes(r.content)
        print(f"{out.name}: {len(r.content)} bytes")


def fetch_yahoo(tickers=YAHOO):
    import yfinance as yf

    RAW.mkdir(parents=True, exist_ok=True)
    for t in tickers:
        df = yf.download(t, period="max", progress=False, auto_adjust=False)
        df.columns = df.columns.get_level_values(0)  # drop the ticker level
        out = RAW / f"yahoo_{t.replace('^', '')}.csv"
        df.to_csv(out)
        print(f"{out.name}: {df.index.min().date()} to {df.index.max().date()}, {len(df)} rows")


def _tenor_years(label):
    n, unit = label.split()
    return float(n) / 12 if unit.lower().startswith("mo") else float(n)


def load_treasury(kind):
    frames = []
    for f in sorted(RAW.glob(f"ust_{kind}_*.csv")):
        df = pd.read_csv(f, index_col="Date", parse_dates=True)
        frames.append(df)
    df = pd.concat(frames).sort_index()
    df.columns = [_tenor_years(c) for c in df.columns]
    return df


def load_yahoo(ticker, col="Adj Close"):
    f = RAW / f"yahoo_{ticker.replace('^', '')}.csv"
    df = pd.read_csv(f, index_col=0, parse_dates=True)
    return df[col].rename(ticker)


def write_snapshot():
    lines = [f"# Raw data snapshot ({date.today().isoformat()})", "",
             "sha256 of each file in data/raw. Yahoo back-adjusts prices, so a fresh",
             "download will not match these exactly; the date above is what matters.", ""]
    for f in sorted(RAW.iterdir()):
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        lines.append(f"- `{f.name}` {h}")
    (RAW.parent / "SNAPSHOT.md").write_text("\n".join(lines) + "\n")
