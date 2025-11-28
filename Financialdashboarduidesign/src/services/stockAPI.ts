// API service for fetching stock data
import { Stock } from '../components/StockTable';

export class StockAPI {
  private baseURL: string;

  constructor(baseURL: string = import.meta.env.VITE_API_URL || 'http://localhost:3001/api') {
    this.baseURL = baseURL;
  }

  /**
   * Fetch all stocks data
   * Expected API endpoint: GET /stocks
   * Expected response format:
   * [
   *   {
   *     "name": "Dr. Reddy's Laboratories",
   *     "ticker": "DRREDDY",
   *     "sector": "Healthcare",
   *     "index": "NIFTY Pharma",
   *     "country": "India",
   *     "price": "₹5,680.90",
   *     "change": 4.21,
   *     "volume": "1.2M",
   *     "marketCap": "₹945B",
   *     "sentiment": 85,
   *     "logo": "💊"
   *   },
   *   ...
   * ]
   */
  async getAllStocks(): Promise<Stock[]> {
    try {
      const response = await fetch(`${this.baseURL}/stocks`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!Array.isArray(data)) {
        throw new Error('Invalid data format: expected array');
      }
      
      // Validate each stock object has required fields
      data.forEach((stock, index) => {
        const requiredFields = ['name', 'ticker', 'sector', 'index', 'country', 'price', 'change', 'volume', 'marketCap', 'sentiment'];
        for (const field of requiredFields) {
          if (!(field in stock)) {
            throw new Error(`Missing required field '${field}' in stock at index ${index}`);
          }
        }
      });
      
      return data;
    } catch (error) {
      console.error('Error fetching stocks:', error);
      throw error;
    }
  }

  /**
   * Fetch specific stock data by ticker
   * Expected API endpoint: GET /stocks/{ticker}
   */
  async getStockByTicker(ticker: string): Promise<Stock> {
    try {
      const response = await fetch(`${this.baseURL}/stocks/${ticker}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Error fetching stock ${ticker}:`, error);
      throw error;
    }
  }

  /**
   * Fetch stocks filtered by sector
   * Expected API endpoint: GET /stocks?sector={sector}
   */
  async getStocksBySector(sector: string): Promise<Stock[]> {
    try {
      const response = await fetch(`${this.baseURL}/stocks?sector=${encodeURIComponent(sector)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!Array.isArray(data)) {
        throw new Error('Invalid data format: expected array');
      }
      
      return data;
    } catch (error) {
      console.error(`Error fetching stocks for sector ${sector}:`, error);
      throw error;
    }
  }

  /**
   * Fetch stocks with sentiment above threshold
   * Expected API endpoint: GET /stocks?sentiment_min={threshold}
   */
  async getStocksBySentiment(minSentiment: number): Promise<Stock[]> {
    try {
      const response = await fetch(`${this.baseURL}/stocks?sentiment_min=${minSentiment}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!Array.isArray(data)) {
        throw new Error('Invalid data format: expected array');
      }
      
      return data;
    } catch (error) {
      console.error(`Error fetching stocks with sentiment >= ${minSentiment}:`, error);
      throw error;
    }
  }
}

// Create a singleton instance
export const stockAPI = new StockAPI();