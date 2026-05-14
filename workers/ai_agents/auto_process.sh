#!/bin/bash

# Sentimatix Auto-Process & Shutdown Script
# Purpose: Maximize AMD Cloud Credits by running only when needed.

echo "🚀 Starting Sentimatix Auto-Process Pipeline..."

# 1. Activate Environment
cd /root/ai_agents
source /root/ai_env/bin/activate

# 2. Pull latest code from GitHub (self-updating!)
echo "📦 Pulling latest code from GitHub..."
git pull origin main 2>/dev/null || echo "⚠️ Git pull failed, using existing code."

# 3. Wait for vLLM to be ready
echo "⏳ Waiting for vLLM (the brain) to wake up..."
MAX_RETRIES=30
COUNT=0
while ! curl -s http://localhost:8000/v1/models > /dev/null; do
    echo "😴 vLLM is still sleeping... (Attempt $COUNT/$MAX_RETRIES)"
    sleep 10
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "❌ vLLM failed to start. Starting it manually..."
        docker start vllm_server
        sleep 30
        if ! curl -s http://localhost:8000/v1/models > /dev/null; then
            echo "❌ vLLM still not responding. Shutting down to save credits."
            sudo shutdown -h now
            exit 1
        fi
    fi
done
echo "🧠 vLLM is AWAKE! Starting analysis..."

# 4. Run Global Sentiment Enrichment
python3 sentiment_engine.py --global

# 5. Run the Orchestrator & post to @sentimatix channel
python3 orchestrator.py

echo "✅ Pipeline Complete!"

# 6. Auto-Shutdown to save credits
echo "💤 Shutting down in 60 seconds to save credits... (Press Ctrl+C to cancel)"
sleep 60
sudo shutdown -h now
