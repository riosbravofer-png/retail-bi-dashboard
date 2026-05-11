"""
app.py — Retail Business Intelligence Dashboard (Streamlit)

Navigation
----------
  Executive Summary   — KPIs, revenue trend, top countries
  Product Intelligence — top products, scatter, treemap
  Customer Analytics  — RFM, CLV, cohort retention
  Time Intelligence   — hourly heatmap, weekly + YoY trends
"""

from __future__ import annotations

import sqlite3

import pandas as pd
import streamlit as st

from src.data_loader import get_clean_data, get_sqlite_connection
from src.transformations import compute_rfm, compute_cohort
from src.sql_queries import (
    get_monthly_revenue,
    get_top_products,
    get_country_revenue,
    get_customer_rfm,
    get_cohort_data,
    get_hourly_heatmap,
    get_kpi_summary,
    get_last_two_months_revenue,
    get_weekly_revenue,
    get_revenue_by_dow,
    get_yoy_revenue,
    get_product_category_revenue,
)
from src import charts

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Retail BI Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');

      html, body, [class*="css"] { font-family: 'IBM Plex Mono', monospace; }

      .kpi-card {
          background: #1c1e26;
          border: 1px solid #2d2f3a;
          border-radius: 10px;
          padding: 18px 22px;
          text-align: center;
      }
      .kpi-label  { color: #8b949e; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; }
      .kpi-value  { color: #00d4aa; font-size: 26px; font-weight: 600; margin: 6px 0 4px; }
      .kpi-delta  { font-size: 12px; }
      .kpi-delta.pos { color: #3fb950; }
      .kpi-delta.neg { color: #f85149; }
      div[data-testid="stSidebar"] { background: #1c1e26; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_resource
def _build_connection(df: pd.DataFrame) -> sqlite3.Connection:
    return get_sqlite_connection(df)


@st.cache_data
def _cached_rfm(df: pd.DataFrame) -> pd.DataFrame:
    return compute_rfm(df)


@st.cache_data
def _cached_cohort(df: pd.DataFrame) -> pd.DataFrame:
    return compute_cohort(df)


df_full = get_clean_data()
conn    = _build_connection(df_full)

# ---------------------------------------------------------------------------
# Sidebar — global filters
# ---------------------------------------------------------------------------
st.sidebar.title("🛍️ Retail BI")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["Executive Summary", "Product Intelligence", "Customer Analytics", "Time Intelligence"],
    index=0,
)
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

# Date range
min_date = df_full["InvoiceDate"].dt.date.min()
max_date = df_full["InvoiceDate"].dt.date.max()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Country multiselect
all_countries = sorted(df_full["Country_clean"].unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Countries",
    options=all_countries,
    default=[],
    placeholder="All countries",
)

# Min order value
min_order_val = st.sidebar.slider(
    "Min Order Revenue (£)",
    min_value=0,
    max_value=500,
    value=0,
    step=10,
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Dataset: {len(df_full):,} transactions")


# ---------------------------------------------------------------------------
# Apply filters → filtered DataFrame + fresh SQLite connection
# ---------------------------------------------------------------------------
@st.cache_data
def apply_filters(
    _df: pd.DataFrame,
    date_start,
    date_end,
    countries: list[str],
    min_rev: float,
) -> pd.DataFrame:
    mask = (
        (_df["InvoiceDate"].dt.date >= date_start)
        & (_df["InvoiceDate"].dt.date <= date_end)
        & (_df["Revenue"] >= min_rev)
    )
    if countries:
        mask &= _df["Country_clean"].isin(countries)
    return _df[mask].copy()


start_date, end_date = (date_range if len(date_range) == 2
                        else (min_date, max_date))
df = apply_filters(df_full, start_date, end_date, selected_countries, min_order_val)

if df.empty:
    st.warning("No data matches the current filters. Adjust the sidebar settings.")
    st.stop()

# rebuild connection from filtered data
@st.cache_resource
def _filtered_conn(_df: pd.DataFrame, _key: str) -> sqlite3.Connection:
    return get_sqlite_connection(_df)


filter_key = f"{start_date}_{end_date}_{selected_countries}_{min_order_val}"
fconn = _filtered_conn(df, filter_key)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def kpi_card(label: str, value: str, delta: str = "", pos: bool = True) -> None:
    delta_class = "pos" if pos else "neg"
    delta_html  = f'<div class="kpi-delta {delta_class}">{delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# PAGE 1 — Executive Summary
# ===========================================================================
if page == "Executive Summary":
    st.title("Executive Summary")

    kpis                  = get_kpi_summary(fconn)
    cur_rev, prev_rev     = get_last_two_months_revenue(fconn)
    rev_delta_pct         = ((cur_rev - prev_rev) / prev_rev * 100) if prev_rev else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Revenue", f"£{kpis['TotalRevenue']:,.0f}")
    with c2:
        kpi_card("Total Orders", f"{int(kpis['TotalOrders']):,}")
    with c3:
        kpi_card("Unique Customers", f"{int(kpis['UniqueCustomers']):,}")
    with c4:
        kpi_card(
            "Avg Order Value",
            f"£{kpis['AvgOrderValue']:,.2f}",
            delta=f"{'▲' if rev_delta_pct >= 0 else '▼'} {abs(rev_delta_pct):.1f}% vs prev month",
            pos=rev_delta_pct >= 0,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])
    with col_left:
        monthly_df = get_monthly_revenue(fconn)
        st.plotly_chart(
            charts.monthly_revenue_line(monthly_df),
            width="stretch",
        )
    with col_right:
        country_df = get_country_revenue(fconn)
        st.plotly_chart(
            charts.country_revenue_bar(country_df, top_n=10),
            width="stretch",
        )


# ===========================================================================
# PAGE 2 — Product Intelligence
# ===========================================================================
elif page == "Product Intelligence":
    st.title("Product Intelligence")

    products_df  = get_top_products(fconn, n=20)
    category_df  = get_product_category_revenue(fconn)

    st.plotly_chart(charts.top_products_bar(products_df), use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(charts.product_scatter(products_df), use_container_width=True)
    with col_r:
        st.plotly_chart(charts.category_treemap(category_df), use_container_width=True)


# ===========================================================================
# PAGE 3 — Customer Analytics
# ===========================================================================
elif page == "Customer Analytics":
    st.title("Customer Analytics")

    rfm_df      = _cached_rfm(df)
    retention   = _cached_cohort(df)

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(charts.rfm_scatter(rfm_df), use_container_width=True)
    with col_r:
        st.plotly_chart(charts.clv_histogram(rfm_df), use_container_width=True)

    st.plotly_chart(charts.segment_bar(rfm_df), use_container_width=True)

    st.markdown("### Cohort Retention")
    st.plotly_chart(charts.cohort_heatmap(retention), use_container_width=True)


# ===========================================================================
# PAGE 4 — Time Intelligence
# ===========================================================================
elif page == "Time Intelligence":
    st.title("Time Intelligence")

    heatmap_pivot = get_hourly_heatmap(fconn)
    weekly_df     = get_weekly_revenue(fconn)
    dow_df        = get_revenue_by_dow(fconn)
    yoy_df        = get_yoy_revenue(fconn)

    st.plotly_chart(charts.hourly_heatmap(heatmap_pivot), use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(charts.weekly_revenue_line(weekly_df), use_container_width=True)
    with col_r:
        st.plotly_chart(charts.dow_bar(dow_df), use_container_width=True)

    if yoy_df["Year"].nunique() > 1:
        st.plotly_chart(charts.yoy_line(yoy_df), use_container_width=True)
    else:
        st.info("Year-over-year comparison requires data spanning at least 2 calendar years.")
