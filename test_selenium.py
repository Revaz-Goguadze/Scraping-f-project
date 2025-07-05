from src.scrapers.selenium_scraper import AmazonSeleniumScraper

def test_amazon():
    scraper = AmazonSeleniumScraper()
    url = "https://www.amazon.com/dp/B0863FR3S9"
    data = scraper.scrape_product(url)
    print("Amazon product data:", data)

if __name__ == "__main__":
    test_amazon()