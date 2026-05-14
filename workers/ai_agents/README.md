# Sentimatix Autonomous AI Pipeline
**Operation & Deployment Guide for AMD MI300X**

This document outlines the workflow, architecture, and operation of the Sentimatix Autonomous Pipeline. The system is designed to provide high-quality stock market sentiment analysis using a local Qwen 2.5 7B model running on an AMD MI300X GPU, while strictly managing cloud costs through automated power cycling.

## 🏗️ Architecture Overview

The pipeline consists of three core components running on the MI300X:

1. **vLLM Inference Server (The Brain):**
   - Runs Qwen 2.5 7B inside a Docker container (`vllm_server`).
   - Handles all LLM requests from the AI Agents.
   - Configured to auto-start on boot (`--restart always`).
2. **Sentiment Engine (`sentiment_engine.py`):**
   - Fetches unanalyzed news from the Sentimatix Supabase database.
   - Uses the local vLLM to assign positive/negative/neutral sentiment.
   - Updates the DB, marking news as `is_ready = 'Y'`.
3. **Orchestrator (`orchestrator.py`):**
   - Identifies the top "trending" stock (most news volume).
   - Coordinates a crew of specialized AI agents (Analyst, Reddit Writer, Medium Writer, Compliance Reviewer) to generate a premium market report.
   - Saves the final report to the DB.
   - **Distributor (`distributor.py`):** Automatically parses the output and posts a formatted alert directly to your Telegram channel (`@sentimatix`).

## 🚀 How to Run the Pipeline (Daily Operations)

The system is designed for a "Set-and-Forget" workflow. You do not need to manually run Python scripts or interact with the terminal once the server is on.

### The 3-Step Process:

1. **Start the Instance:**
   - Log in to your AMD Cloud Dashboard.
   - Start your `MI300X` instance.

2. **Run the Master Script:**
   - SSH into your server:
     ```bash
     ssh root@134.199.192.8
     ```
   - Execute the auto-process script:
     ```bash
     bash /root/ai_agents/auto_process.sh
     ```

3. **Walk Away:**
   - The script will take over completely. It will:
     - 📦 **Pull the latest code** from your GitHub repository automatically.
     - ⏳ **Wait for vLLM** to fully initialize (checking port 8000).
     - 🧠 **Run Sentiment Analysis** on all pending news.
     - 📝 **Generate the Market Report** for the top trending stock.
     - 📲 **Post the Alert** to your Telegram channel.
     - 💤 **Shut Down the Server** automatically 60 seconds after completion.

You are done! The system safely turns itself off, preserving your $100 credit.

## ⚙️ Configuration & Environment

All environment variables required by the pipeline are stored in `/root/ai_agents/.env` on the MI300X instance.

Key variables include:
- `SENTIMATIX_API_URL`: Points to your Railway-hosted API.
- `SENTIMATIX_API_KEY`: Secure bearer token for API communication.
- `TELEGRAM_BOT_TOKEN`: The token for `@Sentimatix_bot`.
- `TELEGRAM_CHAT_ID`: Set to `@sentimatix` (the target channel).

*Note: If you change your Telegram channel or bot, you must manually update the `.env` file on the MI300X.*

## 🛠️ Troubleshooting

If the pipeline fails or behaves unexpectedly:

1. **Script is stuck waiting for vLLM:**
   - The vLLM Docker container might have crashed. The script will automatically try to start it with `docker start vllm_server` after 300 seconds.
   - To inspect manually: `docker logs vllm_server --tail 100`

2. **Telegram Message Not Delivered:**
   - Verify the bot (`@Sentimatix_bot`) is an **Administrator** in the `@sentimatix` channel with "Post Messages" permission.
   - Ensure the report didn't exceed the 4096-character Telegram limit (the `distributor.py` script automatically truncates, but extreme edge cases may fail).

3. **Updating the Code:**
   - You do **not** need to manually `scp` files to the server anymore.
   - Simply push your changes to the `main` branch on GitHub.
   - The `auto_process.sh` script automatically runs `git pull origin main` every time it executes.
