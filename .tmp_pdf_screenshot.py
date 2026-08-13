from pathlib import Path
from playwright.sync_api import sync_playwright
out = Path('d:/ResumeForge/site/software/pdf-render-check.png')
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1200})
    page.goto('http://127.0.0.1:8000/software/Ahmed_Resume.pdf', wait_until='commit')
    page.wait_for_timeout(3000)
    page.screenshot(path=str(out), full_page=True)
    browser.close()
print(out.exists(), out.stat().st_size)
