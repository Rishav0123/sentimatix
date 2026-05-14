import time
from openai import OpenAI
import os

# Point the OpenAI client to the MI300X vLLM instance
vllm_client = OpenAI(
    api_key="EMPTY",  # vLLM doesn't require an API key by default
    base_url="http://134.199.192.8:8000/v1",
)

def test_financial_reasoning():
    print("Testing MI300X Qwen 2.5 7B reasoning capabilities...")
    start_time = time.time()
    
    completion = vllm_client.chat.completions.create(
        model="Qwen/Qwen2.5-7B-Instruct",
        messages=[
            {"role": "system", "content": "You are a sharp, analytical AI financial analyst focusing on Indian markets."},
            {"role": "user", "content": "Reliance Industries just announced a massive new $5B investment into their renewable energy arm. How might this impact their stock price in the short term vs the long term? Be concise."}
        ],
        max_tokens=200,
        temperature=0.7
    )
    
    elapsed = time.time() - start_time
    response = completion.choices[0].message.content
    
    print("\n" + "="*50)
    print(f"Response (generated in {elapsed:.2f} seconds):\n")
    print(response)
    print("="*50)

if __name__ == "__main__":
    test_financial_reasoning()
