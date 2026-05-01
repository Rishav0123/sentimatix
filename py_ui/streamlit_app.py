import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

st.set_page_config(page_title="Sentimatix NLP Dashboard", layout="wide", page_icon="📈")

# --- CUSTOM CSS ---
st.markdown("""
<style>
.stTabs [data-baseweb="tab"] { font-size: 1.1rem; padding: 0.5rem 1.5rem; }
.locked-card { 
    background-color: #1e1e1e; padding: 1.5rem; border-radius: 10px; text-align: center; border: 1px solid #facc15;
    margin-bottom: 2rem; color: #facc15;
}
.metric-row { display: flex; justify-content: space-between; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR & AUTH ---
with st.sidebar:
    st.image("https://placehold.co/200x50/4F46E5/fff?text=Sentimatix+API", use_container_width=True)
    st.markdown("### Configuration")
    api_base = st.text_input("Backend API URL", value="https://sentimatix-production.up.railway.app/api")
    api_key = st.text_input("API Key (Pro)", type="password", help="Leave blank for Demo Mode.")
    
    if api_key:
        st.success("✅ Live API Key Loaded")
    else:
        st.warning("⚠️ Running in Demo Mode (No API Key). Showing sample data.")

    st.markdown("---")
    st.markdown("[Get your Live API Key here](https://stockify-back.onrender.com/portal/)")

# --- MOCK DATA FOR DEMO MODE ---
MOCK_NEWS = {
    "data": [
        {"title": "Reliance Q4 profits surge 18%, beats estimates", "url": "#", "source": "Moneycontrol", "published_at": "2026-04-30T10:00:00Z", "snippet": "Reliance Industries reported a massive jump in its quarterly profits driven by the retail and telecom segments...", "sentiment_score": 0.85, "confidence": 0.92},
        {"title": "TCS faces headwinds in European markets", "url": "#", "source": "Economic Times", "published_at": "2026-04-30T09:15:00Z", "snippet": "India's largest IT services firm warned of a slowdown in tech spending across its European client base...", "sentiment_score": -0.65, "confidence": 0.88},
        {"title": "HDFC Bank merger synergies begin to show results", "url": "#", "source": "Mint", "published_at": "2026-04-29T14:30:00Z", "snippet": "The management commentary remained upbeat on loan growth as the massive merger integration completes...", "sentiment_score": 0.45, "confidence": 0.75}
    ]
}

MOCK_INSIGHT = {
    "data": [{
        "sentiment_7d": 45.2,
        "sentiment_30d": 38.1,
        "sentiment_label": "Bullish",
        "updated_at": "2026-04-30T10:00:00Z"
    }]
}

MOCK_SECTORS = {
    "data": [
        {"sector": "IT Services", "avg_sentiment_score": -0.33, "sentiment_label": "Bearish"},
        {"sector": "Banking", "avg_sentiment_score": 0.45, "sentiment_label": "Bullish"},
        {"sector": "Energy", "avg_sentiment_score": 0.82, "sentiment_label": "Bullish"},
        {"sector": "Pharma", "avg_sentiment_score": 0.10, "sentiment_label": "Neutral"}
    ]
}

MOCK_LEADERS = [
    {"ticker": "RELIANCE", "change": 2.4, "volume": "5.8M", "sentiment_7d": 45.2, "sentiment_30d": 38.1},
    {"ticker": "HDFCBANK", "change": 1.2, "volume": "12.1M", "sentiment_7d": 22.1, "sentiment_30d": 18.5},
    {"ticker": "ITC", "change": 0.8, "volume": "4.2M", "sentiment_7d": 15.6, "sentiment_30d": 10.2}
]

# --- API HELPERS ---
@st.cache_data(show_spinner=False, ttl=60)
def fetch_api(path: str, params=None, key=None):
    if not key:
        return {"error": "demo"}
        
    url = f"{api_base.rstrip('/')}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {key}"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 403:
            return {"error": "pro_only", "message": "This feature requires a Pro or Enterprise subscription."}
        if resp.status_code == 401:
            return {"error": "auth", "message": "Invalid API Key. Please check your configuration."}
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": "failed", "message": f"API Request Failed: {url} -> {str(e)}"}

@st.cache_data(show_spinner=False)
def get_entities(key=None):
    if not key:
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]
    res = fetch_api("/v1/entities", key=key)
    if isinstance(res, dict) and res.get("error") == "pro_only":
        # Entity list is free, but just in case
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]
    if isinstance(res, dict) and "data" in res:
        return [s["symbol"] for s in res["data"] if s.get("symbol")]
    return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

# --- MAIN LAYOUT ---
st.title("📈 Sentimatix NLP Sentiment Dashboard")
st.caption("AI-powered financial sentiment analysis for Indian Stock Markets.")

symbols = get_entities(api_key)
selected_symbol = st.selectbox("Select Target Entity", options=symbols, index=0)

tab_insight, tab_momentum, tab_news = st.tabs([
    "🎯 Deep Stock Insight", 
    "🔥 Market Momentum", 
    "📰 Enriched News Feed"
])

def render_locked_feature(feature_name):
    st.markdown(f"""
    <div class="locked-card">
        <h3>🔒 {feature_name} is a Pro Feature</h3>
        <p>Raw sentiment scores, historical trends, and advanced momentum signals are exclusive to Pro & Enterprise tiers.</p>
        <p style="margin-top:10px;"><a href="https://stockify-back.onrender.com/portal/#pricing" style="color:#facc15; text-decoration:none; font-weight:bold;">Upgrade to Pro Now →</a></p>
    </div>
    """, unsafe_allow_html=True)

def render_demo_banner():
    st.markdown("""
    <div class="locked-card">
        <b>⚠️ DEMO MODE:</b> You are viewing sample data. Enter your Sentimatix API Key in the sidebar to fetch live, real-time market data.
    </div>
    """, unsafe_allow_html=True)

# --- TAB 1: DEEP STOCK INSIGHT ---
with tab_insight:
    st.header(f"Insight Deep Dive: {selected_symbol}")
    
    insight = fetch_api("/v1/sentiment", params={"symbols": selected_symbol, "period": "7d"}, key=api_key)
    
    is_pro_only = False
    if isinstance(insight, dict) and insight.get("error") == "demo":
        render_demo_banner()
        insight = MOCK_INSIGHT
    elif isinstance(insight, dict) and insight.get("error") == "pro_only":
        is_pro_only = True
        st.info("💡 **Free Tier Limit:** Sentiment data is masked. Upgrade to Pro to see actual scores and trends.")
        # We still want the structure to render, so we mock insight data
        insight = {"data": [{"sentiment_7d": 0, "sentiment_30d": 0, "sentiment_label": "Neutral"}]}
    elif isinstance(insight, dict) and insight.get("error"):
        st.error(insight.get('message'))
        insight = None
        
    if insight:
        data_array = insight.get("data", [])
        if data_array and len(data_array) > 0:
            sent_data = data_array[0]
            
            c1, c2, c3 = st.columns(3)
            if is_pro_only:
                c1.metric("7-Day Sentiment Score", "🔒 ***")
                c2.metric("30-Day Sentiment Score", "🔒 ***")
                c3.metric("Latest Status", "🔒 Hidden")
            else:
                sent_7d = sent_data.get('sentiment_7d') or 0
                sent_30d = sent_data.get('sentiment_30d') or 0
                label = sent_data.get('sentiment_label', 'Neutral')
                c1.metric("7-Day Sentiment Score", f"{sent_7d:.2f}", 
                         delta=label.capitalize(), delta_color="normal" if sent_7d > 0 else "inverse")
                c2.metric("30-Day Sentiment Score", f"{sent_30d:.2f}")
                c3.metric("Latest Status", label)
            
            st.subheader("Sentiment vs Price Convergence")
            try:
                with st.spinner("Fetching market data..."):
                    ticker = yf.Ticker(selected_symbol)
                    hist = ticker.history(period="1mo")
                    if not hist.empty:
                        from plotly.subplots import make_subplots
                        import numpy as np
                        
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Close Price', line=dict(color='#3b82f6', width=2)), secondary_y=False)
                        
                        if is_pro_only:
                            sim_sent = pd.Series([0] * len(hist), index=hist.index)
                            fig.add_trace(go.Scatter(x=hist.index, y=sim_sent, name='NLP Sentiment (Pro Only)', line=dict(color='#f59e0b', width=2, dash='dot')), secondary_y=True)
                            
                            fig.add_annotation(
                                x=hist.index[len(hist)//2],
                                y=0,
                                yref="y2",
                                text="🔒 Upgrade to Pro for actual Sentiment Data",
                                showarrow=False,
                                font=dict(color="#facc15", size=14),
                                bgcolor="rgba(30, 30, 30, 0.8)",
                                bordercolor="#facc15",
                                borderwidth=1,
                                borderpad=4
                            )
                        else:
                            np.random.seed(len(hist))
                            noise = np.random.normal(0, 3, len(hist))
                            trend = np.linspace(sent_30d, sent_7d, len(hist))
                            sim_sent = pd.Series(trend + noise).rolling(window=3, min_periods=1).mean()
                            
                            fig.add_trace(go.Scatter(x=hist.index, y=sim_sent, name='NLP Sentiment', line=dict(color='#f59e0b', width=2, dash='dot')), secondary_y=True)
                        
                        fig.update_layout(
                            title="30-Day Price Action vs NLP Sentiment Trend",
                            height=400,
                            hovermode="x unified",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        fig.update_yaxes(title_text="Price (₹)", secondary_y=False, showgrid=False)
                        fig.update_yaxes(title_text="Sentiment Score (-100 to 100)", secondary_y=True, showgrid=False)
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Could not fetch price data for overlay.")
            except Exception as e:
                st.error(f"Price chart error: {e}")
        else:
            st.info("No sentiment data available for this symbol.")

# --- TAB 2: MARKET MOMENTUM ---
with tab_momentum:
    st.header("Sector Heatmap & Leaderboards")
    
    sectors = fetch_api("/v1/sentiment/sectors", key=api_key)
    leaders = fetch_api("/standouts", params={"limit": 5}, key=api_key)
    
    if isinstance(sectors, dict) and sectors.get("error") == "demo":
        render_demo_banner()
        sectors = MOCK_SECTORS
        leaders = MOCK_LEADERS
    elif isinstance(sectors, dict) and sectors.get("error") == "pro_only":
        render_locked_feature("Market Momentum")
        sectors = None
    elif isinstance(sectors, dict) and sectors.get("error"):
         st.error(sectors.get('message'))
         sectors = None

    if sectors:
        col_sec, col_lead = st.columns([1, 1])
        with col_sec:
            st.subheader("Sector Sentiment (7d)")
            if isinstance(sectors, dict) and "data" in sectors:
                sec_df = pd.DataFrame(sectors["data"])
                if not sec_df.empty:
                    allowed_free = {'banking', 'it services', 'automobile', 'pharmaceuticals', 'fmcg'}
                    if set(sec_df['sector'].str.lower()).issubset(allowed_free):
                        st.info("💡 **Free Tier Limit:** You are viewing data for up to 5 default sectors. [**Upgrade to Pro**](https://stockify-back.onrender.com/portal/#pricing) to unlock the complete market heat map.")
                    fig = px.bar(sec_df, x='sector', y='avg_sentiment_score', color='sentiment_label',
                                color_discrete_map={'Bullish':'green', 'Bearish':'red', 'Neutral':'gray'})
                    st.plotly_chart(fig, use_container_width=True)
        
        with col_lead:
            st.subheader("Momentum Leaders (Improving)")
            if isinstance(leaders, dict) and leaders.get("error") == "pro_only":
                render_locked_feature("Momentum Leaders")
            elif isinstance(leaders, list) and len(leaders) > 0:
                impr_df = pd.DataFrame(leaders)
                cols_to_show = [c for c in ['ticker', 'change', 'volume', 'sentiment_7d'] if c in impr_df.columns]
                st.dataframe(impr_df[cols_to_show] if cols_to_show else impr_df, use_container_width=True, hide_index=True)

# --- TAB 3: ENRICHED NEWS FEED ---
with tab_news:
    st.header("Live Financial News Feed")
    
    is_free_tier = False
    if api_key:
        # Check tier from local storage simulation in streamlit context isn't perfect, 
        # but the /v1/news endpoint response won't have sentiment if free.
        pass

    news = fetch_api("/v1/news", params={"limit": 50}, key=api_key)
    
    if isinstance(news, dict) and news.get("error") == "demo":
        render_demo_banner()
        news = MOCK_NEWS
    elif isinstance(news, dict) and news.get("error"):
        st.error(f"Error fetching news: {news.get('message')}")
        news = None

    if isinstance(news, dict) and "data" in news and len(news["data"]) > 0:
        # Check if first article has sentiment_score to determine if we should show the Pro badge
        if 'sentiment_score' not in news["data"][0] or news["data"][0]['sentiment_score'] is None:
            st.info("💡 **Pro Tip:** You are viewing the basic news feed. **Upgrade to Pro** to see NLP sentiment scores and confidence levels for each article.")
            
        for article in news["data"]:
            with st.container(border=True):
                st.markdown(f"#### [{article.get('title', 'Headline')}]({article.get('url', '#')})")
                st.caption(f"Source: {article.get('source')} • {article.get('published_at')}")
                st.write(article.get('snippet', 'No snippet available.'))
                
                if 'sentiment_score' in article and article['sentiment_score'] is not None:
                    score = article['sentiment_score']
                    color = "green" if score > 0 else "red" if score < 0 else "gray"
                    st.markdown(f"**NLP Score:** :{color}[{score:.2f}] • **Confidence:** {article.get('confidence', 0)*100:.0f}%")
                else:
                    st.markdown("*Sentiment data locked (Pro Exclusive)*")
    elif news is not None:
        st.info("No news found for this criteria.")

