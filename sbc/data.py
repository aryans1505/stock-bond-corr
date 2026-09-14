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

YAHOO = ["^SP500TR", "SPY", "IEF", "^TNX", "^IRX", "^FTAS", "^FTSE", "ISF.L", "IGLT.L"]
# .L tickers: Yahoo's Adj Close does not reflect the distributions it lists, so the
# dividend history is saved separately and total returns are rebuilt from Close + dividend
YAHOO_DIVIDENDS = ["ISF.L", "IGLT.L"]

# Bank of England nominal government liability curve, daily, split into period workbooks
BOE_URL = "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/{name}"
BOE_ZIPS = ["glcnominalddata.zip", "latest-yield-curve-data.zip"]


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


def fetch_dividends(tickers=YAHOO_DIVIDENDS):
    import yfinance as yf

    for t in tickers:
        d = yf.Ticker(t).dividends
        d.index = d.index.tz_localize(None)
        out = RAW / f"yahoo_{t}_div.csv"
        d.rename("Dividend").to_csv(out)
        print(f"{out.name}: {len(d)} payments")


def fetch_boe(names=BOE_ZIPS):
    RAW.mkdir(parents=True, exist_ok=True)
    for name in names:
        r = requests.get(BOE_URL.format(name=name), timeout=300, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        (RAW / f"boe_{name}").write_bytes(r.content)
        print(f"boe_{name}: {len(r.content)} bytes")


def load_boe_spot():
    """Daily UK nominal spot curve, percent, tenor columns in years (0.5 steps).

    The archive is one workbook per period and the sheet names changed in 2005
    ("4. nominal spot curve" then "4. spot curve"), so the sheet is found by name
    fragment and the header row by its "years:" label. Tenors run to 25y before 2016
    and to 40y after. The current-month file overlaps the archive; the archive wins.
    """
    import io
    import zipfile

    frames = []
    for name in ["glcnominalddata.zip", "latest-yield-curve-data.zip"]:
        z = zipfile.ZipFile(RAW / f"boe_{name}")
        for f in z.namelist():
            if "Nominal" not in f or not f.endswith(".xlsx"):
                continue
            x = pd.ExcelFile(io.BytesIO(z.read(f)))
            sheet = [s for s in x.sheet_names if "spot" in s.lower() and "short" not in s.lower()][0]
            raw = x.parse(sheet, header=None)
            hdr = raw.index[raw.iloc[:, 0].astype(str).str.startswith("years")][0]
            tenors = raw.iloc[hdr, 1:].dropna().astype(float)
            body = raw.iloc[hdr + 1:, :len(tenors) + 1]
            body = body[pd.to_datetime(body.iloc[:, 0], errors="coerce").notna()]
            df = body.iloc[:, 1:].astype(float)
            df.index = pd.to_datetime(body.iloc[:, 0])
            df.columns = tenors.values
            frames.append(df.dropna(how="all"))
    out = pd.concat(frames, sort=True).sort_index()
    return out[~out.index.duplicated(keep="first")]


def load_etf_total_return(ticker):
    # daily total return from Close plus the cash dividend paid that day
    px = load_yahoo(ticker, col="Close")
    div = pd.read_csv(RAW / f"yahoo_{ticker}_div.csv", index_col=0, parse_dates=True)["Dividend"]
    div = div.reindex(px.index, fill_value=0.0)
    return ((px + div) / px.shift(1) - 1).rename(f"{ticker}_tr")


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
    # 2010-10-11 (Columbus Day) is an empty row in the par file: bond market shut, row still published
    return df.dropna(how="all")


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
