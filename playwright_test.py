# playwright_test.py
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
        page.goto("https://example.com")
        print("✅ Page loaded. Playwright is working!")
        page.pause()  # Allows you to inspect the browser manually
        browser.close()

if __name__ == "__main__":
    run()
