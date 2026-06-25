import os
from dotenv import load_dotenv
from crewai import Agent, LLM

# Load environment variables
load_dotenv()

# Connect CrewAI to our LLM instance (defaults to local Ollama)
LLM_MODEL = os.environ.get("LLM_MODEL", "ollama/qwen2.5:7b")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "ollama")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")

# LiteLLM/CrewAI expects the base_url for native 'ollama/' models to be without '/v1' suffix.
# We strip it dynamically here to prevent routing issues and OpenAI timeout fallbacks.
if LLM_MODEL.startswith("ollama/") and LLM_BASE_URL.endswith("/v1"):
    LLM_BASE_URL = LLM_BASE_URL.replace("/v1", "")

llm = LLM(
    model=LLM_MODEL,
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
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
