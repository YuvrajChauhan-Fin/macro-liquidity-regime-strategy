import pandas as pd
import yfinance as yf
from fredapi import Fred
from datetime import datetime


# ============================
# CONFIG
# ============================

START = "1995-01-01"
END = datetime.today().strftime("%Y-%m-%d")

fred = Fred(api_key="edb0f55bbf21a1970f4d5fcd6ac848c7")


# ============================
# FRED MACRO DATA
# ============================

print("Downloading FRED data...")

us10y = fred.get_series("DGS10")
fedfunds = fred.get_series("FEDFUNDS")

# Global liquidity
us_m2 = fred.get_series("WM2NS")

# ECB balance sheet proxy
ecb_assets = fred.get_series("ECBASSETSW")


# ============================
# YAHOO FINANCE FETCH HELPER
# ============================

def fetch_close(ticker):

    data = yf.download(
        ticker,
        start=START,
        end=END,
        auto_adjust=True,   # removes Adj Close problems
        progress=False
    )

    return data["Close"].squeeze()


print("Downloading Yahoo Finance data...")

dxy = fetch_close("DX-Y.NYB")

oil = fetch_close("CL=F")

usdinr = fetch_close("INR=X")


# ============================
# BUILD MACRO DATAFRAME
# ============================

df = pd.DataFrame({

    "US10Y": us10y,
    "FEDFUNDS": fedfunds,
    "DXY": dxy,
    "OIL": oil,
    "USDINR": usdinr,
    "US_M2": us_m2,
    "ECB_ASSETS": ecb_assets

})

df.index = pd.to_datetime(df.index)

df = df.loc[START:END]

# ======================================
# FETCH ASSET PRICES (NIFTY / GLD / SPY)
# ======================================

print("Downloading Asset Prices...")

assets = {

    "NIFTY": "^NSEI",
    "GLD": "GLD",
    "SPY": "SPY"

}

asset_prices = pd.DataFrame()

for name, ticker in assets.items():

    print(f"Downloading {name}...")

    data = yf.download(

        ticker,

        start=START,
        end=END,

        auto_adjust=True,
        progress=False

    )

    if data.empty:

        raise ValueError(
            f"{name} download failed."
        )

    series = data["Close"].copy()

    series.name = name

    asset_prices[name] = series


# Ensure datetime index
asset_prices.index = pd.to_datetime(
    asset_prices.index
)


# ======================================
# JOIN INTO MASTER DATASET
# ======================================

df = df.join(
    asset_prices,
    how="left"
)


# ======================================
# ALIGNMENT (ONE TIME ONLY)
# ======================================

df = df.sort_index()

# Forward fill macro publication lag + market holidays
df = df.ffill()


# ======================================
# SANITY CHECK
# ======================================

print("\nMissing Asset Values After Alignment:")

print(
    df[["NIFTY","GLD","SPY"]]
    .isna()
    .sum()
)


# ======================================
# RETURNS
# ======================================

df["NIFTY_RET"] = df["NIFTY"].pct_change()


# ======================================
# SAVE DATASET
# ======================================

import os

os.makedirs(
    "data_processed",
    exist_ok=True
)

df.to_csv(

    "data_processed/macro_v4_clean.csv"

)

print("\nClean dataset saved.")

print(df.tail())