// endpoints.js — Main content: all API endpoint reference cards

function tag(method) {
  const cls = method === 'GET' ? 'tag-get' : method === 'POST' ? 'tag-post' : 'tag-delete';
  return `<span class="method-tag ${cls}">${method}</span>`;
}

function paramsTable(params) {
  if (!params || !params.length) return '';
  let rows = params.map(p => `<tr>
    <td><span class="param-name">${p.name}</span></td>
    <td><span class="param-type">${p.type}</span></td>
    <td><span class="param-required ${p.required ? 'req' : 'opt'}">${p.required ? 'Required' : 'Optional'}</span></td>
    <td class="param-desc">${p.desc}</td>
    <td><span class="param-default">${p.default || '—'}</span></td>
  </tr>`).join('');
  return `<div class="params-label">Query Parameters</div>
  <table class="params-table">
    <thead><tr><th>Parameter</th><th>Type</th><th>Required</th><th>Description</th><th>Default</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function responseBlock(status, json) {
  return `<div class="response-label">Example Response</div>
  <div class="response-block">
    <div class="response-header">
      <span class="status-badge">● ${status} OK</span>
      <span style="color:var(--muted);font-size:11px;font-family:var(--mono)">application/json</span>
    </div>
    <pre class="response-pre">${json}</pre>
  </div>`;
}

const ENDPOINTS = [
  // =================== NEWS ===================
  {
    id: 'news', group: 'News Data', method: 'GET', path: '/api/v1/news',
    title: 'Get Financial News', desc: 'Fetch paginated financial news articles with NLP sentiment scores. Free tier users are restricted to the last 7 days and a 200-character snippet.',
    params: [
      { name: 'symbols', type: 'string', required: false, desc: 'Comma-separated NSE tickers (e.g. RELIANCE, TCS)', default: '—' },
      { name: 'sectors', type: 'string', required: false, desc: 'Comma-separated sectors (e.g. Banking, IT Services)', default: '—' },
      { name: 'sentiment', type: 'string', required: false, desc: 'positive, negative, neutral, or conflicted', default: '—' },
      { name: 'published_after', type: 'string', required: false, desc: 'Filter from date (YYYY-MM-DD)', default: '—' },
      { name: 'published_before', type: 'string', required: false, desc: 'Filter to date (YYYY-MM-DD)', default: '—' },
      { name: 'only_market_sensitive', type: 'boolean', required: false, desc: 'Filter for high-volatility news (Pro+)', default: 'false' },
      { name: 'limit', type: 'integer', required: false, desc: 'Results per page (Free: 3, Pro: 100)', default: '10' },
      { name: 'page', type: 'integer', required: false, desc: 'Pagination page', default: '1' }
    ],
    response: `{
  "meta": {
    "found": 4821,
    "returned": 2,
    "limit": 2,
    "page": 1,
    "total_pages": 2411
  },
  "data": [
    {
      "uuid": "40b41093-ff37-4ffd-b2e1-92a06bbd9df7",
      "title": "Reliance Q4 profits surge 18%",
      "snippet": "Reliance Industries reported strong financial results...",
      "url": "https://moneycontrol.com/...",
      "source": "moneycontrol.com",
      "published_at": "2026-04-29T15:39:10Z",
      "sentiment": "positive",
      "sentiment_score": 0.72,
      "confidence": 0.89,
      "is_market_sensitive": true,
      "entities": [
        {
          "symbol": "RELIANCE.NS",
          "name": "Reliance Industries",
          "sector": "Conglomerate",
          "country": "IN",
          "exchange": "NSE"
        }
      ]
    }
  ]
}`
  },
  // =================== ENTITIES ===================
  {
    id: 'entities', group: 'Reference Data', method: 'GET', path: '/api/v1/entities',
    title: 'List Stocks (Entities)', desc: 'Returns all active NSE-listed stocks tracked by Sentimatix. Use this to populate dropdowns or validate symbols.',
    params: [
      { name: 'search', type: 'string', required: false, desc: 'Search by company name or symbol (e.g. tata)', default: '—' },
      { name: 'sector', type: 'string', required: false, desc: 'Filter by exact sector name', default: '—' },
      { name: 'exchange', type: 'string', required: false, desc: 'Exchange filter', default: 'NSE' },
    ],
    response: `{
  "data": [
    {
      "symbol": "RELIANCE.NS",
      "name": "Reliance Industries",
      "sector": "Conglomerate",
      "exchange": "NSE",
      "country": "IN",
      "sentiment_7d": 31.13,
      "sentiment_30d": 25.32
    },
    {
      "symbol": "TCS.NS",
      "name": "Tata Consultancy Services",
      "sector": "IT Services",
      "exchange": "NSE",
      "country": "IN",
      "sentiment_7d": -55.04,
      "sentiment_30d": -55.04
    }
  ]
}`
  },
  // =================== SENTIMENT ===================
  {
    id: 'sentiment', group: 'Intelligence (Pro+)', method: 'GET', path: '/api/v1/sentiment',
    title: 'Stock Sentiment Signals', desc: 'Get actionable, pre-aggregated sentiment intelligence for specific stocks. (Requires Pro or Enterprise tier).',
    params: [
      { name: 'symbols', type: 'string', required: true, desc: 'Comma-separated NSE tickers (e.g. RELIANCE,TCS)', default: '—' },
      { name: 'period', type: 'string', required: false, desc: 'Timeframe for sentiment: "7d" or "30d"', default: '7d' },
    ],
    response: `{
  "data": [
    {
      "symbol": "RELIANCE.NS",
      "name": "Reliance Industries",
      "sector": "Conglomerate",
      "sentiment_7d": 31.13,
      "sentiment_30d": 25.32,
      "sentiment_label": "Bullish",
      "updated_at": "2026-04-30T00:34:43Z"
    }
  ]
}`
  },
  {
    id: 'sector-sentiment', group: 'Intelligence (Pro+)', method: 'GET', path: '/api/v1/sentiment/sectors',
    title: 'Sector Sentiment Signals', desc: 'Aggregate NLP sentiment scores grouped by entire market sectors. Useful for identifying macro-level market bias. (Requires Pro or Enterprise tier).',
    params: [
      { name: 'sectors', type: 'string', required: false, desc: 'Comma-separated sectors (e.g. Banking, Chemicals)', default: '—' },
      { name: 'period', type: 'string', required: false, desc: 'Timeframe for sentiment: "7d" or "30d"', default: '7d' },
    ],
    response: `{
  "period": "7d",
  "data": [
    {
      "sector": "IT Services",
      "avg_sentiment_score": -0.3369,
      "sentiment_label": "Bearish",
      "total_articles": 9
    },
    {
      "sector": "Pharmaceuticals",
      "avg_sentiment_score": -0.1095,
      "sentiment_label": "Neutral",
      "total_articles": 3
    }
  ]
}`
  }
];

function renderEndpoints() {
  const content = document.getElementById('content');
  if (!content) return;

  let currentGroup = '';
  let html = '';

  for (const ep of ENDPOINTS) {
    if (ep.group !== currentGroup) {
      currentGroup = ep.group;
      html += `<div class="endpoint-label">${currentGroup}</div>`;
    }

    const bodySection = ep.bodyFields ? `
      <div class="params-label" style="margin-top:16px">Request Body (JSON)</div>
      <table class="params-table">
        <thead><tr><th>Field</th><th>Type</th><th>Required</th><th>Description</th></tr></thead>
        <tbody>${ep.bodyFields.map(f => `<tr>
          <td><span class="param-name">${f.name}</span></td>
          <td><span class="param-type">${f.type}</span></td>
          <td><span class="param-required ${f.required ? 'req' : 'opt'}">${f.required ? 'Required' : 'Optional'}</span></td>
          <td class="param-desc">${f.desc}</td>
        </tr>`).join('')}</tbody>
      </table>` : '';

    html += `
    <div class="endpoint-section" id="section-${ep.id}">
      <div class="endpoint-title">${ep.title}</div>
      <p class="endpoint-desc">${ep.desc}</p>
      <div class="endpoint-url">
        ${tag(ep.method)}
        <span class="url-path">${ep.path}</span>
      </div>
      ${paramsTable(ep.params)}
      ${bodySection}
      ${responseBlock(200, ep.response)}
    </div>`;
  }

  content.innerHTML = html;
  if (typeof setupScrollSpy === 'function') setupScrollSpy();
}

renderEndpoints();
