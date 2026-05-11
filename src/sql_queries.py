"""
sql_queries.py — All analytical SQL queries executed against the SQLite layer.

Every function accepts a sqlite3.Connection and returns a pd.DataFrame.
Parameterised queries are used throughout to avoid SQL injection.
"""

from __future__ import annotations

import sqlite3

import pandas as pd


# ---------------------------------------------------------------------------
# Revenue aggregations
# ---------------------------------------------------------------------------

def get_monthly_revenue(conn: sqlite3.Connection) -> pd.DataFrame:
    """Monthly revenue totals, order counts, and 3-month rolling average."""
    sql = """
        SELECT
            Month,
            ROUND(SUM(Revenue), 2)                          AS TotalRevenue,
            COUNT(DISTINCT Invoice)                          AS OrderCount,
            COUNT(DISTINCT "Customer ID")                    AS UniqueCustomers
        FROM retail
        GROUP BY Month
        ORDER BY Month
    """
    df = pd.read_sql_query(sql, conn)
    df["RollingAvg3M"] = df["TotalRevenue"].rolling(3, min_periods=1).mean().round(2)
    return df


def get_top_products(conn: sqlite3.Connection, n: int = 20) -> pd.DataFrame:
    """Top N products by revenue with quantity and order count."""
    sql = """
        SELECT
            Description,
            StockCode,
            ROUND(SUM(Revenue), 2)          AS TotalRevenue,
            SUM(Quantity)                    AS TotalQuantity,
            COUNT(DISTINCT Invoice)          AS OrderCount,
            ROUND(AVG(Price), 2)             AS AvgPrice
        FROM retail
        GROUP BY Description, StockCode
        ORDER BY TotalRevenue DESC
        LIMIT :n
    """
    return pd.read_sql_query(sql, conn, params={"n": n})


def get_country_revenue(conn: sqlite3.Connection) -> pd.DataFrame:
    """Revenue, customer count, and order count broken down by country."""
    sql = """
        SELECT
            Country_clean                        AS Country,
            ROUND(SUM(Revenue), 2)               AS TotalRevenue,
            COUNT(DISTINCT "Customer ID")        AS UniqueCustomers,
            COUNT(DISTINCT Invoice)              AS OrderCount,
            ROUND(AVG(Revenue), 2)               AS AvgOrderRevenue
        FROM retail
        GROUP BY Country_clean
        ORDER BY TotalRevenue DESC
    """
    return pd.read_sql_query(sql, conn)


def get_customer_rfm(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Recency / Frequency / Monetary values per customer.

    Recency  = days between last purchase and the dataset's max date
    Frequency = distinct invoice count
    Monetary  = total spend
    """
    sql = """
        WITH ref AS (
            SELECT DATE(MAX(InvoiceDate)) AS ref_date FROM retail
        )
        SELECT
            "Customer ID"                                           AS CustomerID,
            CAST(JULIANDAY((SELECT ref_date FROM ref))
                 - JULIANDAY(MAX(DATE(InvoiceDate))) AS INTEGER)   AS Recency,
            COUNT(DISTINCT Invoice)                                 AS Frequency,
            ROUND(SUM(Revenue), 2)                                  AS Monetary
        FROM retail
        GROUP BY "Customer ID"
        ORDER BY Monetary DESC
    """
    return pd.read_sql_query(sql, conn)


def get_cohort_data(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    First purchase month per customer used as cohort label,
    then distinct customer count per (cohort, order_month) pair.
    """
    sql = """
        WITH first_purchase AS (
            SELECT
                "Customer ID",
                MIN(Month) AS CohortMonth
            FROM retail
            GROUP BY "Customer ID"
        )
        SELECT
            fp.CohortMonth,
            r.Month                         AS OrderMonth,
            COUNT(DISTINCT r."Customer ID") AS Customers
        FROM retail r
        JOIN first_purchase fp ON r."Customer ID" = fp."Customer ID"
        GROUP BY fp.CohortMonth, r.Month
        ORDER BY fp.CohortMonth, r.Month
    """
    return pd.read_sql_query(sql, conn)


def get_hourly_heatmap(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Revenue density by DayOfWeek (0=Mon) × Hour.
    Returns a pivot table ready for Plotly heatmap.
    """
    sql = """
        SELECT
            DayOfWeek,
            Hour,
            ROUND(SUM(Revenue), 2) AS TotalRevenue
        FROM retail
        GROUP BY DayOfWeek, Hour
        ORDER BY DayOfWeek, Hour
    """
    raw = pd.read_sql_query(sql, conn)
    pivot = raw.pivot(index="DayOfWeek", columns="Hour", values="TotalRevenue").fillna(0)
    pivot.index = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][: len(pivot)]
    return pivot


def get_kpi_summary(conn: sqlite3.Connection) -> dict:
    """Single-row KPI snapshot: revenue, orders, customers, AOV."""
    sql = """
        SELECT
            ROUND(SUM(Revenue), 2)              AS TotalRevenue,
            COUNT(DISTINCT Invoice)             AS TotalOrders,
            COUNT(DISTINCT "Customer ID")       AS UniqueCustomers,
            ROUND(SUM(Revenue)
                  / COUNT(DISTINCT Invoice), 2) AS AvgOrderValue
        FROM retail
    """
    row = pd.read_sql_query(sql, conn).iloc[0]
    return row.to_dict()


def get_last_two_months_revenue(conn: sqlite3.Connection) -> tuple[float, float]:
    """Return (current_month_revenue, previous_month_revenue) for delta cards."""
    sql = """
        SELECT Month, ROUND(SUM(Revenue), 2) AS TotalRevenue
        FROM retail
        GROUP BY Month
        ORDER BY Month DESC
        LIMIT 2
    """
    df = pd.read_sql_query(sql, conn)
    if len(df) >= 2:
        return df.iloc[0]["TotalRevenue"], df.iloc[1]["TotalRevenue"]
    if len(df) == 1:
        return df.iloc[0]["TotalRevenue"], 0.0
    return 0.0, 0.0


def get_weekly_revenue(conn: sqlite3.Connection) -> pd.DataFrame:
    """Aggregate revenue by ISO week for seasonality analysis."""
    sql = """
        SELECT
            STRFTIME('%Y-W%W', InvoiceDate)    AS Week,
            ROUND(SUM(Revenue), 2)              AS TotalRevenue,
            COUNT(DISTINCT Invoice)             AS OrderCount
        FROM retail
        GROUP BY Week
        ORDER BY Week
    """
    return pd.read_sql_query(sql, conn)


def get_revenue_by_dow(conn: sqlite3.Connection) -> pd.DataFrame:
    """Average and total revenue per day of week."""
    sql = """
        SELECT
            DayOfWeek,
            ROUND(SUM(Revenue), 2)  AS TotalRevenue,
            ROUND(AVG(Revenue), 2)  AS AvgRevenue,
            COUNT(DISTINCT Invoice) AS OrderCount
        FROM retail
        GROUP BY DayOfWeek
        ORDER BY DayOfWeek
    """
    df = pd.read_sql_query(sql, conn)
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    df["DayName"] = df["DayOfWeek"].apply(lambda x: day_labels[x] if x < 7 else str(x))
    return df


def get_yoy_revenue(conn: sqlite3.Connection) -> pd.DataFrame:
    """Year-over-year monthly revenue for multi-year datasets."""
    sql = """
        SELECT
            STRFTIME('%Y', InvoiceDate)    AS Year,
            STRFTIME('%m', InvoiceDate)    AS MonthNum,
            ROUND(SUM(Revenue), 2)          AS TotalRevenue
        FROM retail
        GROUP BY Year, MonthNum
        ORDER BY Year, MonthNum
    """
    return pd.read_sql_query(sql, conn)


def get_product_category_revenue(conn: sqlite3.Connection) -> pd.DataFrame:
    """Revenue by first word of product description (proxy for category)."""
    sql = """
        SELECT
            UPPER(SUBSTR(Description, 1,
                  CASE WHEN INSTR(Description, ' ') = 0
                       THEN LENGTH(Description)
                       ELSE INSTR(Description, ' ') - 1
                  END))                       AS Category,
            ROUND(SUM(Revenue), 2)             AS TotalRevenue,
            COUNT(DISTINCT StockCode)          AS ProductCount,
            SUM(Quantity)                      AS TotalQuantity
        FROM retail
        WHERE Description IS NOT NULL
        GROUP BY Category
        ORDER BY TotalRevenue DESC
        LIMIT 40
    """
    return pd.read_sql_query(sql, conn)
