"""
Selenium-based scrapers for dynamic content e-commerce sites.
Handles JavaScript-heavy sites like Walmart that require browser automation.
"""

import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import re

from .base_scraper import AbstractScraper, ProductData, ScrapingError
from ..cli.utils.config import config_manager


class WalmartSeleniumScraper(AbstractScraper):
    """
    Walmart scraper using Selenium for dynamic content.
    Handles Walmart's JavaScript-heavy product pages.
    """
    
    def __init__(self):
        super().__init__('walmart')
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Initialize Chrome WebDriver with appropriate options."""
        try:
            # Get Selenium configuration
            selenium_config = config_manager.get_setting('selenium', {})
            
            # Configure Chrome options
            chrome_options = Options()
            
            if selenium_config.get('headless', True):
                chrome_options.add_argument('--headless')
            
            # Add window size
            window_size = selenium_config.get('window_size', '1920,1080')
            chrome_options.add_argument(f'--window-size={window_size}')
            
            # Add Chrome options from configuration
            chrome_opts = selenium_config.get('chrome_options', [])
            for opt in chrome_opts:
                chrome_options.add_argument(opt)
            
            # Additional options for better scraping
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Configure timeouts
            page_load_timeout = selenium_config.get('page_load_timeout', 30)
            implicit_wait = selenium_config.get('implicit_wait', 10)
            
            self.driver.set_page_load_timeout(page_load_timeout)
            self.driver.implicitly_wait(implicit_wait)
            
            # Initialize WebDriverWait
            self.wait = WebDriverWait(self.driver, 15)
            
            # Execute script to hide automation flags
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            self.logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise ScrapingError(f"WebDriver initialization failed: {str(e)}", "selenium_setup")
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch page using Selenium WebDriver.
        Overrides base class method to use Selenium instead of requests.
        """
        if not self.driver:
            raise ScrapingError("WebDriver not initialized", "selenium_setup", url)
        
        self._respect_rate_limit()
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Loading page with Selenium: {url} (attempt {attempt + 1})")
                
                # Navigate to page
                self.driver.get(url)
                
                # Wait for key element to ensure page is loaded
                wait_element = self.config.get('selenium_options', {}).get('wait_for_element')
                if wait_element:
                    try:
                        self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, wait_element))
                        )
                    except TimeoutException:
                        self.logger.warning(f"Timeout waiting for element: {wait_element}")
                
                # Optional scroll to load dynamic content
                scroll_pause = self.config.get('selenium_options', {}).get('scroll_pause', 2)
                if scroll_pause:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(scroll_pause)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                
                # Get page source
                page_source = self.driver.page_source
                self.logger.debug(f"Successfully loaded page with Selenium: {url}")
                
                return page_source
                
            except WebDriverException as e:
                self.logger.warning(f"Selenium request failed for {url}: {e}")
                
                if attempt < self.max_retries:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    raise ScrapingError(
                        f"Failed to load page with Selenium after {self.max_retries + 1} attempts",
                        error_type="selenium",
                        url=url
                    )
        
        return None
    
    def parse_page(self, html_content: str, url: str) -> ProductData:
        """Parse Walmart product page using Selenium-loaded content."""
        try:
            # Use Selenium to find elements for more reliable extraction
            product_data = ProductData(url)
            
            # Extract title
            product_data.title = self._extract_walmart_title()
            
            # Extract price
            product_data.price = self._extract_walmart_price()
            
            # Extract availability
            product_data.availability = self._extract_walmart_availability()
            
            # Extract brand
            product_data.brand = self._extract_walmart_brand()
            
            # Extract rating
            product_data.rating = self._extract_walmart_rating()
            
            # Extract reviews count
            product_data.reviews_count = self._extract_walmart_reviews_count()
            
            # Extract image URL
            product_data.image_url = self._extract_walmart_image()
            
            # Add Walmart-specific metadata
            product_data.metadata.update({
                'item_id': self._extract_walmart_item_id(url),
                'department': self._extract_walmart_department(),
                'seller': self._extract_walmart_seller(),
                'shipping_info': self._extract_walmart_shipping()
            })
            
            return product_data
            
        except Exception as e:
            raise ScrapingError(f"Failed to parse Walmart page: {str(e)}", "parsing", url)
    
    def _extract_walmart_title(self) -> Optional[str]:
        """Extract product title using Selenium."""
        title_selectors = [
            '[data-automation-id="product-title"]',
            'h1[data-testid="product-title"]',
            '.prod-ProductTitle',
            'h1'
        ]
        
        for selector in title_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.text.strip():
                    return element.text.strip()
            except:
                continue
        
        return None
    
    def _extract_walmart_price(self) -> Optional[float]:
        """Extract price using Selenium."""
        price_selectors = [
            '[itemprop="price"]',
            '[data-testid="price"]',
            '.price-current',
            '.price .visuallyhidden',
            '[data-automation-id="product-price"]'
        ]
        
        for selector in price_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    price_text = element.text or element.get_attribute('content') or element.get_attribute('value')
                    if price_text:
                        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                        if price_match:
                            return float(price_match.group().replace(',', ''))
            except:
                continue
        
        return None
    
    def _extract_walmart_availability(self) -> Optional[str]:
        """Extract availability status using Selenium."""
        try:
            # Check for add to cart button
            add_to_cart_selectors = [
                '[data-automation-id="fulfillment-add-to-cart"]',
                '[data-testid="add-to-cart"]',
                '.prod-ProductCTA button'
            ]
            
            for selector in add_to_cart_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_enabled():
                        button_text = element.text.lower()
                        if 'add to cart' in button_text:
                            return 'in_stock'
                        elif 'out of stock' in button_text:
                            return 'out_of_stock'
                except:
                    continue
            
            # Check for out of stock indicators
            oos_selectors = [
                '[data-testid="out-of-stock"]',
                '.prod-ProductNotAvailable'
            ]
            
            for selector in oos_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        return 'out_of_stock'
                except:
                    continue
            
        except:
            pass
        
        return 'unknown'
    
    def _extract_walmart_brand(self) -> Optional[str]:
        """Extract brand using Selenium."""
        brand_selectors = [
            '[data-automation-id="product-brand"]',
            '[data-testid="product-brand"]',
            '.prod-ProductBrand'
        ]
        
        for selector in brand_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.text.strip():
                    return element.text.strip()
            except:
                continue
        
        return None
    
    def _extract_walmart_rating(self) -> Optional[float]:
        """Extract product rating using Selenium."""
        rating_selectors = [
            '[data-testid="reviews-section"] .average-rating',
            '.average-rating',
            '[data-testid="rating-number"]'
        ]
        
        for selector in rating_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    rating_text = element.text or element.get_attribute('aria-label')
                    if rating_text:
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            return float(rating_match.group(1))
            except:
                continue
        
        return None
    
    def _extract_walmart_reviews_count(self) -> Optional[int]:
        """Extract reviews count using Selenium."""
        reviews_selectors = [
            '[data-testid="reviews-section"] .review-count',
            '.review-count',
            '[data-testid="total-review-count"]'
        ]
        
        for selector in reviews_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    reviews_text = element.text
                    if reviews_text:
                        reviews_match = re.search(r'(\d+)', reviews_text.replace(',', ''))
                        if reviews_match:
                            return int(reviews_match.group(1))
            except:
                continue
        
        return None
    
    def _extract_walmart_image(self) -> Optional[str]:
        """Extract main product image URL using Selenium."""
        image_selectors = [
            '[data-testid="hero-image-container"] img',
            '.prod-HeroImage img',
            '.prod-ProductMedia img'
        ]
        
        for selector in image_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    src = element.get_attribute('src') or element.get_attribute('data-src')
                    if src and src.startswith('http'):
                        return src
            except:
                continue
        
        return None
    
    def _extract_walmart_item_id(self, url: str) -> Optional[str]:
        """Extract Walmart item ID from URL."""
        item_match = re.search(r'/ip/.*?/(\d+)', url)
        return item_match.group(1) if item_match else None
    
    def _extract_walmart_department(self) -> Optional[str]:
        """Extract department from breadcrumbs using Selenium."""
        try:
            breadcrumb = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="breadcrumb"]')
            if breadcrumb:
                links = breadcrumb.find_elements(By.TAG_NAME, 'a')
                if len(links) > 1:
                    return links[1].text.strip()
        except:
            pass
        
        return None
    
    def _extract_walmart_seller(self) -> Optional[str]:
        """Extract seller information using Selenium."""
        seller_selectors = [
            '[data-testid="seller-name"]',
            '.seller-name',
            '[data-automation-id="seller-info"]'
        ]
        
        for selector in seller_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.text.strip():
                    return element.text.strip()
            except:
                continue
        
        return None
    
    def _extract_walmart_shipping(self) -> Optional[str]:
        """Extract shipping information using Selenium."""
        shipping_selectors = [
            '[data-testid="shipping-info"]',
            '.shipping-info',
            '[data-automation-id="delivery-option"]'
        ]
        
        for selector in shipping_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.text.strip():
                    return element.text.strip()
            except:
                continue
        
        return None
    
    def __del__(self):
        """Cleanup WebDriver when scraper is destroyed."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {e}")