#!/bin/bash

# Sentimatix Auto-Process & Shutdown Script
# Purpose: Maximize AMD Cloud Credits by running only when needed.

echo "🚀 Starting Sentimatix Auto-Process Pipeline..."

# 1. Activate Environment
cd /root/ai_agents
source /root/ai_env/bin/activate

# 2. Run Global Sentiment Enrichment
# This will process all 'is_ready = N' news.
echo "🧠 Step 1: Running Global Sentiment Analysis on MI300X..."
python3 sentiment_engine.py --global

# 3. Run the Orchestrator
# This will pick the top trend and post to Telegram.
echo "📡 Step 2: Running Orchestrator & Posting to Telegram..."
python3 orchestrator.py

echo "✅ Pipeline Complete!"

# 4. Final Safety Check
# You can comment out the line below if you want to stay logged in.
echo "💤 Shutting down in 60 seconds to save credits... (Press Ctrl+C to cancel)"
sleep 60
sudo shutdown -h now
