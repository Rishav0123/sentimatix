import autogen
from crewai.tools import BaseTool
import os

class AutoGenDebateTool(BaseTool):
    name: str = "Debate Financial News"
    description: str = "Runs a simulated debate between a Bullish Analyst and a Bearish Analyst over a piece of financial news. Use this to determine the nuanced impact of the news before writing content."
    
    def _run(self, news_content: str) -> str:
        # Configuration pointing to our local MI300X vLLM instance
        config_list = [{
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "api_key": "EMPTY",
            "base_url": "http://134.199.192.8:8000/v1"
        }]
        
        llm_config = {"config_list": config_list, "temperature": 0.7, "cache_seed": None}

        bull_analyst = autogen.AssistantAgent(
            name="Bull_Analyst",
            system_message="You are a fundamentally optimistic financial analyst. When presented with news, always argue the bullish case. Focus on growth, expansion, and potential revenue. Keep responses under 100 words.",
            llm_config=llm_config,
        )
        
        bear_analyst = autogen.AssistantAgent(
            name="Bear_Analyst",
            system_message="You are a cautious, risk-averse financial analyst. When presented with news, challenge the bull case. Focus on macro headwinds, valuation concerns, and historical risks. Keep responses under 100 words.",
            llm_config=llm_config,
        )
        
        moderator = autogen.UserProxyAgent(
            name="Moderator",
            system_message="You are the moderator. You observe the debate and summarize the consensus.",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2,  # 2 replies each = 4 total turns
            is_termination_msg=lambda x: True if "CONSENSUS REACHED" in x.get("content", "") else False,
            code_execution_config=False,
        )
        
        # Initiate the debate
        try:
            chat_res = moderator.initiate_chat(
                bull_analyst,
                message=f"Here is the latest market news. What is your bullish take?\n\nNEWS:\n{news_content}",
                summary_method="reflection_with_llm",
                max_turns=2
            )
            
            # Extract the summary of the debate
            summary = chat_res.summary if hasattr(chat_res, 'summary') else "Debate completed. Synthesis required."
            
            return f"--- AUTOGEN DEBATE SUMMARY ---\n{summary}\n------------------------------"
            
        except Exception as e:
            return f"AutoGen Debate failed: {str(e)}"
