"""Daily market breadth tracker for Nifty 500.
Counts how many stocks moved above/below X% vs previous close
and saves one row per trading day to history.csv.
"""
import io, os
import pandas as pd
import requests
import yfinance as yf

THRESHOLDS = [3, 5, 10]   # change these to whatever you like
SUFFIX = ".NS"
CSV = "history.csv"
LIST_URLS = [
    "https://niftyindices.com/IndexConstituent/ind_nifty500list.csv",
    "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
]


def get_symbols():
    for url in LIST_URLS:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            r.raise_for_status()
            syms = pd.read_csv(io.StringIO(r.text))["Symbol"].dropna().tolist()
            if len(syms) > 400:
                print(f"Loaded {len(syms)} symbols from {url}")
                return syms
        except Exception as e:
            print("List download failed:", url, e)
    print("Using stocks.txt fallback")
    return [s.strip() for s in open("stocks.txt") if s.strip()]


symbols = get_symbols()
tickers = [s.upper() + SUFFIX for s in symbols]

prices = yf.download(tickers, period="10d", auto_adjust=False, progress=False)["Close"]
change = prices.pct_change(fill_method=None).iloc[-1].dropna() * 100
date = prices.index[-1].strftime("%Y-%m-%d")

row = {"Date": date, "Stocks": len(change)}
for t in THRESHOLDS:
    row[f"Abv {t}%"] = int((change >= t).sum())
    row[f"Blw {t}%"] = int((change <= -t).sum())

new = pd.DataFrame([row])
if os.path.exists(CSV):
    new = pd.concat([pd.read_csv(CSV), new]).drop_duplicates("Date", keep="last")
new.sort_values("Date", ascending=False).to_csv(CSV, index=False)
print(new.sort_values("Date", ascending=False).head())
