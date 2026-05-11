"""
transformations.py — Data cleaning and feature engineering.

All logic is pure pandas — no I/O, no Streamlit calls.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


def clean_and_engineer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all cleaning steps and derive new columns.

    Steps
    -----
    1. Drop rows with null CustomerID
    2. Remove cancelled orders (Invoice starting with 'C')
    3. Remove non-positive Quantity or Price
    4. Parse InvoiceDate as datetime
    5. Derive: Revenue, Month, DayOfWeek, Hour, Country_clean
    """
    df = df.copy()

    # 1 — drop missing customers
    df = df.dropna(subset=["Customer ID"])
    df["Customer ID"] = df["Customer ID"].astype(int)

    # 2 — remove cancellations
    df = df[~df["Invoice"].astype(str).str.startswith("C")]

    # 3 — remove bad quantities / prices
    df = df[(df["Quantity"] > 0) & (df["Price"] > 0)]

    # 4 — parse dates
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # 5 — derived columns
    df["Revenue"]       = (df["Quantity"] * df["Price"]).round(2)
    df["Month"]         = df["InvoiceDate"].dt.to_period("M").astype(str)
    df["DayOfWeek"]     = df["InvoiceDate"].dt.dayofweek   # 0 = Monday
    df["Hour"]          = df["InvoiceDate"].dt.hour
    df["Country_clean"] = df["Country"].str.strip().str.title()

    return df.reset_index(drop=True)


def compute_rfm(df: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """
    Calculate RFM scores (1–5 quintiles) and assign named segments.

    Parameters
    ----------
    df : cleaned retail DataFrame
    reference_date : anchor for recency calculation; defaults to max InvoiceDate + 1 day
    """
    if reference_date is None:
        reference_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = (
        df.groupby("Customer ID")
        .agg(
            LastPurchase=("InvoiceDate", "max"),
            Frequency=("Invoice", "nunique"),
            Monetary=("Revenue", "sum"),
        )
        .reset_index()
    )
    rfm["Recency"] = (reference_date - rfm["LastPurchase"]).dt.days

    # quintile scoring — higher is better for F and M; lower recency is better
    rfm["R_score"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5,
                              labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_score"] = pd.qcut(rfm["Monetary"].rank(method="first"), 5,
                              labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

    rfm["Segment"] = rfm.apply(_assign_segment, axis=1)
    return rfm


def _assign_segment(row: pd.Series) -> str:
    r, f, m = row["R_score"], row["F_score"], row["M_score"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal"
    if r >= 4 and f <= 2:
        return "New"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r == 1 and f == 1:
        return "Lost"
    return "Potential"


def compute_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a customer cohort retention table.

    Returns a DataFrame pivoted as:
        rows    = cohort month (first purchase month)
        columns = months since first purchase (0, 1, 2, …)
        values  = retention rate (0–1)
    """
    temp = df[["Customer ID", "InvoiceDate", "Invoice"]].copy()
    temp["OrderMonth"] = temp["InvoiceDate"].dt.to_period("M")

    cohort_month = (
        temp.groupby("Customer ID")["OrderMonth"]
        .min()
        .rename("CohortMonth")
        .reset_index()
    )
    temp = temp.merge(cohort_month, on="Customer ID")
    temp["PeriodIndex"] = (
        temp["OrderMonth"].dt.to_timestamp() - temp["CohortMonth"].dt.to_timestamp()
    ).dt.days // 30

    cohort_data = (
        temp.groupby(["CohortMonth", "PeriodIndex"])["Customer ID"]
        .nunique()
        .reset_index()
        .rename(columns={"Customer ID": "Customers"})
    )

    cohort_pivot = cohort_data.pivot(
        index="CohortMonth", columns="PeriodIndex", values="Customers"
    )
    # retention relative to cohort size (period 0)
    cohort_sizes = cohort_pivot[0]
    retention = cohort_pivot.divide(cohort_sizes, axis=0) * 100
    retention.index = retention.index.astype(str)
    return retention
