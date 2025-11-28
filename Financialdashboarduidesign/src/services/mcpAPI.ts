// MCP API service for AI-powered stock analysis
export interface MCPMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  metadata?: {
    symbol?: string;
    tool_status?: Record<string, string>;
    price_change?: number;
    sentiment_score?: number;
    correlation?: number;
  };
}

export interface PriceExplanation {
  symbol: string;
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  stock_summary: {
    symbol: string;
    current_price: number;
    change: number;
    change_percent: number;
    volatility: number;
  };
  sentiment_aggregate: {
    total_articles?: number;
    avg_sentiment: number;
    positive_count: number;
    negative_count: number;
    neutral_count: number;
  };
  rag_evidence: Array<{
    title: string;
    summary: string;
    source: string;
    published_at: string;
    sentiment: string;
    relevance_score: number;
    match_quality: string;
  }>;
  correlation: {
    correlation_coefficient: number;
    strength: string;
    interpretation: string;
    recommendation: string;
  } | null;
  tool_status: Record<string, string>;
}

export class MCPAPI {
  private baseURL: string;
  private apiKey: string;

  constructor(
    baseURL: string = import.meta.env.VITE_MCP_URL || 'http://localhost:8001',
    apiKey: string = import.meta.env.VITE_MCP_API_KEY || 'stockify-mcp-2025'
  ) {
    this.baseURL = baseURL;
    this.apiKey = apiKey;
  }

  /**
   * Parse natural language query to extract stock symbol and date range
   */
  private parseQuery(query: string): {
    symbol: string | null;
    period: string | null;
    action: 'explain' | 'analyze' | 'unknown';
  } {
    const queryLower = query.toLowerCase();
    
    // Extract symbol (common patterns)
    let symbol: string | null = null;
    const symbolPatterns = [
      /\b(hdfc\s*bank|hdfcbank)\b/i,
      /\b(tcs)\b/i,
      /\b(infy|infosys)\b/i,
      /\b(reliance|ril)\b/i,
      /\b(wipro)\b/i,
      /\b(icici\s*bank|icicibank)\b/i,
      /\b(sbi|state\s*bank)\b/i,
      /\b(axis\s*bank|axisbank)\b/i,
      /\b(kotak|kotak\s*bank)\b/i,
      /\b([A-Z]{2,})\b/,  // Generic uppercase symbols
    ];

    for (const pattern of symbolPatterns) {
      const match = query.match(pattern);
      if (match) {
        symbol = match[1].replace(/\s+/g, '').toUpperCase();
        // Normalize common names
        if (symbol === 'HDFCBANK' || symbol === 'HDFC') symbol = 'HDFCBANK';
        if (symbol === 'INFOSYS') symbol = 'INFY';
        if (symbol === 'RIL') symbol = 'RELIANCE';
        if (symbol === 'ICICIBANK' || symbol === 'ICICI') symbol = 'ICICIBANK';
        if (symbol === 'STATEBANK') symbol = 'SBILIFE';
        if (symbol === 'AXISBANK') symbol = 'AXISBANK';
        if (symbol === 'KOTAKBANK' || symbol === 'KOTAK') symbol = 'KOTAKBANK';
        break;
      }
    }

    // Determine time period - check from most specific to least specific
    let period: string | null = null;
    
    // Check for specific number of days/months
    const daysMatch = queryLower.match(/(\d+)\s*days?/);
    const weeksMatch = queryLower.match(/(\d+)\s*weeks?/);
    const monthsMatch = queryLower.match(/(\d+)\s*months?/);
    
    if (daysMatch) {
      const days = parseInt(daysMatch[1]);
      period = `${days}days`;
      console.log(`🔍 Detected: ${days} days`);
    } else if (weeksMatch) {
      const weeks = parseInt(weeksMatch[1]);
      period = `${weeks * 7}days`;
      console.log(`🔍 Detected: ${weeks} weeks = ${weeks * 7} days`);
    } else if (monthsMatch) {
      const months = parseInt(monthsMatch[1]);
      period = `${months * 30}days`;
      console.log(`🔍 Detected: ${months} months = ${months * 30} days`);
    } else if (queryLower.includes('today')) {
      period = '1day';
    } else if (queryLower.includes('yesterday')) {
      period = '2days';
    } else if (queryLower.includes('this week') || queryLower.includes('last week')) {
      period = '7days';
    } else if (queryLower.includes('this month') || queryLower.includes('last month')) {
      period = '30days';
    } else if (queryLower.includes('quarter') || queryLower.includes('q1') || queryLower.includes('q2') || queryLower.includes('q3') || queryLower.includes('q4')) {
      period = '90days';
    } else if (queryLower.includes('year') || queryLower.includes('ytd')) {
      period = '365days';
    } else {
      period = '30days'; // Default to 1 month
    }

    // Determine action - be very permissive, default to 'analyze' if symbol found
    let action: 'explain' | 'analyze' | 'unknown' = 'unknown';
    
    // Action keywords - very broad patterns
    const actionKeywords = [
      'why', 'what', 'how', 'tell', 'show', 'give', 'get',
      'explain', 'analyze', 'analysis', 'summary', 'summery',
      'performance', 'news', 'update', 'report', 'insight',
      'happened', 'going', 'doing', 'move', 'moved', 'change',
      'about', 'regarding', 'concerning', 'related',
      'look', 'check', 'see', 'view', 'find', 'search'
    ];

    const hasActionKeyword = actionKeywords.some(keyword => queryLower.includes(keyword));
    
    // If we found a symbol and any action-like keyword (or even without), treat as valid
    if (symbol) {
      if (hasActionKeyword || queryLower.split(' ').length <= 5) {
        // Short queries with symbol = likely want analysis
        action = 'analyze';
      } else {
        action = 'analyze'; // Default to analyze if symbol found
      }
    }

    return { symbol, period, action };
  }

  /**
   * Calculate date range from period
   */
  private getDateRange(period: string): { start_date: string; end_date: string } {
    const endDate = new Date();
    const startDate = new Date();

    // Extract number of days if period format is "Xdays"
    const daysMatch = period.match(/^(\d+)days?$/);
    
    if (daysMatch) {
      const days = parseInt(daysMatch[1]);
      startDate.setDate(startDate.getDate() - days);
    } else {
      // Fallback for legacy fixed periods
      switch (period) {
        case '1day':
          startDate.setDate(startDate.getDate() - 1);
          break;
        case '7days':
          startDate.setDate(startDate.getDate() - 7);
          break;
        case '30days':
          startDate.setDate(startDate.getDate() - 30);
          break;
        case '90days':
          startDate.setDate(startDate.getDate() - 90);
          break;
        case '365days':
          startDate.setDate(startDate.getDate() - 365);
          break;
        default:
          startDate.setDate(startDate.getDate() - 30);
      }
    }

    return {
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
    };
  }

  /**
   * Format the explanation into a natural language response
   */
  private formatResponse(data: PriceExplanation, query: string, dateRange?: {start_date: string, end_date: string}): string {
    const { symbol, stock_summary, sentiment_aggregate, rag_evidence, correlation, tool_status } = data;

    let response = '';

    // Check if we have price data
    if (!stock_summary || stock_summary.current_price === undefined || tool_status?.stock_summary === 'error') {
      response += `**${symbol} Analysis**\n\n`;
      response += `⚠️ **No price data available** for ${symbol} in the requested period.\n\n`;
      
      // Show what data we do have
      if (sentiment_aggregate && sentiment_aggregate.total_articles && sentiment_aggregate.total_articles > 0) {
        const sentimentDirection = sentiment_aggregate.avg_sentiment >= 0 ? 'positive' : 'negative';
        response += `📊 **Sentiment Analysis (Available):**\n`;
        response += `Found ${sentiment_aggregate.total_articles} articles with ${sentimentDirection} sentiment `;
        response += `(${(sentiment_aggregate.avg_sentiment * 100).toFixed(1)}%).\n\n`;
      }

      if (rag_evidence && rag_evidence.length > 0) {
        response += `📰 **Recent News:**\n`;
        rag_evidence.slice(0, 3).forEach((evidence, idx) => {
          response += `${idx + 1}. **${evidence.title}** (${evidence.source})\n`;
        });
        response += `\n`;
      }

      response += `💡 **Note:** This stock may not have price data in our database, or the symbol might be different. `;
      response += `Try these symbols: HDFCBANK, TCS, INFY, RELIANCE, ICICIBANK, AXISBANK, KOTAKBANK\n`;
      
      return response;
    }

    // Opening - we have price data
    const change = stock_summary.change_percent;
    const direction = change >= 0 ? 'up' : 'down';
    const absChange = Math.abs(change).toFixed(2);
    
    response += `**${symbol} Price Movement Analysis**\n\n`;
    
    // Show date range if provided
    if (dateRange) {
      const startFormatted = new Date(dateRange.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      const endFormatted = new Date(dateRange.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      response += `📅 **Period:** ${startFormatted} to ${endFormatted}\n\n`;
    }
    
    response += `${symbol} moved **${direction} by ${absChange}%** `;
    response += `(₹${stock_summary.change >= 0 ? '+' : ''}${stock_summary.change.toFixed(2)}) `;
    response += `to ₹${stock_summary.current_price.toFixed(2)}.\n\n`;

    // Sentiment analysis
    if (sentiment_aggregate && sentiment_aggregate.total_articles && sentiment_aggregate.total_articles > 0) {
      const sentimentDirection = sentiment_aggregate.avg_sentiment >= 0 ? 'positive' : 'negative';
      response += `📊 **Sentiment Analysis:**\n`;
      response += `Overall sentiment is ${sentimentDirection} (${(sentiment_aggregate.avg_sentiment * 100).toFixed(1)}%), `;
      response += `with ${sentiment_aggregate.positive_count} positive, `;
      response += `${sentiment_aggregate.negative_count} negative, and `;
      response += `${sentiment_aggregate.neutral_count} neutral articles.\n\n`;
    }

    // Key news evidence
    if (rag_evidence && rag_evidence.length > 0) {
      response += `📰 **Key News & Events:**\n`;
      const topEvidence = rag_evidence.slice(0, 3);
      topEvidence.forEach((evidence, idx) => {
        response += `${idx + 1}. **${evidence.title}** (${evidence.source})\n`;
        if (evidence.summary) {
          response += `   ${evidence.summary.substring(0, 150)}...\n`;
        }
        response += `   _Relevance: ${(evidence.relevance_score * 100).toFixed(0)}% | Quality: ${evidence.match_quality}_\n\n`;
      });
    } else {
      response += `📰 **Key News:** No significant news events found for this period.\n\n`;
    }

    // Correlation insight
    if (correlation) {
      response += `🔗 **Sentiment-Price Correlation:**\n`;
      response += `${correlation.interpretation}\n`;
      response += `**Recommendation:** ${correlation.recommendation}\n\n`;
    }

    // Summary
    response += `💡 **Summary:** `;
    if (Math.abs(change) < 1) {
      response += `${symbol} showed minimal movement with low volatility (${stock_summary.volatility?.toFixed(2) || 'N/A'}%). `;
    } else if (change > 5) {
      response += `${symbol} experienced strong gains, `;
    } else if (change < -5) {
      response += `${symbol} saw significant decline, `;
    } else {
      response += `${symbol} showed moderate ${direction}ward movement, `;
    }

    if (correlation && correlation.strength === 'VERY_STRONG') {
      response += `with sentiment strongly aligned to price action.`;
    } else if (correlation && correlation.strength === 'WEAK') {
      response += `though sentiment showed weak correlation to price movements.`;
    } else {
      response += `with moderate fundamental support.`;
    }

    return response;
  }

  /**
   * Call MCP server to explain price change
   */
  async explainPriceChange(
    symbol: string,
    startDate: string,
    endDate: string
  ): Promise<PriceExplanation> {
    try {
      const response = await fetch(`${this.baseURL}/call`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey,
        },
        body: JSON.stringify({
          name: 'explain_price_change',
          arguments: {
            symbol,
            start_date: startDate,
            end_date: endDate,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`MCP API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'MCP request failed');
      }

      return data.result;
    } catch (error) {
      console.error('Error calling MCP API:', error);
      throw error;
    }
  }

  /**
   * Process natural language query and return AI response
   */
  async processQuery(query: string): Promise<MCPMessage> {
    try {
      // Parse the query
      const parsed = this.parseQuery(query);

      if (!parsed.symbol) {
        return {
          role: 'assistant',
          content: `I couldn't identify a stock symbol in your query. Please mention a stock name or symbol.\n\n**Try these:**\n- "TCS news last month"\n- "Tell me about HDFC Bank"\n- "What's happening with Reliance?"\n- "Give me Infosys summary"\n- "Show me ICICI Bank updates"\n\n**Supported stocks:** HDFCBANK, TCS, INFY, RELIANCE, ICICIBANK, WIPRO, AXISBANK, KOTAKBANK`,
          timestamp: new Date().toISOString(),
        };
      }

      // Action is now auto-determined, no need to check for 'unknown'
      // Get date range
      const dateRange = this.getDateRange(parsed.period || '30days');

      console.log(`📅 Query parsed: Symbol=${parsed.symbol}, Period=${parsed.period}, DateRange=${dateRange.start_date} to ${dateRange.end_date}`);

      // Call MCP API
      const explanation = await this.explainPriceChange(
        parsed.symbol,
        dateRange.start_date,
        dateRange.end_date
      );

      // Format response
      const content = this.formatResponse(explanation, query, dateRange);

      return {
        role: 'assistant',
        content,
        timestamp: new Date().toISOString(),
        metadata: {
          symbol: explanation.symbol,
          tool_status: explanation.tool_status,
          price_change: explanation.stock_summary.change_percent,
          sentiment_score: explanation.sentiment_aggregate?.avg_sentiment || 0,
          correlation: explanation.correlation?.correlation_coefficient || 0,
        },
      };
    } catch (error) {
      console.error('Error processing query:', error);
      return {
        role: 'assistant',
        content: `I encountered an error while analyzing that query. Please make sure:\n\n1. The MCP server is running (http://localhost:8002)\n2. The backend API is running (http://localhost:8000)\n3. The stock symbol is valid\n\n**Error:** ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Create singleton instance
export const mcpAPI = new MCPAPI();
