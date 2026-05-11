"""
data_loader.py — Load, cache, and generate the retail dataset.

Tries to load from data/online_retail.csv first.
Falls back to synthetic data generation if the file is missing.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from faker import Faker

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "online_retail.csv"

COUNTRIES = [
    "United Kingdom", "Germany", "France", "EIRE", "Spain",
    "Netherlands", "Belgium", "Switzerland", "Portugal", "Australia",
    "Norway", "Italy", "Denmark", "Cyprus", "Sweden",
    "Japan", "Finland", "Channel Islands", "Singapore", "Malta",
]

COUNTRY_WEIGHTS = [
    0.85, 0.03, 0.03, 0.02, 0.01,
    0.01, 0.005, 0.005, 0.005, 0.005,
    0.003, 0.003, 0.003, 0.002, 0.002,
    0.002, 0.001, 0.001, 0.001, 0.001,
]

SAMPLE_PRODUCTS = [
    ("85123A", "WHITE HANGING HEART T-LIGHT HOLDER"),
    ("71053",  "WHITE METAL LANTERN"),
    ("84406B", "CREAM CUPID HEARTS COAT HANGER"),
    ("84029G", "KNITTED UNION FLAG HOT WATER BOTTLE"),
    ("84029E", "RED WOOLLY HOTTIE WHITE HEART"),
    ("22752",  "SET 7 BABUSHKA NESTING BOXES"),
    ("21730",  "GLASS STAR FROSTED T-LIGHT HOLDER"),
    ("22633",  "HAND WARMER UNION JACK"),
    ("22632",  "HAND WARMER RED POLKA DOT"),
    ("84797",  "RETRO COFFEE MUGS ASSORTED"),
    ("20725",  "LUNCH BAG RED RETROSPOT"),
    ("20727",  "LUNCH BAG BLACK SKULL"),
    ("20728",  "LUNCH BAG CARS BLUE"),
    ("21212",  "PACK OF 72 RETROSPOT CAKE CASES"),
    ("23298",  "VICTORIAN GLASS HANGING T-LIGHT"),
    ("22423",  "REGENCY CAKESTAND 3 TIER"),
    ("47566",  "PARTY BUNTING"),
    ("85099B", "JUMBO BAG RED RETROSPOT"),
    ("22111",  "SCOTTIE DOG HOT WATER BOTTLE"),
    ("22086",  "PAPER CHAIN KIT VINTAGE CHRISTMAS"),
    ("21931",  "JUMBO STORAGE BAG SUKI"),
    ("21928",  "JUMBO BAG PINK POLKADOT"),
    ("21929",  "JUMBO BAG SCANDINAVIAN BLUE"),
    ("22197",  "SMALL POPCORN HOLDER"),
    ("22355",  "CHARLOTTE BAG PINK POLKADOT"),
    ("22356",  "CHARLOTTE BAG SUKI DESIGN"),
    ("22357",  "KINGS CHOICE BISCUIT TIN"),
    ("22382",  "LUNCH BAG SPACEBOY DESIGN"),
    ("22383",  "LUNCH BAG SUKI DESIGN"),
    ("22384",  "LUNCH BAG PINK POLKADOT"),
    ("22386",  "JUMBO BAG WOODLAND ANIMALS"),
    ("22390",  "PICNIC BASKET WICKER SMALL"),
    ("22391",  "PICNIC BASKET WICKER MEDIUM"),
    ("22393",  "PICNIC BASKET WICKER LARGE"),
    ("22412",  "TOADSTOOL LED NIGHT LIGHT"),
    ("22413",  "LED TORCH RETRO SPOT"),
    ("22416",  "JIGSAW BOX RETROSPOT"),
    ("22417",  "JIGSAW CIRCUS PARADE"),
    ("22418",  "JIGSAW SNOWMAN"),
    ("22419",  "JIGSAW SPACEBOY"),
    ("22469",  "HEART OF WICKER SMALL"),
    ("22470",  "HEART OF WICKER LARGE"),
    ("22471",  "HANGING HEART ZINC T-LIGHT HOLDER"),
    ("22485",  "PAINTED METAL STAR"),
    ("22486",  "PAINTED METAL HEARTS ASSORTED"),
    ("22551",  "PLASTERS IN TIN CIRCUS PARADE"),
    ("22552",  "PLASTERS IN TIN STRONGMAN"),
    ("22553",  "PLASTERS IN TIN VINTAGE STAR"),
    ("22554",  "PLASTERS IN TIN SKIPPING GIRL"),
    ("22556",  "PLASTERS IN TIN WOODLAND"),
]


def _generate_synthetic_data(n_rows: int = 500_000) -> pd.DataFrame:
    """Generate realistic synthetic UK retail transactions."""
    rng = np.random.default_rng(42)
    fake = Faker("en_GB")
    Faker.seed(42)

    n_customers = 4_500
    n_invoices = 25_000
    customer_ids = rng.integers(10_000, 20_000, size=n_customers)

    invoice_ids = [f"{rng.integers(489_000, 581_600):06d}" for _ in range(n_invoices)]

    # date range: 2009-12-01 to 2011-12-09
    start_ts = pd.Timestamp("2009-12-01")
    end_ts   = pd.Timestamp("2011-12-09")
    total_seconds = int((end_ts - start_ts).total_seconds())

    rows = []
    used = 0
    for inv_idx in range(n_invoices):
        if used >= n_rows:
            break
        invoice_no = invoice_ids[inv_idx]
        customer_id = customer_ids[rng.integers(0, n_customers)]
        country = rng.choice(COUNTRIES, p=COUNTRY_WEIGHTS / np.array(COUNTRY_WEIGHTS).sum())

        # business hours skew
        hour_weights = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.2, 0.5, 1.5, 3.0,
                                  4.5, 5.0, 5.5, 5.0, 4.5, 4.0, 3.0, 2.0, 1.5,
                                  1.0, 0.5, 0.3, 0.2, 0.15, 0.1])
        hour_weights /= hour_weights.sum()
        hour = rng.choice(24, p=hour_weights)

        offset_s = rng.integers(0, total_seconds)
        inv_dt = start_ts + pd.Timedelta(seconds=int(offset_s))
        inv_dt = inv_dt.replace(hour=hour, minute=rng.integers(0, 60))

        # number of line items per invoice
        n_items = min(rng.integers(1, 18), n_rows - used)
        for _ in range(n_items):
            stock_code, description = SAMPLE_PRODUCTS[rng.integers(0, len(SAMPLE_PRODUCTS))]
            quantity = int(rng.integers(1, 48))
            price = round(float(rng.choice([0.42, 0.85, 1.25, 1.65, 2.10, 2.95,
                                             3.75, 4.95, 6.50, 8.50, 12.75, 16.95,
                                             19.99, 24.95, 32.50])), 2)
            rows.append({
                "Invoice":      invoice_no,
                "StockCode":    stock_code,
                "Description":  description,
                "Quantity":     quantity,
                "InvoiceDate":  inv_dt,
                "Price":        price,
                "Customer ID":  customer_id,
                "Country":      country,
            })
            used += 1

    df = pd.DataFrame(rows)
    return df


def load_raw_data() -> pd.DataFrame:
    """Load raw data from CSV, or generate synthetic data if CSV is absent."""
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH, encoding="latin-1", low_memory=False)
        # normalise column names for both dataset versions
        col_map = {
            "InvoiceNo":  "Invoice",
            "UnitPrice":  "Price",
            "CustomerID": "Customer ID",
        }
        df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)
        return df

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = _generate_synthetic_data(500_000)
    df.to_csv(CSV_PATH, index=False)
    return df


@st.cache_data(show_spinner="Loading dataset…")
def get_clean_data() -> pd.DataFrame:
    """Return the cleaned, feature-engineered DataFrame (cached by Streamlit)."""
    from src.transformations import clean_and_engineer
    raw = load_raw_data()
    return clean_and_engineer(raw)


def get_sqlite_connection(df: pd.DataFrame) -> sqlite3.Connection:
    """Create an in-memory SQLite DB loaded with the cleaned DataFrame."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql("retail", conn, if_exists="replace", index=False)
    return conn
