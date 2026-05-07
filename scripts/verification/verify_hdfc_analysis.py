import sys
import os
import logging
from unittest.mock import patch, MagicMock
import asyncio

# Ensure d:\sentimatix is in path so we can import 'mcp'
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), '..'))

# Import the module via correct path for patching
from mcp.server.tools import enhanced_analysis

logging.basicConfig(level=logging.CRITICAL) # Suppress all logs

async def test_logic_flow():
    print("Starting verification (Logs suppressed - writing to file)...")

    # Setup async future helper
    def async_return(result):
        f = asyncio.Future()
        f.set_result(result)
        return f

    # Patch the names in the mcp.server.tools.enhanced_analysis module
    with patch('mcp.server.tools.enhanced_analysis.get_stock_summary') as mock_stock_sum, \
         patch('mcp.server.tools.enhanced_analysis.get_technical_analysis') as mock_ta, \
         patch('mcp.server.tools.enhanced_analysis.get_news_sentiment') as mock_news, \
         patch('mcp.server.tools.enhanced_analysis.get_sentiment_aggregate') as mock_sent_agg, \
         patch('mcp.server.tools.enhanced_analysis.get_rag_evidence') as mock_rag, \
         patch('mcp.server.tools.enhanced_analysis.calculate_sentiment_price_correlation') as mock_correlation:
            
        # Configure mocks
        mock_stock_sum.return_value = {
            "current_price": 1500, "change_percent": 1.5, "change": 22.5, 
            "volatility": 1.2, "symbol": "HDFCBANK"
        }
        # mock_ta needs to return an awaitable
        mock_ta.side_effect = lambda *args, **kwargs: async_return({"rsi": 50, "macd": "neutral"})
        
        mock_news.return_value = [{"title": "News 1", "sentiment": "positive", "relevance_score": 90}]
        mock_sent_agg.return_value = {"avg_sentiment": 0.5, "total_articles": 10}
        mock_rag.return_value = []
        mock_correlation.return_value = {"correlation": 0.8}
        
        symbol = "HDFCBANK"
        
        with open("verification_output.txt", "w") as f:
            f.write("Starting verification...\n")
            
            # Test 1: Technical Analysis Only
            f.write("\n--- Test 1: Technical Analysis Only ---\n")
            mock_news.reset_mock()
            mock_ta.reset_mock()
            
            result_tech = await enhanced_analysis.analyze_stock_enhanced(
                symbol=symbol, period="6m", analysis_type="technical"
            )
            
            if result_tech.get("success"):
                data = result_tech["data"]
                tech_present = data.get("technical_analysis") is not None
                news_present = bool(data.get("key_events"))
                
                f.write(f"Technical Analysis Present: {tech_present}\n")
                f.write(f"News Present: {news_present}\n")
                f.write(f"get_technical_analysis called: {mock_ta.called}\n")
                f.write(f"get_news_sentiment called: {mock_news.called}\n")
                
                if mock_ta.called and not mock_news.called:
                    f.write("PASS: Correctly filtered for technical analysis.\n")
                else:
                    f.write("FAIL: Incorrect function calls.\n")
            else:
                f.write(f"Technical Analysis Failed: {result_tech.get('message')}\n")

            # Test 2: Fundamental Analysis Only
            f.write("\n--- Test 2: Fundamental Analysis Only ---\n")
            mock_news.reset_mock()
            mock_ta.reset_mock()
            
            result_fund = await enhanced_analysis.analyze_stock_enhanced(
                symbol=symbol, period="6m", analysis_type="fundamental"
            )
            
            if result_fund.get("success"):
                data = result_fund["data"]
                tech_present = bool(data.get("technical_analysis"))
                news_present = bool(data.get("key_events"))
                
                f.write(f"Technical Analysis Present: {tech_present}\n")
                f.write(f"News Present: {news_present}\n")
                f.write(f"get_technical_analysis called: {mock_ta.called}\n")
                f.write(f"get_news_sentiment called: {mock_news.called}\n")
                
                if mock_news.called and not mock_ta.called:
                    f.write("PASS: Correctly filtered for fundamental analysis.\n")
                else:
                    f.write("FAIL: Incorrect function calls.\n")
            else:
                f.write(f"Fundamental Analysis Failed: {result_fund.get('message')}\n")

if __name__ == "__main__":
    asyncio.run(test_logic_flow())
