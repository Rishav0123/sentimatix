import markdown
import os
import base64
import re

with open(r'd:\sentimatix\docs\medium_article_draft.md.resolved', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace local image paths with base64-encoded data URIs
def embed_image(match):
    alt = match.group(1)
    path = match.group(2)
    # Normalize path
    path = path.replace('/', '\\')
    if not os.path.isabs(path):
        path = os.path.join(r'd:\sentimatix\docs', path)
    if os.path.exists(path):
        with open(path, 'rb') as img_file:
            ext = os.path.splitext(path)[1].lower().replace('.', '')
            if ext == 'jpg': ext = 'jpeg'
            b64 = base64.b64encode(img_file.read()).decode('utf-8')
            return f'![{alt}](data:image/{ext};base64,{b64})'
    return match.group(0)

text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', embed_image, text)

html = markdown.markdown(text, extensions=['fenced_code'])

html_template = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 2em; }}
    pre {{ background: #f4f4f4; padding: 1em; border-radius: 5px; overflow-x: auto; }}
    code {{ font-family: monospace; }}
    img {{ max-width: 100%; height: auto; display: block; margin: 1em auto; border-radius: 8px; }}
    h1 {{ font-size: 2em; }}
    h2 {{ font-size: 1.4em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }}
</style>
</head>
<body>
{html}
</body>
</html>
"""

html_path = r'd:\sentimatix\docs\temp.html'
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_template)

from playwright.sync_api import sync_playwright

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('file:///' + os.path.abspath(html_path).replace('\\', '/'))
        page.wait_for_timeout(2000)
        page.pdf(path=r'd:\sentimatix\docs\sentimatix_article.pdf', format='A4', margin={'top':'1in', 'right':'1in', 'bottom':'1in', 'left':'1in'})
        browser.close()
    print("PDF successfully generated with images.")
except Exception as e:
    print(f"Playwright error: {e}")
