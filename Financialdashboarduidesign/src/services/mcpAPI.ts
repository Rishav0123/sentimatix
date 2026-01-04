// MCP API service for AI-powered stock analysis
export interface MCPMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  metadata?: {
    symbol?: string; // Primary symbol if single stock
    symbols?: string[]; // List of symbols if comparison
    tool_status?: Record<string, string>;
    price_change?: number;
    sentiment_score?: number;
    correlation?: number;
    comparison_data?: any; // Store raw comparison result for UI hacks
  };
}

export interface PriceExplanation {
  symbol: string;
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  stock_summary?: {
    symbol: string;
    name: string;
    current_price: number | string;
    formatted_price?: string;
    change_percent: number;
    period: string;
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
    url?: string;
  }>;
  correlation: {
    correlation_coefficient: number;
    strength: string;
    interpretation: string;
    recommendation: string;
  } | null;
  news_sentiment?: Array<{
    title: string;
    source: string;
    published_at: string;
    sentiment?: string;
    sentiment_score?: number;
    url?: string;
  }>;
  insights?: {
    bottom_line: string;
    key_drivers: string[];
    risk_factors: string[];
    recommendation: string;
    confidence_level: string;
    market_themes: string[];
  };
  tool_status: Record<string, string>;
}

export interface ComparisonResult {
  comparison_summary: {
    period: string;
    stocks_analyzed: number;
    best_performer: string;
    worst_performer: string;
  };
  stock_comparison: Array<{
    symbol: string;
    rank: number;
    performance: {
      change_percent: number;
      change: number;
      current_price: number;
    };
    sentiment: {
      score: number;
      trend: string;
    };
    key_strength: string;
    key_weakness: string;
  }>;
  comparative_insights: {
    performance_leader: { symbol: string; reason: string };
    sentiment_leader: { symbol: string; reason: string };
  };
  recommendation_ranking: Array<{
    symbol: string;
    rating: string;
    rationale: string;
    confidence: string;
  }>;
}

export class MCPAPI {
  private baseURL: string;
  private apiKey: string;

  constructor(
    baseURL: string = (import.meta as any).env?.VITE_MCP_URL || 'https://mcp-pv1u.onrender.com',
    apiKey: string = (import.meta as any).env?.VITE_MCP_API_KEY || 'dev-key-12345'
  ) {
    // Force correct values to ensure connection works
    this.baseURL = baseURL;
    this.apiKey = apiKey;

    console.log('🔧 MCP API initialized:', { baseURL: this.baseURL, apiKey: this.apiKey });
  }

  /**
   * Parse natural language query to extract stock symbols and date range
   */
  private parseQuery(query: string): {
    symbols: string[];
    period: string | null;
    action: 'explain' | 'analyze' | 'compare' | 'unknown';
  } {
    const queryLower = query.toLowerCase();

    // Extract symbols with improved mapping
    const foundSymbols = new Set<string>();

    // Define comprehensive symbol mapping
    const symbolMappings: Record<string, string> = {
      // Major IT companies
      'tcs': 'TCS',
      'tata consultancy': 'TCS',
      'infosys': 'INFY',
      'infy': 'INFY',
      'wipro': 'WIPRO',
      'hcl tech': 'HCLTECH',
      'hcltech': 'HCLTECH',
      'tech mahindra': 'TECHM',

      // Banking sector
      'hdfc': 'HDFCBANK',
      'hdfc bank': 'HDFCBANK',
      'hdfcbank': 'HDFCBANK',
      'icici': 'ICICIBANK',
      'icici bank': 'ICICIBANK',
      'sbi': 'SBIN',
      'state bank': 'SBIN',
      'axis': 'AXISBANK',
      'axis bank': 'AXISBANK',
      'kotak': 'KOTAKBANK',
      'pnb': 'PNB',

      // Other major stocks
      'reliance': 'RELIANCE',
      'ril': 'RELIANCE',
      'airtel': 'BHARTIARTL',
      'bharti airtel': 'BHARTIARTL',
      'ntpc': 'NTPC',
      'ongc': 'ONGC',
      'ioc': 'IOC',
      'itc': 'ITC',
      'hul': 'HINDUNILVR',
      'hindustan unilever': 'HINDUNILVR',
      'bajaj finance': 'BAJFINANCE',
      'maruti': 'MARUTI',
      'asian paints': 'ASIANPAINT',
      'nestle': 'NESTLEIND',
      'titan': 'TITAN',
      'sun pharma': 'SUNPHARMA',
      'dr reddy': 'DRREDDY',
      'cipla': 'CIPLA',
      'tata steel': 'TATASTEEL',
      'jsw steel': 'JSWSTEEL',
      'hindalco': 'HINDALCO',
      'vedanta': 'VEDL',
      'adani enterprises': 'ADANIENT',
      'adani ports': 'ADANIPORTS',
      'power grid': 'POWERGRID',
      'ultratech': 'ULTRACEMCO',
      'mahindra': 'M&M',
      'tata motors': 'TATAMOTORS'
    };

    // Check for symbol mappings in the query
    // Sort keys by length descending to match longest phrases first (e.g. "HDFC Bank" before "HDFC")
    const sortedKeys = Object.keys(symbolMappings).sort((a, b) => b.length - a.length);

    let tempQuery = queryLower;

    for (const key of sortedKeys) {
      if (tempQuery.includes(key)) { // Use boundary check ideally, but keep simple for now
        // Simple replacement to avoid double matching substrings
        // But need to be careful. For now, just add to set.
        // A better way is to see if the word exists as a distinct token or phrase
        if (new RegExp(`\\b${key}\\b`).test(tempQuery)) {
          foundSymbols.add(symbolMappings[key]);
          // Don't remove from query to allow for context, but we handle the "HDFC Bank" vs "HDFC" via sort order
        }
      }
    }

    // Also look for explicit CAPS symbols like "INFY" or "RELIANCE" if they weren't caught
    const genericSymbolMatch = query.match(/\b([A-Z]{2,})\b/g);
    if (genericSymbolMatch) {
      genericSymbolMatch.forEach(sym => {
        const candidate = sym.toUpperCase();

        // 1. Check if it's a known mapped value (e.g. HDFCBANK)
        if (Object.values(symbolMappings).includes(candidate)) {
          foundSymbols.add(candidate);
          return;
        }

        // 2. Check if it's a known mapping key (e.g. HDFC -> HDFCBANK)
        const mappedValue = symbolMappings[candidate.toLowerCase()];
        if (mappedValue) {
          foundSymbols.add(mappedValue);
          return;
        }

        // 3. Heuristic for unknown symbols
        if (candidate.length >= 3 && !['THE', 'AND', 'FOR', 'WHO', 'WHY', 'HOW', 'WITH', 'BETWEEN'].includes(candidate)) {
          foundSymbols.add(candidate);
        }
      });
    }

    const symbols = Array.from(foundSymbols);

    // Determine time period
    let period: string | null = null;
    const daysMatch = queryLower.match(/(\d+)\s*days?/);
    const monthsMatch = queryLower.match(/(\d+)\s*months?/);

    if (daysMatch) {
      period = `${daysMatch[1]}days`;
    } else if (monthsMatch) {
      period = `${parseInt(monthsMatch[1]) * 30}days`;
    } else if (queryLower.includes('today')) {
      period = '1day';
    } else if (queryLower.includes('week')) {
      period = '7days';
    } else if (queryLower.includes('month')) {
      period = '30days';
    } else if (queryLower.includes('year')) {
      period = '365days';
    } else {
      period = '30days'; // Default
    }

    // Determine action
    let action: 'explain' | 'analyze' | 'compare' | 'unknown' = 'unknown';

    if (symbols.length > 1 || queryLower.includes('compare') || queryLower.includes('comparison') || queryLower.includes('vs') || queryLower.includes('versus')) {
      if (symbols.length >= 2) {
        action = 'compare';
      } else if (symbols.length === 1 && (queryLower.includes('compare') || queryLower.includes('vs'))) {
        // User asked to compare but only gave one symbol? Ambiguous. Fallback to analyze.
        action = 'analyze';
      } else if (symbols.length > 1) {
        action = 'compare';
      }
    } else if (symbols.length === 1) {
      action = 'analyze';
    }

    return { symbols, period, action };
  }

  /**
   * Calculate date range from period
   */
  private getDateRange(period: string): { start_date: string; end_date: string } {
    const endDate = new Date();
    const startDate = new Date();

    const daysMatch = period.match(/^(\d+)days?$/);

    if (daysMatch) {
      startDate.setDate(startDate.getDate() - parseInt(daysMatch[1]));
    } else {
      // Fallback
      startDate.setDate(startDate.getDate() - 30);
    }

    return {
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
    };
  }

  /**
   * Map Xdays to MCP period format (1d, 1w, 1m, 3m, 6m, 1y)
   */
  private getMCPPeriod(period: string): string {
    const daysMatch = period.match(/^(\d+)days?$/);
    if (!daysMatch) return '1m';
    const days = parseInt(daysMatch[1]);

    if (days <= 1) return '1d';
    if (days <= 7) return '1w';
    if (days <= 30) return '1m';
    if (days <= 90) return '3m';
    if (days <= 180) return '6m';
    return '1y';
  }

  /**
   * Format the single stock response
   */
  private formatResponse(data: PriceExplanation, query: string, dateRange?: { start_date: string, end_date: string }): string {
    console.log('📝 Raw Analysis Data:', JSON.stringify(data, null, 2));
    const { symbol, stock_summary, sentiment_aggregate, rag_evidence, news_sentiment, correlation } = data;

    if (!stock_summary || stock_summary.current_price === undefined) {
      return `⚠️ **Data Unavailable**\n\nCould not fetch analysis for ${symbol}. Please try another symbol.`;
    }

    let response = `**${symbol} Analysis**\n\n`;

    if (dateRange) {
      response += `📅 **Period:** ${dateRange.start_date} to ${dateRange.end_date}\n\n`;
    }

    // Price
    const change = stock_summary.change_percent || 0;
    const arrow = change >= 0 ? '📈' : '📉';

    let priceStr = '';
    if (stock_summary.formatted_price) {
      priceStr = stock_summary.formatted_price;
    } else if (typeof stock_summary.current_price === 'number') {
      priceStr = `₹${stock_summary.current_price.toFixed(2)}`;
    } else {
      priceStr = String(stock_summary.current_price || 'N/A');
    }

    response += `${arrow} **Price:** ${priceStr} (${change >= 0 ? '+' : ''}${change.toFixed(2)}%)\n\n`;

    // Sentiment
    if (sentiment_aggregate && !('error' in (sentiment_aggregate as any))) {
      const avgSent = sentiment_aggregate.avg_sentiment || 0;
      const totalArt = sentiment_aggregate.total_articles !== undefined ? sentiment_aggregate.total_articles : 0;
      const sentScore = avgSent * 100;

      response += `📊 **Sentiment:** ${sentScore > 5 ? 'Positive' : sentScore < -5 ? 'Negative' : 'Neutral'} (${Math.abs(sentScore).toFixed(1)}%)\n`;
      response += `Based on ${totalArt} articles.\n\n`;
    } else {
      response += `📊 **Sentiment:** Data Unavailable\n\n`;
    }

    // Recommendation - Prioritize insights recommendation over correlation recommendation
    const insights = data.insights;
    if (insights && insights.recommendation) {
      const confidence = insights.confidence_level || 'moderate';
      response += `💡 **Recommendation:** ${insights.recommendation} (Confidence: ${confidence.toLowerCase()})\n\n`;
    } else if (correlation && correlation.recommendation) {
      response += `💡 **Recommendation:** ${correlation.recommendation}\n\n`;
    } else {
      response += `💡 **Summary:** ${change > 0 ? 'Bullish' : 'Bearish'} trend observed.\n\n`;
    }

    // News Summary & Developments
    const marketThemes = insights?.market_themes || [];

    if (marketThemes && marketThemes.length > 0) {
      response += `📰 **Key News & Developments:**\n`;
      marketThemes.forEach((theme: string, i: number) => {
        response += `${i + 1}. ${theme}\n`;
      });
      response += `\n`;
    } else {
      // News - Merge RAG evidence and news_sentiment (Fallback)
      const ragNews = (rag_evidence && Array.isArray(rag_evidence)) ? rag_evidence : [];
      const standardNews = (news_sentiment && Array.isArray(news_sentiment)) ? news_sentiment : [];

      // Combine and normalize both sources
      const combinedNews = [
        ...ragNews.map(n => ({
          title: n.title,
          source: n.source || 'RAG Evidence',
          published_at: n.published_at,
          url: n.url,
          relevance_score: n.relevance_score || 50,
          sentiment: n.sentiment
        })),
        ...standardNews.map(n => ({
          title: n.title,
          source: n.source || 'News',
          published_at: n.published_at,
          url: n.url,
          relevance_score: (n as any).relevance_score || 50,
          sentiment: n.sentiment || (n.sentiment_score !== undefined ? (n.sentiment_score > 0 ? 'positive' : n.sentiment_score < 0 ? 'negative' : 'neutral') : 'neutral')
        }))
      ];

      // Deduplicate by title (case-insensitive)
      const seenTitles = new Set();
      const uniqueNews = combinedNews.filter(n => {
        if (!n.title) return false;
        const titleLower = n.title.toLowerCase().trim();
        if (seenTitles.has(titleLower)) return false;
        seenTitles.add(titleLower);
        return true;
      });

      // Sort by relevance score desc, then date desc
      uniqueNews.sort((a, b) => {
        const relDiff = (b.relevance_score || 0) - (a.relevance_score || 0);
        if (Math.abs(relDiff) > 0.1) return relDiff;
        return new Date(b.published_at).getTime() - new Date(a.published_at).getTime();
      });

      if (uniqueNews.length > 0) {
        response += `📰 **Key News & Developments:**\n`;
        uniqueNews.slice(0, 5).forEach((n: any, i) => {
          const source = n.source || 'News';
          const title = n.title || 'Untitled Article';
          const link = n.url ? `([link](${n.url}))` : '';
          response += `${i + 1}. **[${source}]** ${title} ${link}\n`;
        });
      } else {
        response += `*No specific news articles found for this period.*\n`;
      }
    }

    return response;
  }

  /**
   * Format the comparison response
   */
  /**
   * Format the comparison response
   */
  private formatComparisonResponse(data: ComparisonResult, symbols: string[]): string {
    console.log('📊 Raw Comparison Data for Formatting:', JSON.stringify(data, null, 2));

    if (!data || !data.comparison_summary) {
      console.error('❌ Missing comparison_summary in response:', data);
      return `⚠️ **Analysis Error**\n\nThe server returned an incomplete response. Please try again.\n\nRaw Data Received: ${JSON.stringify(data).substring(0, 100)}...`;
    }

    const { comparison_summary, stock_comparison, comparative_insights, recommendation_ranking } = data;

    let response = `**Stock Comparison: ${symbols.join(' vs ')}**\n`;
    response += `📅 **Period:** ${comparison_summary.period}\n\n`;

    // Winner
    if (comparison_summary.best_performer) {
      response += `🏆 **Best Performer:** ${comparison_summary.best_performer}\n`;
      response += `📉 **Lagging:** ${comparison_summary.worst_performer}\n\n`;
    }

    // Side by Side Table-like structure
    response += `📊 **Head-to-Head:**\n\n`;

    stock_comparison.forEach(stock => {
      const change = stock.performance.change_percent;
      const arrow = change >= 0 ? '🟢' : '🔴';
      const sentArrow = stock.sentiment.score > 0 ? '😊' : stock.sentiment.score < 0 ? '😟' : '😐';

      response += `**${stock.symbol}**\n`;
      response += `• Price: ${arrow} ${change > 0 ? '+' : ''}${change.toFixed(2)}%\n`;
      response += `• Sentiment: ${sentArrow} ${stock.sentiment.trend}\n`;
      response += `• Strength: ${stock.key_strength}\n`;
      response += `• Weakness: ${stock.key_weakness}\n\n`;
    });

    // Insights
    if (comparative_insights) {
      response += `💡 **Insights:**\n`;
      const pfLeader = comparative_insights.performance_leader;
      response += `• **${pfLeader.symbol}** leads in price due to ${pfLeader.reason.toLowerCase()}.\n`;
      response += `• **${comparative_insights.sentiment_leader.symbol}** has the strongest market sentiment.\n\n`;
    }

    // Recommendations
    if (recommendation_ranking && recommendation_ranking.length > 0) {
      response += `📝 **Recommendations:**\n`;
      recommendation_ranking.forEach(rec => {
        const icon = rec.rating === 'BUY' ? '✅' : rec.rating === 'SELL' ? '❌' : '✋';
        response += `${icon} **${rec.symbol}: ${rec.rating}** - ${rec.rationale}\n`;
      });
    }

    return response;
  }

  /**
   * Call MCP server to explain price change (Single Stock)
   */
  async explainPriceChange(
    symbol: string,
    startDate: string,
    endDate: string
  ): Promise<PriceExplanation> {
    // Reuse existing logic but with better error handling
    console.log('🔍 MCP Single Analysis:', symbol);

    const response = await fetch(`${this.baseURL}/call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': this.apiKey },
      body: JSON.stringify({
        name: 'explain_price_change', // This orchestrator tool calls analyze_stock_enhanced internally
        arguments: { symbol, start_date: startDate, end_date: endDate },
      }),
    });

    if (!response.ok) throw new Error(`MCP Error: ${response.statusText}`);
    const data = await response.json();
    if (!data.success) throw new Error(data.error);

    return data.result;
  }

  /**
   * Call MCP server to compare stocks
   */
  async compareStocks(
    symbols: string[],
    period: string = '1m'
  ): Promise<ComparisonResult> {
    console.log('🔍 MCP Comparison:', symbols);

    const response = await fetch(`${this.baseURL}/call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': this.apiKey },
      body: JSON.stringify({
        name: 'compare_stocks',
        arguments: {
          symbols: symbols,
          period: this.getMCPPeriod(period) // Convert '30days' to '1m'
        },
      }),
    });

    if (!response.ok) throw new Error(`MCP Error: ${response.statusText}`);
    const data = await response.json();
    if (!data.success) throw new Error(data.error);

    // Handle double-wrapped response from enhanced tools
    // Server returns: { success: true, result: { success: true, data: { ... } } }
    if (data.result && data.result.data) {
      return data.result.data as ComparisonResult;
    }

    return data.result as ComparisonResult;
  }

  /**
   * Process natural language query and return AI response
   */
  async processQuery(query: string): Promise<MCPMessage> {
    try {
      const parsed = this.parseQuery(query);

      if (parsed.symbols.length === 0) {
        return {
          role: 'assistant',
          content: `I couldn't identify any stock symbols. Try "Analyze TCS" or "Compare HDFC and ICICI".`,
          timestamp: new Date().toISOString(),
        };
      }

      const dateRange = this.getDateRange(parsed.period || '30days');

      let content = '';
      let metadata: any = {};

      if (parsed.action === 'compare') {
        // Perform Comparison
        const result = await this.compareStocks(parsed.symbols, parsed.period || '30days');
        content = this.formatComparisonResponse(result, parsed.symbols);
        metadata = { symbols: parsed.symbols, comparison_data: result };
      } else {
        // Default to Single Analysis (taking first symbol)
        const symbol = parsed.symbols[0];
        const explanation = await this.explainPriceChange(symbol, dateRange.start_date, dateRange.end_date);
        content = this.formatResponse(explanation, query, dateRange);
        metadata = {
          symbol: symbol,
          price_change: explanation.stock_summary?.change_percent,
          sentiment_score: explanation.sentiment_aggregate?.avg_sentiment
        };
      }

      return {
        role: 'assistant',
        content,
        timestamp: new Date().toISOString(),
        metadata
      };

    } catch (error) {
      console.error('Error processing query:', error);
      return {
        role: 'assistant',
        content: `❌ **Error:** ${error instanceof Error ? error.message : 'Unknown error occcurred during analysis.'}`,
        timestamp: new Date().toISOString(),
      };
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      return response.ok;
    } catch { return false; }
  }
}

export const mcpAPI = new MCPAPI();
