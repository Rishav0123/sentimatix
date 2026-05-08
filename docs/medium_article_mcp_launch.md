# I gave Claude Desktop a Bloomberg Terminal: Building an AI Agent for the Indian Stock Market

![Claude analyzing NSE stocks with Sentimatix](https://smithery.ai/badge/rishavdutta-kgp/sentimatix)

If you ask Claude 3.5 Sonnet or ChatGPT about the Indian stock market today, you’ll get a very polite "I'm sorry, my knowledge cutoff is..." 

Even with web search, AI agents struggle to parse the noise of Indian financial news. They don't know the difference between a random tweet and a market-sensitive exchange filing. They can't calculate sentiment trends across a 30-day window for Reliance Industries on the fly.

So I decided to fix that. I built **Sentimatix** — an intelligence layer that gives AI agents a real-time, sentiment-aware "Bloomberg Terminal" for the NSE and BSE.

---

## The Missing Link: Model Context Protocol (MCP)

Until a few months ago, getting an AI to use your custom data required complex "RAG" pipelines or custom-coded wrappers. But then Anthropic released the **Model Context Protocol (MCP)**.

MCP is a universal standard that lets you plug any data source directly into Claude Desktop, Cursor, or IDEs. Instead of chatting *about* data, the AI now has **Tools** to go and *get* the data itself.

I spent today launching the Sentimatix MCP server across the entire AI ecosystem. Here’s how the architecture looks:

1.  **FastAPI Backend**: A high-performance Python API that scrapes Indian financial news and uses a fine-tuned FinBERT model to score sentiment.
2.  **MCP Layer**: A "translator" that exposes my API tools (like `get_news_sentiment` and `get_sector_sentiment`) to AI agents.
3.  **The Distribution**: To make it accessible, I published it to **Smithery**, **Glama**, **PulseMCP**, and even **PyPI**.

---

## One Command to Rule the Market

The goal was to make this so easy that a trader with zero coding skills could use it. By packaging the server for PyPI, anyone can now give their Claude Desktop "Stock Market Superpowers" with just one command:

```powershell
pip install sentimatix-mcp
```

Once installed, Claude doesn't just guess anymore. When I ask, *"Why is Tata Motors down today?"*, Claude:
1.  Calls `getEntities` to find the correct symbol (`TATAMOTORS.NS`).
2.  Calls `getNews` to fetch the latest headlines and NLP sentiment scores.
3.  Synthesizes the data to give me a data-backed explanation.

---

## Scaling to the "Agent Blue Ocean"

We are entering a "Blue Ocean" where millions of people will have AI agents working for them. These agents need tools. By launching on **6 platforms (Smithery, Glama, PyPI, Claude, ChatGPT, and RapidAPI)**, I’m positioning Sentimatix to be the primary data source for any agent touching the Indian market.

If you’re a developer or a trader, the era of flying blind is over. You can now build your own algorithmic trading bots or AI analysts using the same data used by the pros.

### Ready to try it?
The entire project is open-source. You can find the MCP server, the API docs, and the installation guide below:

👉 **[Sentimatix on Smithery](https://smithery.ai/servers/rishavdutta-kgp/sentimatix)**
👉 **[GitHub Repository](https://github.com/Rishav0123/sentimatix)**

*If you found this useful, drop a ⭐ on GitHub — it helps me keep these tools free for the retail community!*
