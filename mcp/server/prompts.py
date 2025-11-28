"""
LLM Prompt Templates for Stock Analysis

These prompts guide the LLM to produce structured, evidence-backed answers.
"""

SYSTEM_PROMPT = """You are an expert stock market analyst assistant with access to real-time market data, news, and sentiment analysis.

Your role is to:
1. Provide factual, data-driven analysis based on tool outputs
2. Cite specific sources with dates and URLs
3. Distinguish between facts and interpretations
4. Express confidence levels (HIGH/MEDIUM/LOW)
5. Never hallucinate data - only use information from tool calls

When analyzing price movements:
- Start with the numeric facts (percentage change, price levels)
- List top 3-5 contributing factors with evidence
- Provide correlation metrics when relevant
- Include timestamps and sources for all claims
- Suggest what additional data would increase confidence

Format your answers as:
**Quick Facts:** [numeric summary]
**Top Reasons:** [numbered list with evidence]
**Confidence Level:** [HIGH/MEDIUM/LOW] - [why]
**Sources:** [bulleted list with dates and URLs]
"""

EXPLAIN_PRICE_CHANGE_PROMPT = """Based on the tool outputs provided, explain why {symbol} price changed in the last {days} days.

Guidelines:
1. State the price change percentage and absolute values first
2. List the top 3 most significant contributing factors
3. For each factor, provide:
   - The specific news headline or event
   - The source and date
   - The sentiment score if available
   - Your assessment of impact (HIGH/MEDIUM/LOW)
4. Mention the correlation between sentiment and price if provided
5. State your confidence level and what would increase it
6. List all sources with URLs at the end

Be concise but thorough. Focus on causation supported by evidence.
"""

CORRELATION_ANALYSIS_PROMPT = """Analyze the correlation between sentiment and price for {symbol} over the period {start_date} to {end_date}.

Based on the correlation data provided:
1. State the correlation coefficient and what it means
2. Identify periods of strong agreement or divergence
3. Highlight any notable anomalies
4. Suggest potential explanations for the correlation pattern
5. Assess reliability of sentiment as a price predictor for this stock

Support all statements with specific data points from the tool outputs.
"""

MULTI_STOCK_COMPARISON_PROMPT = """Compare the performance and sentiment of {symbols} over the last {days} days.

For each stock, provide:
1. Price change percentage
2. Average sentiment score
3. Key news events
4. Relative performance ranking

Then provide:
- Which stock had the most positive sentiment?
- Which had the strongest price performance?
- Any divergences between sentiment and price?
- Correlation between the stocks' price movements?

Use the tool outputs to support all claims.
"""

RISK_ASSESSMENT_PROMPT = """Assess the risk profile for {symbol} based on recent data.

Analyze:
1. **Volatility**: Price swings in the period
2. **Sentiment stability**: Consistency of news sentiment
3. **Volume patterns**: Trading volume changes
4. **News risk**: Frequency and severity of negative news
5. **Correlation risk**: How it moves with broader market

Provide a risk score (LOW/MEDIUM/HIGH) with justification.
"""

def get_explanation_prompt(symbol: str, days: int, tool_outputs: dict) -> str:
    """Generate a prompt for explaining price changes"""
    return f"""
{EXPLAIN_PRICE_CHANGE_PROMPT.format(symbol=symbol, days=days)}

Here are the tool outputs:

**Stock Summary:**
```json
{tool_outputs.get('stock_summary', {})}
```

**Historical Prices:**
```json
{tool_outputs.get('historical_prices', [])[:5]}  # First 5 for brevity
```

**News & Sentiment:**
```json
{tool_outputs.get('news_sentiment', [])}
```

**RAG Evidence:**
```json
{tool_outputs.get('rag_evidence', [])}
```

**Correlation:**
```json
{tool_outputs.get('correlation', {})}
```

Now provide your analysis following the guidelines above.
"""

def get_citation_requirements() -> str:
    """Get the citation requirements to append to prompts"""
    return """
IMPORTANT: In your "Sources" section, list each source as:
- [Source Name] Headline... (YYYY-MM-DD) [URL if available]

Example:
**Sources:**
- [Bloomberg] Apple Q4 Earnings Miss Estimates (2025-11-10) https://...
- [Reuters] Tech Selloff Accelerates After Fed Minutes (2025-11-12) https://...
"""
