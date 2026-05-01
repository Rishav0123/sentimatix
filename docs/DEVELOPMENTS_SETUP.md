# Stock Developments System - Setup Guide

## Quick Start

Your stock developments system is ready! Here's what was created:

### ✅ Files Created

1. **Database Schema**: `backend/sql/create_stock_developments.sql`
2. **MCP Tool**: `mcp/tools/identify_developments.py`
3. **Worker Script**: `worker-NLP/process_developments.py`
4. **Batch Runner**: `worker-NLP/run_developments.bat`
5. **API Endpoint**: Added to `backend/server.py`
6. **Frontend Component**: Updated `src/components/RecentDevelopments.tsx`

## Installation Steps

### 1. Create Database Table
```powershell
# Connect to your Supabase database and run:
cd d:\sentimetrix\backend\sql
psql -h your-db-host -U postgres -d stocksdb -f create_stock_developments.sql
```

Or use Supabase SQL Editor:
- Go to Supabase Dashboard → SQL Editor
- Copy contents of `create_stock_developments.sql`
- Click "Run"

### 2. Test the System

```powershell
# Test identifying developments for one stock
cd d:\sentimetrix\mcp\tools
python identify_developments.py
```

Expected output:
```
Processed TCS: Found 3 developments
  - [earnings] TCS Reports Strong Q2 Earnings
  - [product] TCS Launches New AI Platform
  - [partnership] TCS Partners with Google Cloud
```

### 3. Run Full Processing

```powershell
cd d:\sentimetrix\worker-NLP
python process_developments.py
```

This will:
- Fetch all active stocks
- Analyze last 24h news for each
- Identify key developments
- Store in database

### 4. Setup Hourly Automation (Windows)

1. Open **Task Scheduler**
2. Click "Create Task" (not "Create Basic Task")
3. **General Tab**:
   - Name: `Stock Developments Processor`
   - Description: `Hourly analysis of stock news to identify key developments`
   - Select "Run whether user is logged on or not"
   - Check "Run with highest privileges"

4. **Triggers Tab**:
   - Click "New..."
   - Begin the task: `On a schedule`
   - Settings: `Daily`
   - Recur every: `1 days`
   - Check "Repeat task every": `1 hour`
   - For a duration of: `Indefinitely`
   - Click OK

5. **Actions Tab**:
   - Click "New..."
   - Action: `Start a program`
   - Program/script: `D:\sentimetrix\worker-NLP\run_developments.bat`
   - Start in: `D:\sentimetrix\worker-NLP`
   - Click OK

6. **Settings Tab**:
   - Check "Allow task to be run on demand"
   - Check "Run task as soon as possible after a scheduled start is missed"
   - If the task fails, restart every: `5 minutes`
   - Attempt to restart up to: `3 times`

7. Click OK, enter your Windows password if prompted

### 5. Test the API

Start your backend server:
```powershell
cd d:\sentimetrix\backend
python server.py
```

Test the endpoint:
```
http://localhost:8000/api/developments?days=7&limit=10
```

With specific stock:
```
http://localhost:8000/api/developments?stock_symbol=TCS&days=14
```

### 6. View in Frontend

The `RecentDevelopments` component is already updated and will automatically fetch from the API. It's used in your dashboard pages.

## How It Works

```
Every Hour → Worker Script → Identify Developments → Store in DB → API → Frontend
```

**Categories Detected**:
- 📊 **Earnings**: quarterly results, profits, revenue
- 🤝 **Merger**: acquisitions, deals, takeovers
- ⚖️ **Regulatory**: approvals, compliance, licenses
- 🚀 **Product**: launches, new services
- 💰 **Financial**: dividends, buybacks
- 👔 **Management**: CEO changes, appointments
- 🤝 **Partnership**: collaborations
- 📈 **Expansion**: new facilities, growth

## Monitoring

### Check Logs
```powershell
# View today's log
Get-Content worker-NLP\logs\developments_20251125.log -Tail 50
```

### Query Database
```sql
-- Recent developments
SELECT * FROM stock_developments 
ORDER BY development_date DESC 
LIMIT 10;

-- Count by category
SELECT category, COUNT(*) as count
FROM stock_developments 
GROUP BY category 
ORDER BY count DESC;

-- Developments for specific stock
SELECT * FROM stock_developments 
WHERE symbol = 'TCS' 
ORDER BY development_date DESC;
```

## Customization

### Add More Categories

Edit `mcp/tools/identify_developments.py`:

```python
categories = {
    'earnings': ['earnings', 'profit', 'revenue', 'quarterly'],
    'your_category': ['keyword1', 'keyword2', 'keyword3'],
    # Add more...
}
```

### Change Processing Window

```python
# Default is 24 hours, change to 48:
developments = identify_key_developments(symbol, hours_back=48)
```

### Adjust Sentiment Thresholds

```python
if sentiment_score > 0.3:  # Default is 0.2
    sentiment = 'positive'
```

## Troubleshooting

**No developments found?**
- Check if news articles exist for the stock
- Verify Supabase connection (check .env file)
- Check date range (default is last 24h)

**API returns error?**
- Make sure backend server is running
- Check backend logs for errors
- Verify database table was created

**Frontend shows "Loading..."?**
- Check browser console (F12)
- Verify backend is running on port 8000
- Check CORS settings in backend

**Worker script fails?**
- Check Python path in batch file
- Verify Supabase credentials in .env
- Check logs in worker-NLP/logs/

## Next Steps

1. ✅ Run database migration
2. ✅ Test development identification
3. ✅ Set up hourly task
4. ✅ Start backend server
5. ✅ View in frontend

Your system is now automatically tracking stock developments every hour! 🎉
