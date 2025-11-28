# AI Chat Integration Guide

## Overview
Your frontend now has a **RAG-powered AI chat** that can explain stock price movements using real news, sentiment data, and correlation analysis.

## Architecture

```
User Query → MCP API → Orchestrator → [Stock Data + News + RAG Evidence] → Formatted Response
```

### Components Created:

1. **`src/services/mcpAPI.ts`** - MCP API client with natural language processing
2. **`src/components/AIChatPanel.tsx`** - Updated chat UI with MCP integration
3. **`.env.local`** - Environment configuration

## Setup Instructions

### 1. Install Dependencies (if needed)

The code uses standard React/TypeScript. No additional npm packages are required for basic functionality.

### 2. Start Required Services

You need **3 servers running**:

#### a) Backend API (Port 8000)
```powershell
cd d:\sentimetrix\backend
python server.py
```

#### b) MCP Server (Port 8001)
```powershell
cd d:\sentimetrix\mcp
$env:MCP_SERVER_PORT="8001"
$env:MCP_API_KEY="stockify-mcp-2025"
python run_server.py
```

#### c) Frontend Dev Server
```powershell
cd d:\sentimetrix\Financialdashboarduidesign
npm run dev
```

### 3. Access the Chat

- Open your app (usually http://localhost:5173)
- Click the AI chat button/icon in your UI
- The `AIChatPanel` will open

### 4. Test Queries

Try these natural language queries:

```
✅ "Why did HDFC Bank move up this month?"
✅ "Explain TCS price change"
✅ "What happened to Reliance this quarter?"
✅ "Why did Infosys drop last week?"
```

## How It Works

### Query Processing Flow:

1. **User types**: "Why did HDFC move up this month?"

2. **Parse Query** (`mcpAPI.parseQuery()`):
   - Extracts symbol: `HDFCBANK`
   - Determines period: `30days`
   - Identifies action: `explain`

3. **Date Calculation**:
   - Converts "this month" to actual date range
   - Example: `2025-10-18` to `2025-11-18`

4. **Call MCP Orchestrator**:
   ```typescript
   POST http://localhost:8001/call
   {
     "name": "explain_price_change",
     "arguments": {
       "symbol": "HDFCBANK",
       "start_date": "2025-10-18",
       "end_date": "2025-11-18"
     }
   }
   ```

5. **MCP Orchestrator Returns**:
   - Stock price summary (+/-%)
   - Historical prices
   - News sentiment (100 articles, avg 0.059)
   - **RAG Evidence** (6 GOOD matches, relevance 0.717-0.736)
   - Correlation analysis (0.207 - VERY_WEAK)

6. **Format Response** (`mcpAPI.formatResponse()`):
   - Creates readable markdown response
   - Highlights key news with relevance scores
   - Provides actionable insights

7. **Display to User**:
   ```
   **HDFCBANK Price Movement Analysis**
   
   HDFCBANK moved down by 0.05% (₹-0.45) to ₹996.55.
   
   📊 Sentiment Analysis:
   Overall sentiment is positive (5.9%), with 7 positive, 0 negative...
   
   📰 Key News & Events:
   1. **HDFC Bank Q2 earnings: Net profit rises 11%...**
      Relevance: 74% | Quality: GOOD
   ```

## Supported Stock Symbols

The system currently supports symbols with data in your database:

- **Banking**: HDFCBANK, ICICIBANK, SBILIFE
- **IT**: TCS, INFY, WIPRO
- **Conglomerate**: RELIANCE
- **Others**: Check your `news` and `stock_prices` tables

### Symbol Normalization

The API auto-normalizes:
- "HDFC Bank" → `HDFCBANK`
- "Infosys" → `INFY`
- "Reliance" / "RIL" → `RELIANCE`

## Customization

### 1. Add More Stock Mappings

Edit `mcpAPI.ts` → `parseQuery()` → `symbolPatterns`:

```typescript
const symbolPatterns = [
  /\b(hdfc\s*bank|hdfcbank)\b/i,
  /\b(state\s*bank|sbi)\b/i,  // Add more patterns
  // ...
];
```

### 2. Adjust Time Periods

Edit `mcpAPI.ts` → `parseQuery()`:

```typescript
if (queryLower.includes('today')) period = '1day';
else if (queryLower.includes('this week')) period = '7days';
// Add custom periods like "last 3 months"
```

### 3. Custom Response Format

Edit `mcpAPI.ts` → `formatResponse()` to change the output structure:

```typescript
response += `**${symbol} moved ${direction}...\n\n`;
// Add charts, tables, or custom sections
```

### 4. UI Styling

The chat uses Tailwind classes. Customize in `AIChatPanel.tsx`:

```tsx
// Change colors
className="bg-[#3B82F6]" // Blue accent
className="bg-[#111827]" // Dark background

// Change width
<div className="w-96"> // Make wider: w-[32rem]
```

## Troubleshooting

### "MCP Server offline" warning

- Check if port 8001 is in use: `netstat -ano | findstr :8001`
- Verify environment variables are set
- Check MCP logs: `d:\sentimetrix\mcp\logs\mcp_server_*.log`

### "No RAG evidence found"

- The vector DB may not have embeddings for that stock/period
- Run ingestion: `python mcp/scripts/ingest_historical.py --symbol SYMBOL`
- Check RAG stats: `GET http://localhost:8001/stats`

### "Could not identify stock symbol"

- Add the symbol to `symbolPatterns` in `mcpAPI.ts`
- Or use exact symbol: "Analyze HDFCBANK"

### Empty or error responses

1. Check all 3 servers are running
2. Verify `.env.local` URLs are correct
3. Check browser console for errors
4. Test MCP directly: 
   ```powershell
   curl http://localhost:8001/health
   ```

## Advanced Features

### Add Citations/Sources

Modify the response to include clickable news links:

```typescript
response += `📰 [${evidence.title}](${evidence.url}) (${evidence.source})\n`;
```

### Add Visualizations

Pass `metadata` to render charts:

```tsx
{message.metadata?.price_change && (
  <MiniChart data={message.metadata.historical_prices} />
)}
```

### Multi-Stock Comparison

Extend `mcpAPI.ts` to handle:
- "Compare HDFC vs ICICI"
- Call orchestrator for both symbols
- Format side-by-side comparison

## Performance Tips

1. **Cache responses**: Store recent queries in localStorage
2. **Debounce typing**: Wait for user to finish before calling API
3. **Stream responses**: Use Server-Sent Events for progressive display
4. **Pagination**: For long evidence lists, show "Load more"

## Next Steps

1. ✅ Test basic queries
2. Add more stock symbol mappings
3. Customize response formatting
4. Add visualization components
5. Implement conversation history
6. Add export/share functionality

## API Reference

### MCPMessage Interface
```typescript
interface MCPMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  metadata?: {
    symbol?: string;
    price_change?: number;
    sentiment_score?: number;
    correlation?: number;
  };
}
```

### Methods

- `mcpAPI.processQuery(query: string): Promise<MCPMessage>`
- `mcpAPI.explainPriceChange(symbol, startDate, endDate): Promise<PriceExplanation>`
- `mcpAPI.healthCheck(): Promise<boolean>`

---

**You're all set!** 🚀 The AI chat is ready to explain price movements with RAG-powered evidence.
