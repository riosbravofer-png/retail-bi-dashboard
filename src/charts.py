"""
charts.py — Plotly figure builders.

Each function returns a go.Figure.
All charts share a dark theme with consistent typography and colour palette.
"""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------
DARK_BG      = "#0f1117"
CARD_BG      = "#1c1e26"
ACCENT       = "#00d4aa"
ACCENT2      = "#ff6b6b"
ACCENT3      = "#ffd166"
FONT_FAMILY  = "IBM Plex Mono, monospace"
PLOTLY_TMPL  = "plotly_dark"

_BASE_LAYOUT = dict(
    template=PLOTLY_TMPL,
    paper_bgcolor=CARD_BG,
    plot_bgcolor=CARD_BG,
    font=dict(family=FONT_FAMILY, size=12, color="#c9d1d9"),
    margin=dict(l=40, r=20, t=50, b=40),
    hoverlabel=dict(
        bgcolor=DARK_BG,
        font_size=12,
        font_family=FONT_FAMILY,
    ),
)


def _apply_base(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(title=dict(text=title, font=dict(size=15, color="#e6edf3")),
                      **_BASE_LAYOUT)
    return fig


# ---------------------------------------------------------------------------
# Executive Summary charts
# ---------------------------------------------------------------------------

def monthly_revenue_line(df: pd.DataFrame) -> go.Figure:
    """Line chart of monthly revenue with 3-month rolling average overlay."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Month"], y=df["TotalRevenue"],
        mode="lines+markers",
        name="Monthly Revenue",
        line=dict(color=ACCENT, width=2),
        marker=dict(size=5),
        hovertemplate="<b>%{x}</b><br>Revenue: £%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["Month"], y=df["RollingAvg3M"],
        mode="lines",
        name="3-Month Avg",
        line=dict(color=ACCENT3, width=2, dash="dash"),
        hovertemplate="<b>%{x}</b><br>3M Avg: £%{y:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(tickangle=-45)
    return _apply_base(fig, "Monthly Revenue Trend")


def country_revenue_bar(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Horizontal bar chart of top N countries by revenue."""
    top = df.head(top_n).sort_values("TotalRevenue")
    fig = go.Figure(go.Bar(
        x=top["TotalRevenue"],
        y=top["Country"],
        orientation="h",
        marker_color=ACCENT,
        hovertemplate="<b>%{y}</b><br>Revenue: £%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Revenue (£)", yaxis_title="")
    return _apply_base(fig, f"Top {top_n} Countries by Revenue")


# ---------------------------------------------------------------------------
# Product Intelligence charts
# ---------------------------------------------------------------------------

def top_products_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of top products by revenue."""
    sorted_df = df.sort_values("TotalRevenue")
    # truncate long descriptions
    labels = sorted_df["Description"].str[:40]
    fig = go.Figure(go.Bar(
        x=sorted_df["TotalRevenue"],
        y=labels,
        orientation="h",
        marker=dict(
            color=sorted_df["TotalRevenue"],
            colorscale=[[0, CARD_BG], [1, ACCENT]],
            showscale=False,
        ),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Revenue: £%{x:,.0f}<extra></extra>"
        ),
    ))
    fig.update_layout(
        xaxis_title="Revenue (£)",
        yaxis_title="",
        height=600,
    )
    return _apply_base(fig, "Top 20 Products by Revenue")


def product_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter: quantity vs revenue per product; bubble size = order count."""
    fig = go.Figure(go.Scatter(
        x=df["TotalQuantity"],
        y=df["TotalRevenue"],
        mode="markers",
        marker=dict(
            size=df["OrderCount"],
            sizemode="area",
            sizeref=2.0 * df["OrderCount"].max() / (40.0 ** 2),
            sizemin=4,
            color=df["TotalRevenue"],
            colorscale="Teal",
            showscale=True,
            colorbar=dict(title="Revenue £"),
        ),
        text=df["Description"].str[:30],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Quantity: %{x:,}<br>"
            "Revenue: £%{y:,.0f}<br>"
            "Orders: %{marker.size:,}<extra></extra>"
        ),
    ))
    fig.update_layout(
        xaxis_title="Total Quantity Sold",
        yaxis_title="Total Revenue (£)",
    )
    return _apply_base(fig, "Quantity vs Revenue per Product")


def category_treemap(df: pd.DataFrame) -> go.Figure:
    """Treemap of revenue by product category."""
    fig = px.treemap(
        df,
        path=["Category"],
        values="TotalRevenue",
        color="TotalRevenue",
        color_continuous_scale=["#1c1e26", ACCENT],
        template=PLOTLY_TMPL,
        hover_data={"ProductCount": True},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Revenue: £%{value:,.0f}<br>"
            "Products: %{customdata[0]}<extra></extra>"
        )
    )
    fig.update_layout(paper_bgcolor=CARD_BG, font_family=FONT_FAMILY,
                      coloraxis_showscale=False)
    return _apply_base(fig, "Revenue by Product Category")


# ---------------------------------------------------------------------------
# Customer Analytics charts
# ---------------------------------------------------------------------------

def rfm_scatter(rfm_df: pd.DataFrame) -> go.Figure:
    """RFM scatter: Recency vs Frequency, colour = Monetary quintile."""
    m_quantiles = pd.qcut(rfm_df["Monetary"], 5, labels=False, duplicates="drop")
    colors = [ACCENT, ACCENT3, ACCENT2, "#a78bfa", "#38bdf8"]
    fig = go.Figure()
    for q in sorted(m_quantiles.unique()):
        mask = m_quantiles == q
        sub  = rfm_df[mask]
        fig.add_trace(go.Scatter(
            x=sub["Recency"],
            y=sub["Frequency"],
            mode="markers",
            name=f"Monetary Q{int(q)+1}",
            marker=dict(color=colors[int(q) % len(colors)], size=5, opacity=0.7),
            hovertemplate=(
                "Recency: %{x}d<br>"
                "Frequency: %{y}<br>"
                "Monetary: £%{customdata:,.0f}<extra></extra>"
            ),
            customdata=sub["Monetary"],
        ))
    fig.update_layout(
        xaxis_title="Recency (days)",
        yaxis_title="Frequency (orders)",
        legend_title="Monetary Quintile",
    )
    return _apply_base(fig, "RFM: Recency vs Frequency")


def clv_histogram(rfm_df: pd.DataFrame) -> go.Figure:
    """Histogram of customer lifetime value (Monetary)."""
    clipped = rfm_df["Monetary"].clip(upper=rfm_df["Monetary"].quantile(0.98))
    fig = go.Figure(go.Histogram(
        x=clipped,
        nbinsx=60,
        marker_color=ACCENT,
        opacity=0.85,
        hovertemplate="Range: £%{x:.0f}<br>Customers: %{y}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Customer Lifetime Value (£)",
        yaxis_title="Number of Customers",
        bargap=0.05,
    )
    return _apply_base(fig, "Customer Lifetime Value Distribution")


def cohort_heatmap(retention: pd.DataFrame) -> go.Figure:
    """Heatmap of cohort retention rates (%)."""
    # keep only first 12 periods to avoid sparse right side
    cols = [c for c in sorted(retention.columns)[:12]]
    data = retention[cols]

    fig = go.Figure(go.Heatmap(
        z=data.values,
        x=[f"M+{c}" for c in cols],
        y=data.index.tolist(),
        colorscale=[[0, DARK_BG], [0.5, "#1a6b5e"], [1, ACCENT]],
        zmin=0, zmax=100,
        hovertemplate=(
            "Cohort: %{y}<br>"
            "Period: %{x}<br>"
            "Retention: %{z:.1f}%<extra></extra>"
        ),
        colorbar=dict(title="Retention %"),
    ))
    fig.update_layout(
        xaxis_title="Months since first purchase",
        yaxis_title="Cohort (first purchase month)",
        height=max(400, len(data) * 22),
    )
    return _apply_base(fig, "Customer Cohort Retention (%)")


def segment_bar(rfm_df: pd.DataFrame) -> go.Figure:
    """Bar chart of customer counts per RFM segment."""
    counts = rfm_df["Segment"].value_counts().reset_index()
    counts.columns = ["Segment", "Count"]
    colors_map = {
        "Champions":  ACCENT,
        "Loyal":      ACCENT3,
        "Potential":  "#38bdf8",
        "New":        "#a78bfa",
        "At Risk":    ACCENT2,
        "Lost":       "#6b7280",
    }
    fig = go.Figure(go.Bar(
        x=counts["Segment"],
        y=counts["Count"],
        marker_color=[colors_map.get(s, ACCENT) for s in counts["Segment"]],
        hovertemplate="<b>%{x}</b><br>Customers: %{y:,}<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Segment", yaxis_title="Customer Count")
    return _apply_base(fig, "Customers by RFM Segment")


# ---------------------------------------------------------------------------
# Time Intelligence charts
# ---------------------------------------------------------------------------

def hourly_heatmap(pivot: pd.DataFrame) -> go.Figure:
    """Revenue density heatmap: day-of-week rows × hour columns."""
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[[0, DARK_BG], [0.5, "#1a6b5e"], [1, ACCENT]],
        hovertemplate=(
            "Day: %{y}<br>"
            "Hour: %{x}<br>"
            "Revenue: £%{z:,.0f}<extra></extra>"
        ),
        colorbar=dict(title="Revenue £"),
    ))
    fig.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=320,
    )
    return _apply_base(fig, "Revenue Heatmap: Hour × Day of Week")


def weekly_revenue_line(df: pd.DataFrame) -> go.Figure:
    """Weekly revenue seasonality line chart."""
    fig = go.Figure(go.Scatter(
        x=df["Week"],
        y=df["TotalRevenue"],
        mode="lines",
        fill="tozeroy",
        fillcolor=f"rgba(0,212,170,0.15)",
        line=dict(color=ACCENT, width=1.5),
        hovertemplate="<b>%{x}</b><br>Revenue: £%{y:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(tickangle=-45)
    fig.update_layout(xaxis_title="Week", yaxis_title="Revenue (£)")
    return _apply_base(fig, "Weekly Revenue Seasonality")


def yoy_line(df: pd.DataFrame) -> go.Figure:
    """Year-over-year monthly revenue comparison."""
    palette = [ACCENT, ACCENT3, ACCENT2, "#a78bfa"]
    fig = go.Figure()
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for i, (year, grp) in enumerate(df.groupby("Year")):
        fig.add_trace(go.Scatter(
            x=grp["MonthNum"].astype(int).map(lambda m: month_labels[m - 1]),
            y=grp["TotalRevenue"],
            mode="lines+markers",
            name=str(year),
            line=dict(color=palette[i % len(palette)], width=2),
            hovertemplate=f"{year} — %{{x}}: £%{{y:,.0f}}<extra></extra>",
        ))
    fig.update_layout(xaxis_title="Month", yaxis_title="Revenue (£)",
                      legend_title="Year")
    return _apply_base(fig, "Year-over-Year Revenue Comparison")


def dow_bar(df: pd.DataFrame) -> go.Figure:
    """Bar chart of total revenue by day of week."""
    fig = go.Figure(go.Bar(
        x=df["DayName"],
        y=df["TotalRevenue"],
        marker_color=ACCENT,
        hovertemplate="<b>%{x}</b><br>Revenue: £%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Day of Week", yaxis_title="Revenue (£)")
    return _apply_base(fig, "Revenue by Day of Week")
