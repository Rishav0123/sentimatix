#!/bin/bash

# Sentimatix Auto-Process & Shutdown Script
# Purpose: Maximize AMD Cloud Credits by running only when needed.

echo "🚀 Starting Sentimatix Auto-Process Pipeline..."

# 1. Activate Environment
cd /root/ai_agents
source /root/ai_env/bin/activate

# 2. Wait for vLLM to be ready
echo "⏳ Waiting for vLLM (the brain) to wake up..."
MAX_RETRIES=30
COUNT=0
while ! curl -s http://localhost:8000/v1/models > /dev/null; do
    echo "😴 vLLM is still sleeping... (Attempt $COUNT/$MAX_RETRIES)"
    sleep 10
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "❌ vLLM failed to start in time. Shutting down to save credits."
        sudo shutdown -h now
        exit 1
    fi
done
echo "🧠 vLLM is AWAKE! Starting analysis..."

# 3. Run Global Sentiment Enrichment
python3 sentiment_engine.py --global

# 4. Run the Orchestrator
python3 orchestrator.py

echo "✅ Pipeline Complete!"

# 5. Final Safety Check
echo "💤 Shutting down in 60 seconds to save credits... (Press Ctrl+C to cancel)"
sleep 60
sudo shutdown -h now
