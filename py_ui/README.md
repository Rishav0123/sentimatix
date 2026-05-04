# 📈 Sentimatix NLP Dashboard

> AI-powered financial sentiment analysis for Indian Stock Markets — built with Streamlit.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](http://localhost:8501/)
[![Backend](https://img.shields.io/badge/Backend-Railway-0B0D0E?logo=railway&logoColor=white)](https://sentimatix-production.up.railway.app/api)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)

---

## Overview

The **Sentimatix Streamlit Dashboard** is an open-source, interactive frontend that visualises real-time NLP sentiment data sourced from the [Sentimatix API](https://sentimatix-production.up.railway.app/api). It is designed for developers and traders who want to explore financial sentiment signals for Indian equity markets without writing a single line of API code.

The dashboard supports two modes:

| Mode | Description |
|------|-------------|
| **Demo Mode** | No API key required. Runs on rich, curated sample data to showcase all features. |
| **Live Mode** | Enter a **Pro** API key to stream real-time, NLP-scored news and sentiment signals. |

---

## Features

### 🎯 Deep Stock Insight
- **7-Day & 30-Day Sentiment Scores** for any tracked Indian equity ticker.
- **Sentiment vs. Price Convergence Chart** — dual-axis Plotly chart overlaying live Yahoo Finance price data with the NLP sentiment trend.
- Sentiment label classification: `Bullish`, `Neutral`, `Bearish`.

### 🔥 Market Momentum
- **Sector Heatmap** — colour-coded bar chart showing average NLP sentiment across all major NIFTY sectors (IT, Banking, Energy, Pharma, FMCG, and more).
- **Momentum Leaders** — leaderboard of top improving tickers by sentiment delta, with live volume and price change data.

### 📰 Enriched News Feed
- Live financial news feed with article title, source, snippet, and publication time.
- **Pro Tier**: each article is enriched with an **NLP sentiment score** (−1 to +1) and a **confidence percentage** computed by the backend NLP pipeline.

### 🔒 Tier-Based Access Control
Features are transparently gated using the API subscription tier:

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| News Feed | ✅ Basic | ✅ + NLP Scores | ✅ + NLP Scores |
| Sector Heatmap | ✅ 5 sectors | ✅ Full market | ✅ Full market |
| Deep Stock Insight | 🔒 Masked | ✅ Full | ✅ Full |
| Momentum Leaders | 🔒 Locked | ✅ Full | ✅ Full |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| UI Framework | [Streamlit](https://streamlit.io/) |
| Charting | [Plotly](https://plotly.com/python/) |
| Market Data | [yfinance](https://github.com/ranaroussi/yfinance) |
| Data Wrangling | [Pandas](https://pandas.pydata.org/) |
| API Transport | [Requests](https://requests.readthedocs.io/) |

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- A Sentimatix API Key *(optional — Demo Mode works without one)*

### 1. Clone the repository

```bash
git clone https://github.com/your-org/sentimatix.git
cd sentimatix/py_ui
```

### 2. Install dependencies

```bash
pip install streamlit requests pandas plotly yfinance
```

### 3. Run the dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard will be available at `http://localhost:8501`.

---

## Configuration

All configuration is done **live within the sidebar** — no environment files needed.

| Setting | Default | Description |
|---------|---------|-------------|
| **Backend API URL** | `https://sentimatix-production.up.railway.app/api` | The Sentimatix REST API base URL. Change this to point at a local backend for development. |
| **API Key (Pro)** | *(empty)* | Your Sentimatix API Key. Leave blank to run in Demo Mode. |

> **Tip:** You can obtain a live API key at [sentimatix-production.up.railway.app/portal/](https://sentimatix-production.up.railway.app/portal/).

---

## Connecting to a Local Backend

If you are running the Sentimatix backend locally (e.g. for development), update the **Backend API URL** in the sidebar to:

```
http://localhost:8000/api
```

Refer to [`../backend/DEPLOY.md`](../backend/DEPLOY.md) for instructions on spinning up the FastAPI backend.

---

## Project Structure

```
py_ui/
└── streamlit_app.py   # Single-file Streamlit application
```

The dashboard is intentionally kept as a **single-file** application for maximum portability. All API helpers, mock data, and page rendering logic live in `streamlit_app.py`.

---

## Demo Mode Data

When running without an API key, the dashboard renders the following curated sample data:

- **News**: 3 sample articles from Moneycontrol, Economic Times, and Mint, with pre-scored NLP sentiment.
- **Insight**: Sample 7-day / 30-day scores for the selected symbol.
- **Sectors**: IT Services, Banking, Energy, and Pharma with example sentiment labels.
- **Leaders**: RELIANCE, HDFCBANK, and ITC with mock momentum metrics.

---

## API Reference

This dashboard consumes the following Sentimatix API endpoints:

| Endpoint | Tier | Description |
|----------|------|-------------|
| `GET /v1/entities` | Free | List of all tracked tickers |
| `GET /v1/news` | Free / Pro | Financial news feed (NLP scores on Pro) |
| `GET /v1/sentiment` | Pro | Per-symbol sentiment scores |
| `GET /v1/sentiment/sectors` | Free / Pro | Sector-level sentiment aggregates |
| `GET /standouts` | Pro | Momentum leaders leaderboard |

Full API documentation is available at [`/api-docs`](https://sentimatix-production.up.railway.app/api-docs).

---

## Contributing

Pull requests are welcome! If you'd like to add a new chart, fix a bug, or improve the UI, please:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feat/my-feature`).
3. Commit your changes.
4. Open a pull request against `main`.

---

## License

This project is licensed under the MIT License. See [`../LICENSE`](../LICENSE) for details.

---

<p align="center">Built with ❤️ using <a href="https://streamlit.io">Streamlit</a> · Powered by the <a href="https://sentimatix-production.up.railway.app/api">Sentimatix API</a></p>
