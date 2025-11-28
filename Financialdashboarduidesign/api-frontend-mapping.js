// API to Frontend Data Mapping for Stock Table
// Based on InsightsDashboard.tsx and StockTable.tsx

/* 
API ENDPOINT: GET /api/stocks
Returns array of objects with this structure:
{
  "symbol": "RELIANCE",           // Stock ticker
  "name": "Reliance Industries",  // Company name  
  "last_price": 2456.75,         // Current price
  "change": 45.67,               // Absolute price change
  "change_percent": 1.87,        // Percentage change
  "volume": 9800000,             // Trading volume
  "sentiment_score": 72.5        // Sentiment score (can be "None")
}
*/

// FRONTEND TABLE COLUMN MAPPING:

// 1. STOCK COLUMN (Name + Ticker)
// ================================
// Display Name: getStockName(apiStock.symbol) || apiStock.name
// - First tries hard-coded mapping based on symbol
// - Falls back to API-provided name
// - If both fail, shows the symbol itself

// Display Ticker: apiStock.symbol
// Logo: getStockLogo(apiStock.symbol) with fallback to "📈"

// Example mappings in code:
const stockNameMap = {
  'RELIANCE': 'Reliance Industries',
  'BHARTIARTL': 'Bharti Airtel',
  'M&M': 'Mahindra & Mahindra',
  // ... only 12 stocks mapped, rest show "Unknown"
};

// 2. SECTOR COLUMN
// ================
// Value: getStockSector(apiStock.symbol)
// - Hard-coded mapping based on symbol
// - No API field used, only frontend mapping
// - Unmapped stocks show "Unknown"

const sectorMap = {
  'RELIANCE': 'Energy',
  'BHARTIARTL': 'Telecom', 
  'HDFCBANK': 'Finance',
  'INFY': 'Technology',
  // ... only 12 stocks mapped, rest show "Unknown"
};

// 3. INDEX COLUMN  
// ===============
// Value: getStockIndex(apiStock.symbol)
// - Hard-coded mapping based on symbol
// - No API field used
// - Unmapped stocks show "NSE" as default

const indexMap = {
  'RELIANCE': 'NIFTY 50',
  'BHARTIARTL': 'NIFTY 50',
  'HDFCBANK': 'NIFTY 50',
  // ... only 12 stocks mapped, rest show "NSE"
};

// 4. PRICE COLUMN
// ===============
// Value: `₹${apiStock.last_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
// BUT: All showing ₹0.00 because API returns last_price: 0.0

// 5. CHANGE COLUMN
// ================
// Value: apiStock.change_percent
// Display: Shows as percentage with + or - and color coding
// BUT: All showing +0.00% because API returns change_percent: 0.0

// 6. VOLUME COLUMN
// ================
// Value: formatVolume(apiStock.volume)
// Converts: 1000000 → "1.0M", 1000 → "1.0K"  
// BUT: All showing 0 because API returns volume: 0

// 7. MARKET CAP COLUMN
// ====================
// Value: getMarketCap(apiStock.symbol)
// - Hard-coded mapping based on symbol
// - No API field used
// - Unmapped stocks show "₹0"

const marketCapMap = {
  'RELIANCE': '₹16.6T',
  'BHARTIARTL': '₹8.5T',
  'HDFCBANK': '₹12.5T',
  // ... only 12 stocks mapped, rest show "₹0"
};

// 8. SENTIMENT COLUMN
// ===================
// Value: typeof apiStock.sentiment_score === 'number' ? apiStock.sentiment_score : 50
// - Uses API sentiment_score if it's a number
// - Defaults to 50 if sentiment_score is "None" or missing
// - Your data shows real sentiment values like 64.82, 28.57, etc.

// SUMMARY OF ISSUES:
// ==================
// ✅ Working: symbol, name, sentiment_score
// ❌ Broken: last_price (always 0), change_percent (always 0), volume (always 0)  
// 🔧 Limited: sector, index, marketCap (only 12 stocks mapped, rest "Unknown"/"₹0")

console.log("This explains why you see:");
console.log("- Real stock tickers (LT, HINDZINC, etc.)");
console.log("- 'Unknown' sectors (only 12 stocks have sector mapping)");
console.log("- ₹0.00 prices (API returns last_price: 0)");
console.log("- 0 volumes (API returns volume: 0)");
console.log("- Real sentiment scores (API provides actual sentiment_score)");
console.log("- Mix of real names vs tickers (some mapped, some not)");