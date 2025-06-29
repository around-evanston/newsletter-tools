from playwright.sync_api import sync_playwright
import time

class DowntownEvanstonCrawler:
    def __init__(self):
        self.url = "https://downtownevanston.org/upcoming-events"

    def fetch_event_links(self):
        events = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=50)
            page = browser.new_page()

            print(f"Navigating to {self.url}...")
            page.goto(self.url, timeout=60000)

            # Wait and scroll down to trigger lazy loading
            time.sleep(1)
            page.mouse.wheel(0, 2000)  # scroll to load all cards
            time.sleep(3)

            # Locate all <a class="sing-card-inner">
            links = page.locator("a.sing-card-inner")
            count = links.count()
            print(f"✅ Found {count} links")

            for i in range(count):
                link = links.nth(i)
                title_el = link.locator("h4.title")
                date_el = link.locator(".sing-card-bottom .category span")

                title = title_el.inner_text().strip() if title_el else "Untitled"
                raw_date = date_el.inner_text().strip() if date_el else None
                external_url = link.get_attribute("href")

                if external_url and external_url.startswith("http"):
                    events.append({
                        "title": title,
                        "raw_date": raw_date,
                        "external_url": external_url
                    })

            browser.close()
        return events


if __name__ == "__main__":
    crawler = DowntownEvanstonCrawler()
    events = crawler.fetch_event_links()

    print("\n--- EVENTS ---\n")
    for e in events:
        print(f"{e['title']}\n{e['raw_date']}\n{e['external_url']}\n---")
