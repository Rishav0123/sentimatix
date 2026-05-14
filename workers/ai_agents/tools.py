from crewai.tools import BaseTool
import os
import httpx
from dotenv import load_dotenv

# Load environment variables for API connection
load_dotenv()

class FetchSentimatixNewsTool(BaseTool):
    name: str = "Fetch Sentimatix Stock News"
    description: str = "Fetches the latest news articles and sentiment scores for a given stock symbol from the Sentimatix API."
    
    def _run(self, stock_symbol: str) -> str:
        api_url = os.getenv("SENTIMATIX_API_URL")
        api_key = os.getenv("SENTIMATIX_API_KEY")
        
        if not api_url or not api_key:
            return "Error: Sentimatix API credentials not found in environment."
            
        try:
            # If the user passes 'RELIANCE', the API handles '.NS' conversion internally
            headers = {"Authorization": f"Bearer {api_key}"}
            params = {
                "symbols": stock_symbol,
                "limit": 10
            }
            
            with httpx.Client(timeout=20.0) as client:
                response = client.get(f"{api_url}/api/v1/news", headers=headers, params=params)
                response.raise_for_status()
                data_resp = response.json()
            
            news_items = data_resp.get("data", [])
            
            if not news_items:
                return f"No recent news found for {stock_symbol} via the Sentimatix API."
                
            # Format the output for the LLM with markdown links
            formatted_news = f"--- SENTIMATIX API EXTRACT FOR {stock_symbol} ---\n\n"
            for idx, article in enumerate(news_items, 1):
                sentiment = article.get('sentiment') or "UNSCORED"
                url = article.get('url', '')
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                published = article.get('published_at', '')[:10]  # date only
                
                link = f"[{title}]({url})" if url else title
                formatted_news += f"{idx}. **{link}**\n   - Source: {source} | Date: {published} | Sentiment: {sentiment.upper()}\n\n"
                
            return formatted_news
            
        except Exception as e:
            return f"API request failed: {str(e)}"
