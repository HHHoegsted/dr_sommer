from playwright.sync_api import sync_playwright

OUTPUT_PATH = "article.pdf"
SEARCH_URL = "https://dr.dk/soeg"
TIME_OUT = 1500

class BrowserManager:
    def __init__(self, headless=True):
        self.browser = None
        self.headless = headless

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()
        self.playwright.stop()

    def new_context(self):
        return self.browser.new_context()

def handle_cookies(page):
    page.wait_for_timeout(TIME_OUT)
    button = page.locator("button.submitChosen")
    if button.is_visible():
        button.click()


def save_article_as_pdf(browser, url, path=OUTPUT_PATH):
    context = browser.new_context()
    page = context.new_page()
    page.goto(url)
    page.pdf(path=path)
    context.close()


def search_and_find_article(page, keyword, headline_text):
    page.goto(SEARCH_URL)

    # Wait for search input field
    search_input = page.locator("input[type='search']")
    search_input.wait_for()

    # Fill keyword and search
    search_input.fill(keyword)
    page.press("input[type='search']", "Enter")

    # Wait for the results area to appear
    page.locator(".dre-teaser-list").wait_for()

    # Sort by publish time
    sort_button = page.locator("input[id='hydra-search-page-form__sort-input__publishtime']")
    if sort_button.is_visible():
        sort_button.click()
        # Wait for teasers to re-render
        page.locator(".dre-teaser-list li").first.wait_for(timeout=TIME_OUT)

    seen_teasers = set()

    # Loops until the article is found or until it runs out of search result pages
    while True:
        teaser_items = page.locator(".dre-teaser-list li")
        count = teaser_items.count()

        for i in range(count):
            teaser = teaser_items.nth(i)
            teaser_text = teaser.inner_text()

            if teaser_text not in seen_teasers:
                seen_teasers.add(teaser_text)

                if headline_text in teaser_text:
                    link = teaser.locator("a").get_attribute("href")
                    return link

        # Load more button
        more_button = page.locator("button.dre-button")
        if more_button.is_visible() and not more_button.is_disabled():
            more_button.click()
            # Wait for new teasers to load by watching for new items
            page.wait_for_timeout(TIME_OUT)
        else:
            break

    return None  # Not found


if __name__ == '__main__':
    with BrowserManager(headless=False) as manager:
        context = manager.new_context()
        page = context.new_page()
        
        try:
            page.goto("http://dr.dk")
            handle_cookies(page)
        except Exception as e:
            print(f"Der var en fejl på DR's server: {e}")
        
        article_path = search_and_find_article(
            page,
            keyword="sommer",
            headline_text="Over 25 graders varme: Vi har årets første sommerdag"
        )

        if article_path:
            article_url = f"https://dr.dk{article_path}"
            save_article_as_pdf(manager.browser, article_url)
            print("Artikel fundet og gemt som PDF")
        else:
            print("Artikel ikke fundet")