import sys
from crewai import Crew, Process
from agents import FinanceAgents
from tasks import FinanceTasks
from data_fetcher import fetch_stock_brief


async def run_pipeline(stock_symbol: str = "RELIANCE"):
    print(f"\n{'='*60}")
    print(f"  Sentimatix AI Agent Pipeline")
    print(f"  Stock: {stock_symbol}")
    print(f"{'='*60}\n")

    # ── Step 1: Fetch REAL data from Supabase (no LLM involved) ──
    print("📡 Fetching grounded data from Sentimatix database...")
    brief = fetch_stock_brief(stock_symbol)
    print(brief)
    print("\n✅ Data fetched. Starting AI agent pipeline...\n")

    # ── Step 2: Initialise agents ──
    agents = FinanceAgents()
    tasks_obj = FinanceTasks()

    analyst  = agents.analyst_agent()
    writer   = agents.writer_agent()
    compliance = agents.compliance_agent()

    # ── Step 3: Build tasks with data injected into prompts ──
    analyse   = tasks_obj.analyse_task(analyst, stock_symbol, brief)
    snippet   = tasks_obj.social_snippet_task(writer, stock_symbol, brief)
    # reddit    = tasks_obj.reddit_task(writer, stock_symbol, brief)
    # medium    = tasks_obj.medium_task(writer, stock_symbol, brief)
    compliant = tasks_obj.compliance_task(compliance)

    # ── Step 4: Run the crew sequentially ──
    crew = Crew(
        agents=[analyst, writer, compliance],
        tasks=[analyse, snippet, compliant],
        process=Process.sequential,
        verbose=True,
    )

    result = await crew.kickoff_async()

    print("\n" + "="*60)
    print("  FINAL APPROVED CONTENT")
    print("="*60 + "\n")
    print(result)
    
    return {
        "symbol": stock_symbol,
        "content": result,
        "news_count": brief.count("Article: ") if "Article: " in brief else 5,
        "brief": brief
    }


if __name__ == "__main__":
    import asyncio
    symbol = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE"
    asyncio.run(run_pipeline(symbol))
