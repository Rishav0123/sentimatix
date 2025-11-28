# Backend API Integration Guide for Stock Data

## 🎯 Where to Add Your Backend API

The stock data you mentioned is currently hardcoded in `src/components/InsightsDashboard.tsx` in the `mockStocks` array (line 11-132).

### Option 1: Simple API Integration (Recommended for beginners)

Replace the hardcoded data in `InsightsDashboard.tsx` with an API call:

```typescript
// In src/components/InsightsDashboard.tsx

import { useState, useEffect } from "react";

export function InsightsDashboard({ onStockSelect }: InsightsDashboardProps) {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 🔥 ADD THIS API CALL
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const response = await fetch('YOUR_BACKEND_URL/api/stocks');
        const data = await response.json();
        setStocks(data);
      } catch (err) {
        console.error('Error:', err);
        setStocks(mockStocks); // Fallback to current data
      } finally {
        setLoading(false);
      }
    };

    fetchStocks();
  }, []);

  // Rest of your component...
}
```

### Option 2: Advanced API Integration (Custom Hook)

Use the custom hook I created in `src/hooks/useStockData.ts`:

```typescript
// In src/components/InsightsDashboard.tsx

import { useStockData } from "../hooks/useStockData";

export function InsightsDashboard({ onStockSelect }: InsightsDashboardProps) {
  const { stocks, loading, error, refetch } = useStockData();
  
  // Your existing filter logic here...
  
  return (
    <div className="space-y-6">
      {loading && <div>Loading...</div>}
      {error && <div>Error: {error}</div>}
      
      {/* Add refresh button */}
      <button onClick={refetch}>Refresh Data</button>
      
      {/* Your existing UI */}
      <StockTable stocks={filteredStocks} onStockClick={onStockSelect} />
    </div>
  );
}
```

## 📋 Required API Response Format

Your backend API should return data in this exact format:

```json
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
]
```

## 🔗 API Endpoints You Should Create

### 1. Get All Stocks
```
GET /api/stocks
```
Returns the complete list of stocks (like your current table)

### 2. Get Stock by Ticker
```
GET /api/stocks/{ticker}
```
Returns single stock data (e.g., `/api/stocks/DRREDDY`)

### 3. Filter by Sector
```
GET /api/stocks?sector=Healthcare
```
Returns only healthcare stocks

### 4. Filter by Sentiment
```
GET /api/stocks?sentiment_min=80
```
Returns stocks with sentiment >= 80

### 5. Real-time Updates (WebSocket)
```
ws://your-backend/stocks/updates
```
For live price/sentiment updates

## 🔧 Environment Variables

Add to your `.env` file:

```env
REACT_APP_API_URL=http://localhost:3001/api
REACT_APP_WS_URL=ws://localhost:3001
```

## 🚀 Quick Implementation Steps

1. **Set up your backend API** with the endpoints above
2. **Replace the mockStocks array** with API calls
3. **Add error handling** and loading states
4. **Test with your data** to ensure formatting matches

## 📁 Files to Modify

- `src/components/InsightsDashboard.tsx` - Main component with stock table
- `src/hooks/useStockData.ts` - Custom hook for API calls (already created)
- `src/services/stockAPI.ts` - API service class (already created)

## 🔄 Current Stock Data Location

Your exact stock data is currently in:
- **File:** `src/components/InsightsDashboard.tsx`
- **Variable:** `mockStocks` array (lines 11-132)
- **Used by:** `StockTable` component to display the table

Replace this array with your API data, and the table will automatically update!