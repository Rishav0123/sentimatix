
"""
Stokify Streamlit Dashboard — Polished Version

Usage:
1. pip install streamlit requests pandas plotly
2. Start backend: cd backend && python server.py
3. Run: streamlit run py_ui/streamlit_app.py

Features:
- API base URL selector
- Tabs: Dashboard, Price Data, News & Sentiment, Predictions
- Responsive layout, metrics, charts, tables
- Caching for API calls
- Error handling and refresh button
- Light/dark mode support
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from typing import Optional


st.set_page_config(page_title="Stokify Dashboard", layout="wide")
st.markdown("""
<style>
.stTabs [data-baseweb="tab"] {
    font-size: 1.1rem;
    padding: 0.5rem 1.5rem;
}
.stMetric { font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
        st.image("https://placehold.co/120x40/4F46E5/fff?text=Stokify", use_container_width=True)
        API_BASE = st.text_input("API base URL (include /api)", value="http://localhost:8000/api")
        REFRESH = st.button("🔄 Refresh data")



@st.cache_data(show_spinner=False, ttl=300)
def fetch_json(path: str, params: Optional[dict] = None):
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.sidebar.error(f"Failed to load {path}: {e}")
        return None


# Provide a simple helper to get stocks list
@st.cache_data(show_spinner=False)
def get_stocks():
    data = fetch_json("/stocks")
    if not data:
        return []
    return data



# Layout: top description
st.title("📊 Stokify — Python Dashboard")
st.caption("Interact with your FastAPI backend. Choose a stock, view charts, news, and predictions.")


# Load stocks and pick a symbol
stocks = get_stocks() or []
stock_symbols = [s.get("symbol") for s in stocks if s.get("symbol")]
selected = st.sidebar.selectbox("Choose stock", options=stock_symbols or ["TCS"], index=0 if stock_symbols else 0)


# Tabs
tabs = st.tabs(["Dashboard", "Price Data", "News & Sentiment", "Predictions"]) 


# DASHBOARD TAB
with tabs[0]:
    st.header(f"Market Overview — {selected}")
    overview = fetch_json("/market/overview") or {}
    col1, col2 = st.columns([2, 1])
    with col1:
        indices = overview.get("indices", [])
        if indices:
            st.subheader("Indices")
            idx_df = pd.DataFrame(indices)
            st.dataframe(idx_df, use_container_width=True, hide_index=True)
        st.subheader("Top Gainers")
        gainers = pd.DataFrame(overview.get("top_gainers", []))
        if not gainers.empty:
            st.dataframe(gainers, use_container_width=True, hide_index=True)
        st.subheader("Top Losers")
        losers = pd.DataFrame(overview.get("top_losers", []))
        if not losers.empty:
            st.dataframe(losers, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Quick Stock Snapshot")
        latest = next((s for s in stocks if s.get("symbol") == selected), None)
        if latest:
            st.metric("Last Price", f"{latest.get('last_price', 'N/A')}", delta=f"{latest.get('change', 0):.2f}")
            st.metric("Change %", f"{latest.get('change_percent', 0):.2f}%")
            st.metric("Volume", f"{latest.get('volume', 'N/A')}")
        else:
            st.info("Select a stock to see quick stats")
    st.divider()
    st.subheader("Price (last 90 days)")
    price_data = fetch_json(f"/stocks/{selected}/prices", params={"days": 90}) or []
    if price_data:
        pdf = pd.DataFrame(price_data)
        if 'date' in pdf.columns:
            pdf['date'] = pd.to_datetime(pdf['date'], errors='coerce')
            pdf = pdf.sort_values('date')
        fig = px.line(pdf, x='date', y='close', title=f"{selected} price", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No price history available for this symbol")



# PRICE DATA TAB
with tabs[1]:
    st.header(f"Price Data — {selected}")
    days = st.slider("Days of history", min_value=7, max_value=365, value=90, step=7)
    price_data = fetch_json(f"/stocks/{selected}/prices", params={"days": days}) or []
    if price_data:
        df = pd.DataFrame(price_data)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date')
        fig = px.area(df, x='date', y='close', title=f"{selected} Close Price — last {days} days", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.line_chart(df.set_index('date')[['open', 'close', 'high', 'low']], use_container_width=True)
    else:
        st.info("No price data found for selected stock")


# NEWS & SENTIMENT TAB
with tabs[2]:
    st.header(f"News & Sentiment — {selected}")
    news = fetch_json("/news", params={"stock_symbol": selected}) or []
    if news:
        ndf = pd.DataFrame(news)
    st.dataframe(ndf, use_container_width=True, hide_index=True)
    else:
        st.info("No news for selected stock")

    st.subheader("Sentiment Trend")
    trend = fetch_json("/news/sentiment/trend", params={"symbol": selected}) or []
    if trend:
        tdf = pd.DataFrame(trend)
        if 'date' in tdf.columns:
            tdf['date'] = pd.to_datetime(tdf['date'], errors='coerce')
            tdf = tdf.sort_values('date')
        if 'sentiment' in tdf.columns or 'avg_sentiment' in tdf.columns:
            ycol = 'sentiment' if 'sentiment' in tdf.columns else 'avg_sentiment' if 'avg_sentiment' in tdf.columns else list(tdf.columns[-1:])[0]
            fig = px.line(tdf, x='date', y=ycol, title=f"Sentiment trend for {selected}", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(tdf)
    else:
        st.info("No sentiment trend available")


# PREDICTIONS TAB
with tabs[3]:
    st.header(f"Model Predictions — {selected}")
    preds = fetch_json(f"/predictions/{selected}") or []
    if preds:
        pdf = pd.DataFrame(preds)
    st.dataframe(pdf, use_container_width=True, hide_index=True)
        latest = pdf.iloc[0]
        st.metric("Predicted Price", f"{latest.get('predicted_price', 'N/A')}", delta=f"{latest.get('predicted_change', 0):.2f}")
        st.metric("Confidence", f"{latest.get('confidence', 'N/A')}")
        st.write("Direction:", latest.get('direction', 'N/A'))
        if 'prediction_date' in pdf.columns:
            pdf['prediction_date'] = pd.to_datetime(pdf['prediction_date'], errors='coerce')
            pdf = pdf.sort_values('prediction_date')
        fig = px.line(pdf, x='prediction_date', y='predicted_price', title=f"Predicted Price Over Time", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No predictions available for selected stock")

# Refresh control

# Refresh control
if REFRESH:
    st.cache_data.clear()
    st.experimental_rerun()
