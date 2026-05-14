import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def send_telegram_message(message: str):
    """Send a message to a Telegram channel/chat via the Bot API."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ Telegram credentials missing. Skipping distribution.")
        return
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = httpx.post(url, json=payload)
        response.raise_for_status()
        print("✅ Telegram message sent successfully.")
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")

import re

def distribute_content(result: dict):
    """Parse the agent result and push to various channels with premium formatting."""
    content = str(result.get("content", ""))
    brief = str(result.get("brief", ""))
    
    # 1. Extract the Social Snippet using the explicit markers
    if "[[SOCIAL_SNIPPET]]" in content:
        try:
            snippet = content.split("[[SOCIAL_SNIPPET]]")[1]
            if "[[" in snippet:
                snippet = snippet.split("[[")[0]
            snippet = snippet.strip()
        except Exception:
            snippet = content[:4000] 
    else:
        snippet = content[:4000]

    # 2. AUTOMATED LINK INJECTION (The "Premium" part)
    # Extract all Markdown links from the original brief to ensure accuracy
    links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', brief)
    
    link_section = "\n\n**🔗 Top Data Sources:**\n"
    if links:
        # Take the top 2-3 unique links
        seen_urls = set()
        count = 0
        for title, url in links:
            if url not in seen_urls and count < 3:
                link_section += f"• [{title}]({url})\n"
                seen_urls.add(url)
                count += 1
    else:
        link_section = ""

    # 3. Add the Branding Footer
    footer = (
        "\n\n---\n"
        "🌐 [Sentimatix Portal](https://sentimatix-production.up.railway.app/portal/)\n"
        "🔌 [Sentimatix API](https://rapidapi.com/rishavduttakgp/api/sentimatix-indian-stock-market-sentiment)\n"
        "⚠️ *Disclaimer: Educational purposes only. Not financial advice.*"
    )
    
    final_message = snippet + link_section + footer
    send_telegram_message(final_message)
    
    # Add WhatsApp / others here...
