from crewai import Task


class FinanceTasks:
    def analyse_task(self, agent, stock_symbol: str, grounded_brief: str):
        return Task(
            description=f"""
You are given a VERIFIED data brief pulled from the Sentimatix database.
Do NOT invent any data. Do NOT add URLs that are not in the brief below.

--- BEGIN GROUNDED BRIEF ---
{grounded_brief}
--- END GROUNDED BRIEF ---

Your job:
1. Identify the top 5 most market-relevant articles from the brief above.
2. Write a structured Bull Case (3 points) using only facts from the brief.
3. Write a structured Bear Case (3 points) using only facts from the brief.
4. Write a 2-sentence consensus that weighs both sides.
5. Copy the exact markdown links from the brief into your output for each article you reference.
""",
            expected_output=(
                f"A structured analysis for {stock_symbol} with: "
                "Bull Case (3 points with source links), Bear Case (3 points with source links), "
                "and a 2-sentence consensus. All links must be exact copies from the brief."
            ),
            agent=agent,
        )

    def reddit_task(self, agent, stock_symbol: str, grounded_brief: str):
        return Task(
            description=f"""
Write a detailed Reddit post for r/IndiaInvestments about {stock_symbol}.

You will be provided with the analyst's output (Bull/Bear/Consensus) which was derived from this brief:
--- BEGIN GROUNDED BRIEF ---
{grounded_brief}
--- END GROUNDED BRIEF ---

Required Reddit post format (strict):
# {stock_symbol} Deep Dive — [Write a catchy, data-backed title here]

## 📰 The Catalyst
- Bullet points of the key news events. Each bullet MUST include the markdown hyperlink from the brief above.

## 🐂 Bull Case
- (Use the analyst's bull points, keep source links)

## 🐻 Bear Case  
- (Use the analyst's bear points, keep source links)

## 📊 Sentiment Data
- Summary of the Sentimatix sentiment breakdown (% bullish, % bearish, article count)

## 🎯 TL;DR
One sharp sentence summarising the opportunity/risk for a retail investor.

---
*Data sourced from Sentimatix. All source links are clickable above.*
""",
            expected_output=(
                "A fully formatted Reddit Markdown post following the exact structure above, "
                "with every source link embedded as a clickable markdown hyperlink."
            ),
            agent=agent,
        )

    def medium_task(self, agent, stock_symbol: str, grounded_brief: str):
        return Task(
            description=f"""
Write a professional, SEO-optimized Medium article about {stock_symbol} for Indian retail investors.

Use the data brief and analyst output already generated. Do NOT invent data.

Brief for reference:
--- BEGIN GROUNDED BRIEF ---
{grounded_brief}
--- END GROUNDED BRIEF ---

Required Medium article format:
# [SEO-Optimized H1 Title about {stock_symbol}]

## Executive Summary
2-3 sentences covering the most important market development.

## The News Driving the Story
Long-form paragraph analysis of the top 3-5 news events. MUST include markdown links [Source Name](URL) for every article cited.

## Bull Case: Why {stock_symbol} Could Rally
Detailed paragraph expanding the bull argument with data points and linked sources.

## Bear Case: Risks Investors Must Consider  
Detailed paragraph expanding the bear argument with data points and linked sources.

## Our Verdict
2-3 sentences of balanced, nuanced conclusion.
""",
            expected_output=(
                "A professional, long-form Medium article in Markdown format with "
                "H2/H3 headers, every source cited as a clickable markdown hyperlink, "
                "minimum 400 words."
            ),
            agent=agent,
        )

    def compliance_task(self, agent):
        return Task(
            description="""
Review the Reddit post, Medium article, and Social Snippet produced by the previous agents.
1. Ensure no sentence makes absolute guarantees of profit or loss.
2. Soften any language like 'will rise', 'guaranteed', 'certain to'.
3. Append the SEBI disclaimer verbatim to the bottom of the Reddit and Medium content.
4. CRITICAL: Do NOT remove or modify any source URLs or Markdown links found in the content. Every link from the previous agents MUST be preserved in the final output.

Return the FINAL approved versions using these exact markers:
[[SOCIAL_SNIPPET]]
(Short snippet here)

[[REDDIT]]
(Reddit post here)

[[MEDIUM]]
(Medium article here)
""",
            expected_output=(
                "The final, compliance-approved Reddit Post, Medium Article, and Social Snippet, separated by [[REDDIT]], [[MEDIUM]], and [[SOCIAL_SNIPPET]] markers."
            ),
            agent=agent,
        )

    def social_snippet_task(self, agent, stock_symbol: str, grounded_brief: str):
        return Task(
            description=f"""
Write a professional, high-impact social media alert for Telegram/WhatsApp about {stock_symbol}.
Use a structured, emoji-rich template.

Required Template:
📊 **{stock_symbol} | AI Market Alert**
---
**🔍 Quick Summary:**
[Write 2 sentences about the most critical news catalyst]

**📈 Key Bullish Signals:**
🔹 [Fact 1]
🔹 [Fact 2]

**📉 Key Bearish Risks:**
🔹 [Fact 1]
🔹 [Fact 2]

**🎯 Market Verdict:**
[One punchy sentence for a retail investor]

#Investing #StockMarket #Nifty50 #{stock_symbol}
""",
            expected_output=(
                "A perfectly formatted market alert following the exact template above."
            ),
            agent=agent,
        )
