from playwright.sync_api import sync_playwright

results = {}
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    console_msgs = []
    page.on('console', lambda msg: console_msgs.append((msg.type, msg.text)))
    page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
    results['download_cv_exists'] = page.query_selector('.download-cv') is not None
    modal = page.query_selector('.download-modal')
    results['modal_exists'] = modal is not None
    results['modal_hidden_before'] = modal.get_attribute('hidden') if modal else None
    # click open
    page.click('.download-cv')
    results['modal_hidden_after_click'] = modal.get_attribute('hidden') if modal else None
    results['button_aria_expanded'] = page.query_selector('.download-cv').get_attribute('aria-expanded')
    results['modal_aria_hidden'] = modal.get_attribute('aria-hidden') if modal else None
    # test links in modal
    links = page.query_selector_all('.download-option')
    link_hrefs = [l.get_attribute('href') for l in links]
    results['link_hrefs'] = link_hrefs
    # verify each PDF URL via HTTP
    pdf_results = {}
    import requests
    base = 'http://127.0.0.1:8000'
    for href in link_hrefs:
        if href.startswith('/'):
            url = base + href
        else:
            url = base + '/' + href
        try:
            r = requests.head(url, timeout=10)
            pdf_results[href] = {'status': r.status_code, 'content-type': r.headers.get('Content-Type'), 'content-length': r.headers.get('Content-Length')}
        except Exception as e:
            pdf_results[href] = {'error': str(e)}
    results['pdf_results'] = pdf_results
    # close via close button
    page.click('.download-modal__close')
    results['modal_hidden_after_close_btn'] = modal.get_attribute('hidden') if modal else None
    # reopen and close with Escape
    page.click('.download-cv')
    page.keyboard.press('Escape')
    results['modal_hidden_after_escape'] = modal.get_attribute('hidden') if modal else None
    results['console'] = console_msgs
    browser.close()

import json
print(json.dumps(results, indent=2))
