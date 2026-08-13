from pathlib import Path
from playwright.sync_api import sync_playwright
html_path = Path('d:/ResumeForge/site/software/index.html').resolve()
out = Path('d:/ResumeForge/site/software/test-render.pdf')
with sync_playwright() as browser_manager:
    browser = browser_manager.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(html_path.as_uri(), wait_until='networkidle')
    page.pdf(path=str(out), format='A4', print_background=True, prefer_css_page_size=True, display_header_footer=False, outline=False, tagged=False)
    browser.close()
print(out.exists(), out.stat().st_size)
