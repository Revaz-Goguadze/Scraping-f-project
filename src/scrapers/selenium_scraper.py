"""
Dynamic scrapers using Selenium for JS-rendered pages.
"""
import time
from typing import Optional
from .base_scraper import AbstractScraper, ScrapingError
from .static_scraper import AmazonScraper, EbayScraper, ShopGeScraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from ..cli.utils.config import config_manager
from ..cli.utils.logger import get_logger

class BaseSeleniumScraper(AbstractScraper):
    def __init__(self, site_name: str):
        super().__init__(site_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=options)

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch page using Selenium and return rendered HTML."""
        self._respect_rate_limit()
        try:
            self.logger.debug(f"Selenium fetching page: {url}")
            self.driver.get(url)
            delay = config_manager.get_setting('scraping.selenium_delay', 2)
            time.sleep(delay)
            return self.driver.page_source
        except WebDriverException as e:
            raise ScrapingError(f"Selenium failed to fetch {url}: {e}", "selenium", url)

    def __del__(self):
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except Exception:
                pass

class AmazonSeleniumScraper(AmazonScraper, BaseSeleniumScraper):
    def __init__(self):
        AmazonScraper.__init__(self)
        BaseSeleniumScraper.__init__(self, 'amazon')

class EbaySeleniumScraper(EbayScraper, BaseSeleniumScraper):
    def __init__(self):
        EbayScraper.__init__(self)
        BaseSeleniumScraper.__init__(self, 'ebay')

class ShopGeSeleniumScraper(ShopGeScraper, BaseSeleniumScraper):
    def __init__(self):
        ShopGeScraper.__init__(self)
        BaseSeleniumScraper.__init__(self, 'shopge')