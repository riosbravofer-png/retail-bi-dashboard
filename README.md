# 🛍️ Retail Business Intelligence Dashboard

> An end-to-end data analytics project combining SQL, Python, and interactive dashboards
> to extract actionable insights from 225,000+ e-commerce transactions spanning 2009–2011.

## 🚀 Quick Start

```bash
# 1. Clone & enter the project
cd retail-bi-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the dashboard (dataset auto-generated on first run)
streamlit run app.py
```

The app opens at **http://localhost:8501**. No API keys, no external services — everything runs on SQLite in-memory.

---

## 📊 Key Findings

- **Thursday 11:00 drives peak revenue** — mid-week, mid-morning is consistently the highest-density trading window across the full dataset
- **UK accounts for 85.5% of revenue** — Germany, France, and EIRE are the top international markets with consistent growth potential
- **Top 20% of products generate ~80% of revenue** — a textbook Pareto distribution; the long tail of SKUs contributes minimally
- **Month-1 customer retention averages ~25%** — most customers do not return after first purchase; a post-purchase nurture sequence is the highest-leverage retention investment

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-5.20+-purple?logo=plotly)
![SQLite](https://img.shields.io/badge/SQLite-in--memory-lightgrey?logo=sqlite)
![Pandas](https://img.shields.io/badge/Pandas-2.2+-green?logo=pandas)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-orange?logo=scikit-learn)

---

## 📁 Project Structure

```
retail-bi-dashboard/
├── app.py                    # Main Streamlit app (4 pages + sidebar filters)
├── data/
│   └── online_retail.csv     # Dataset (auto-generated synthetic data on first run)
├── src/
│   ├── __init__.py
│   ├── data_loader.py        # Load/generate data; SQLite connection
│   ├── sql_queries.py        # All analytics SQL (parameterised, returns DataFrames)
│   ├── transformations.py    # Pandas cleaning, RFM, cohort computation
│   └── charts.py             # Plotly figure builders (one function per chart)
├── notebooks/
│   └── eda.ipynb             # Full analysis narrative (6 sections)
├── .streamlit/
│   └── config.toml           # Dark theme config
├── requirements.txt
└── README.md
```

---

## 📈 Dashboard Pages

### Executive Summary
KPI cards (Total Revenue · Orders · Customers · AOV), monthly revenue trend with 3-month rolling average, and top-10 countries bar chart. Metric delta shows last-month vs previous-month change.

### Product Intelligence
Top-20 products by revenue (horizontal bar), quantity-vs-revenue scatter with bubble sizing, and a treemap breaking revenue down by product category.

### Customer Analytics
RFM scatter coloured by monetary quintile, customer lifetime value histogram, RFM segment bar chart (Champions / Loyal / New / At Risk / Lost / Potential), and a full cohort retention heatmap.

### Time Intelligence
Hour × day-of-week revenue heatmap, weekly seasonality area chart, day-of-week bar chart, and year-over-year monthly comparison (data spans 2009–2011).

**All pages respect global sidebar filters**: date range picker, country multiselect, minimum order value slider.

---

## 🔍 Analysis Highlights (notebooks/eda.ipynb)

The notebook follows a six-section narrative:

1. **Data Acquisition** — load raw data, data dictionary, dtype overview
2. **Quality Assessment** — null heatmap, duplicate detection, IQR outlier analysis with box plots
3. **EDA** — revenue trends with annotations, product analysis, geographic choropleth
4. **RFM Segmentation** — quintile scoring, segment assignment, pie + profile table
5. **Statistical Insights** — peak hour/day, cohort retention, Pareto concentration curve, country growth analysis
6. **Business Recommendations** — 7 data-grounded findings

---

## 📈 Skills Demonstrated

- **Data cleaning & quality validation** — null handling, outlier detection (IQR), type coercion, deduplication
- **SQL query design** — window functions, CTEs, aggregations, JOINs, all via parameterised SQLite
- **Interactive visualisation** — Plotly Express + Graph Objects, 12+ chart types, consistent dark theme
- **Customer segmentation** — RFM analysis with quintile scoring, cohort retention tables
- **BI dashboard design** — multi-page Streamlit app with live filters, KPI cards, responsive layout
- **Statistical analysis** — Pareto/Lorenz curves, YoY comparison, seasonality decomposition

---

## 🗂️ Dataset

**Synthetic data** is generated on first run (500 k rows target, ~225 k after cleaning) using Faker + NumPy seeded for reproducibility. It faithfully mimics the UCI Online Retail II schema:

| Field | Description |
|---|---|
| Invoice | Unique order number |
| StockCode | Product SKU |
| Description | Product name |
| Quantity | Units ordered |
| InvoiceDate | Transaction datetime (Dec 2009 – Dec 2011) |
| Price | Unit price in GBP |
| Customer ID | Anonymised customer identifier |
| Country | Customer country |

To use the real dataset, download the [Online Retail II XLS from UCI](https://archive.ics.uci.edu/dataset/502/online+retail+ii), save either sheet as `data/online_retail.csv`, and re-run the app.

---

## 📄 License

MIT
