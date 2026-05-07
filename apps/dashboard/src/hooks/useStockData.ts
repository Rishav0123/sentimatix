// Example: How to integrate your backend API for stock data
// This file shows you exactly where to put your API calls

import { useState, useEffect } from "react";
import { Stock } from "../components/StockTable";

// 🔥 THIS IS WHERE YOU PUT YOUR BACKEND API INTEGRATION 🔥

export const useStockData = () => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 🚀 REPLACE THIS URL WITH YOUR ACTUAL BACKEND API
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

  const fetchStocks = async () => {
    try {
      setLoading(true);
      setError(null);

      // 🔥 THIS IS THE API CALL FOR YOUR STOCK DATA 🔥
      const response = await fetch(`${API_BASE_URL}/stocks`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // 📋 YOUR API SHOULD RETURN DATA IN THIS FORMAT:
      /*
      [
        {
          "name": "Dr. Reddy's Laboratories",
          "ticker": "DRREDDY",
          "sector": "Healthcare",
          "index": "NIFTY Pharma",
          "country": "India",
          "price": "₹5,680.90",
          "change": 4.21,
          "volume": "1.2M",
          "marketCap": "₹945B",
          "sentiment": 85,
          "logo": "💊"
        },
        {
          "name": "Tata Consultancy Services",
          "ticker": "TCS",
          "sector": "Technology",
          "index": "NIFTY 50",
          "country": "India",
          "price": "₹3,850.60",
          "change": 2.15,
          "volume": "2.4M",
          "marketCap": "₹14.1T",
          "sentiment": 82,
          "logo": "💼"
        }
        // ... more stocks
      ]
      */

      setStocks(data);
    } catch (err) {
      console.error('Error fetching stocks:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch stock data');
      
      // 🔄 FALLBACK TO MOCK DATA IF API FAILS
      setStocks(MOCK_STOCKS);
    } finally {
      setLoading(false);
    }
  };

  // Fetch data when component mounts
  useEffect(() => {
    fetchStocks();
  }, []);

  return {
    stocks,
    loading,
    error,
    refetch: fetchStocks
  };
};

// 📊 MOCK DATA (Your current data structure)
const MOCK_STOCKS: Stock[] = [
  {
    name: "Dr. Reddy's Laboratories",
    ticker: "DRREDDY",
    sector: "Healthcare",
    index: "NIFTY Pharma",
    country: "India",
    price: "₹5,680.90",
    change: 4.21,
    volume: "1.2M",
    marketCap: "₹945B",
    sentiment: 85,
    logo: "💊",
  },
  {
    name: "Tata Consultancy Services",
    ticker: "TCS",
    sector: "Technology",
    index: "NIFTY 50",
    country: "India",
    price: "₹3,850.60",
    change: 2.15,
    volume: "2.4M",
    marketCap: "₹14.1T",
    sentiment: 82,
    logo: "💼",
  },
  {
    name: "Sun Pharmaceutical",
    ticker: "SUNPHARMA",
    sector: "Healthcare",
    index: "NIFTY Pharma",
    country: "India",
    price: "₹1,678.40",
    change: 2.89,
    volume: "3.2M",
    marketCap: "₹4.0T",
    sentiment: 80,
    logo: "☀️",
  },
  {
    name: "Infosys Limited",
    ticker: "INFY",
    sector: "Technology",
    index: "NIFTY 50",
    country: "India",
    price: "₹1,482.30",
    change: 3.45,
    volume: "8.2M",
    marketCap: "₹6.2T",
    sentiment: 78,
    logo: "🏢",
  }
];

// 🔗 ADDITIONAL API ENDPOINTS YOU CAN CREATE:

// Get stock by ticker
export const fetchStockByTicker = async (ticker: string): Promise<Stock> => {
  const response = await fetch(`${import.meta.env.VITE_API_URL}/stocks/${ticker}`);
  if (!response.ok) throw new Error('Failed to fetch stock');
  return response.json();
};

// Get stocks by sector
export const fetchStocksBySector = async (sector: string): Promise<Stock[]> => {
  const response = await fetch(`${import.meta.env.VITE_API_URL}/stocks?sector=${sector}`);
  if (!response.ok) throw new Error('Failed to fetch stocks');
  return response.json();
};

// Get top performing stocks
export const fetchTopPerformers = async (limit: number = 10): Promise<Stock[]> => {
  const response = await fetch(`${import.meta.env.VITE_API_URL}/stocks/top-performers?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch top performers');
  return response.json();
};

// Real-time stock updates (WebSocket)
export const subscribeToStockUpdates = (callback: (stock: Stock) => void) => {
  const ws = new WebSocket(`${import.meta.env.VITE_WS_URL}/stocks/updates`);
  
  ws.onmessage = (event) => {
    const stock = JSON.parse(event.data);
    callback(stock);
  };
  
  return () => ws.close();
};