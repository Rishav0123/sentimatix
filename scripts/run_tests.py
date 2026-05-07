import sys
import os
sys.path.insert(0, os.path.abspath(r"d:\sentimatix\workers/nlp\stock-news\nlp"))
import asyncio
import analyze_sentiment_production as asp

async def run_tests():
    print("Running tests...")
    await asp.test_production_analyzer()
    await asp.test_with_sample_database_records()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(run_tests())
