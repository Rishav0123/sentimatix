from crewai import Agent, LLM

# Connect CrewAI to our local MI300X vLLM instance
llm = LLM(
    model="openai/Qwen/Qwen2.5-7B-Instruct",
    api_key="EMPTY",
    base_url="http://134.199.192.8:8000/v1"
)


class FinanceAgents:
    def analyst_agent(self):
        return Agent(
            role="Senior Financial Analyst",
            goal=(
                "Analyse the provided news brief and produce a structured bull/bear "
                "debate and consensus for the given Indian stock."
            ),
            backstory=(
                "You are a seasoned equity analyst covering Indian markets (NSE/BSE). "
                "You are rigorous, data-driven, and always cite exact source links "
                "provided to you. You NEVER invent data or URLs."
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )

    def writer_agent(self):
        return Agent(
            role="Viral Finance Content Creator",
            goal=(
                "Transform analyst research into compelling long-form content for "
                "Reddit (r/IndiaInvestments) and Medium, using only the data and "
                "links provided. Include every source link."
            ),
            backstory=(
                "You are a financial storyteller who writes deeply analytical, "
                "data-backed content that retail Indian investors love. "
                "You always hyperlink your sources in markdown format."
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )

    def compliance_agent(self):
        return Agent(
            role="Financial Compliance Officer",
            goal=(
                "Review all generated content, remove absolute profit guarantees, "
                "and append SEBI-compliant educational disclaimers."
            ),
            backstory=(
                "You are a strict regulatory compliance officer ensuring the platform "
                "cannot be held liable for investment losses."
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )
