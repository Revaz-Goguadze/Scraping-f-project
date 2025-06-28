"""
Static scrapers for e-commerce sites using BeautifulSoup.
Implements concrete scrapers for Amazon, eBay, and Walmart.
"""

import re
from typing import Optional
from bs4 import BeautifulSoup
from .base_scraper import AbstractScraper, ProductData, ScrapingError


class AmazonScraper(AbstractScraper):
    """
    Amazon scraper using BeautifulSoup for static content.
    Handles Amazon's product page structure and data extraction.
    """
    
    def __init__(self):
        super().__init__('amazon')
    
    def parse_page(self, html_content: str, url: str) -> ProductData:
        """Parse Amazon product page and extract product information."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            product_data = ProductData(url)
            
            # Extract title
            title_element = soup.select_one(self.selectors['title'])
            if title_element:
                product_data.title = title_element.get_text().strip()
            
            # Extract price
            product_data.price = self._extract_amazon_price(soup)
            
            # Extract availability
            availability_element = soup.select_one(self.selectors['availability'])
            if availability_element:
                product_data.availability = availability_element.get_text().strip()
            
            # Extract brand
            brand_element = soup.select_one(self.selectors.get('brand', ''))
            if brand_element:
                brand_text = brand_element.get_text().strip()
                # Extract brand from "by Brand Name" format
                brand_match = re.search(r'by\s+(.+)', brand_text)
                if brand_match:
                    product_data.brand = brand_match.group(1).strip()
            
            # Extract image URL
            image_element = soup.select_one(self.selectors.get('image', ''))
            if image_element:
                product_data.image_url = image_element.get('src') or image_element.get('data-src')
            
            # Extract rating
            rating_element = soup.select_one(self.selectors.get('rating', ''))
            if rating_element:
                rating_text = rating_element.get('alt', '')
                rating_match = re.search(r'(\d+\.?\d*)\s*out of', rating_text)
                if rating_match:
                    product_data.rating = float(rating_match.group(1))
            
            # Add Amazon-specific metadata
            product_data.metadata.update({
                'asin': self._extract_asin(url),
                'department': self._extract_department(soup),
                'prime_eligible': self._check_prime_eligibility(soup)
            })
            
            return product_data
            
        except Exception as e:
            raise ScrapingError(f"Failed to parse Amazon page: {str(e)}", "parsing", url)
    
    def _extract_amazon_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from Amazon page with multiple fallback selectors."""
        price_selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '#priceblock_dealprice',
            '#priceblock_ourprice',
            '.a-price-range'
        ]
        
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price_text = price_element.get_text().strip()
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    try:
                        return float(price_match.group().replace(',', ''))
                    except ValueError:
                        continue
        
        return None
    
    def _extract_asin(self, url: str) -> Optional[str]:
        """Extract ASIN from Amazon URL."""
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        return asin_match.group(1) if asin_match else None
    
    def _extract_department(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product department/category."""
        breadcrumb = soup.select_one('#wayfinding-breadcrumbs_feature_div')
        if breadcrumb:
            links = breadcrumb.select('a')
            if len(links) > 1:
                return links[1].get_text().strip()
        return None
    
    def _check_prime_eligibility(self, soup: BeautifulSoup) -> bool:
        """Check if product is Prime eligible."""
        prime_element = soup.select_one('[aria-label*="Prime"]')
        return prime_element is not None


class EbayScraper(AbstractScraper):
    """
    eBay scraper using BeautifulSoup for static content.
    Handles eBay's product page structure and data extraction.
    """
    
    def __init__(self):
        super().__init__('ebay')
    
    def parse_page(self, html_content: str, url: str) -> ProductData:
        """Parse eBay product page and extract product information."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            product_data = ProductData(url)
            
            # Extract title
            title_element = soup.select_one(self.selectors['title'])
            if title_element:
                product_data.title = title_element.get_text().strip()
            
            # Extract price
            product_data.price = self._extract_ebay_price(soup)
            
            # Extract condition
            condition_element = soup.select_one(self.selectors.get('condition', ''))
            if condition_element:
                product_data.availability = condition_element.get_text().strip()
            
            # Extract seller information
            seller_element = soup.select_one(self.selectors.get('seller', ''))
            if seller_element:
                product_data.metadata['seller'] = seller_element.get_text().strip()
            
            # Extract image URL
            image_element = soup.select_one(self.selectors.get('image', ''))
            if image_element:
                product_data.image_url = image_element.get('src') or image_element.get('data-src')
            
            # Extract shipping information
            shipping_element = soup.select_one(self.selectors.get('shipping', ''))
            if shipping_element:
                product_data.metadata['shipping'] = shipping_element.get_text().strip()
            
            # Add eBay-specific metadata
            product_data.metadata.update({
                'item_number': self._extract_item_number(url),
                'listing_type': self._extract_listing_type(soup),
                'time_left': self._extract_time_left(soup)
            })
            
            return product_data
            
        except Exception as e:
            raise ScrapingError(f"Failed to parse eBay page: {str(e)}", "parsing", url)
    
    def _extract_ebay_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from eBay page with multiple fallback selectors."""
        price_selectors = [
            '.x-price-primary',
            '.u-flL.notranslate',
            '.notranslate',
            '#x-price-primary'
        ]
        
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price_text = price_element.get_text().strip()
                # Remove currency symbols and extract numeric value
                price_text = re.sub(r'[^\d.,]', '', price_text)
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    try:
                        return float(price_match.group().replace(',', ''))
                    except ValueError:
                        continue
        
        return None
    
    def _extract_item_number(self, url: str) -> Optional[str]:
        """Extract item number from eBay URL."""
        item_match = re.search(r'/itm/(\d+)', url)
        return item_match.group(1) if item_match else None
    
    def _extract_listing_type(self, soup: BeautifulSoup) -> str:
        """Determine if it's an auction or buy-it-now listing."""
        if soup.select_one('[data-testid="x-btn-primary"]'):
            return "buy_it_now"
        elif soup.select_one('[data-testid="x-btn-secondary"]'):
            return "auction"
        return "unknown"
    
    def _extract_time_left(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract auction time left if applicable."""
        time_element = soup.select_one('.timeMs')
        return time_element.get_text().strip() if time_element else None


class WalmartStaticScraper(AbstractScraper):
    """
    Walmart scraper using BeautifulSoup for static content.
    Note: Walmart heavily uses JavaScript, so this may have limited success.
    The selenium scraper should be preferred for Walmart.
    """
    
    def __init__(self):
        super().__init__('walmart')
    
    def parse_page(self, html_content: str, url: str) -> ProductData:
        """Parse Walmart product page and extract product information."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            product_data = ProductData(url)
            
            # Extract title
            title_selectors = [
                '[data-automation-id="product-title"]',
                'h1[data-testid="product-title"]',
                '.prod-ProductTitle'
            ]
            
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    product_data.title = title_element.get_text().strip()
                    break
            
            # Extract price
            product_data.price = self._extract_walmart_price(soup)
            
            # Extract availability
            availability_selectors = [
                '[data-automation-id="fulfillment-add-to-cart"]',
                '.prod-ProductCTA',
                '[data-testid="add-to-cart"]'
            ]
            
            for selector in availability_selectors:
                availability_element = soup.select_one(selector)
                if availability_element:
                    if 'add to cart' in availability_element.get_text().lower():
                        product_data.availability = 'in_stock'
                    break
            
            # Extract brand
            brand_element = soup.select_one('[data-automation-id="product-brand"]')
            if brand_element:
                product_data.brand = brand_element.get_text().strip()
            
            # Add Walmart-specific metadata
            product_data.metadata.update({
                'item_id': self._extract_item_id(url),
                'department': self._extract_walmart_department(soup)
            })
            
            return product_data
            
        except Exception as e:
            raise ScrapingError(f"Failed to parse Walmart page: {str(e)}", "parsing", url)
    
    def _extract_walmart_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from Walmart page with multiple fallback selectors."""
        price_selectors = [
            '[itemprop="price"]',
            '.price-current',
            '[data-testid="price"]',
            '.price .visuallyhidden'
        ]
        
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price_text = price_element.get_text().strip()
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    try:
                        return float(price_match.group().replace(',', ''))
                    except ValueError:
                        continue
        
        return None
    
    def _extract_item_id(self, url: str) -> Optional[str]:
        """Extract item ID from Walmart URL."""
        item_match = re.search(r'/ip/.*?/(\d+)', url)
        return item_match.group(1) if item_match else None
    
    def _extract_walmart_department(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product department from breadcrumbs."""
        breadcrumb = soup.select_one('[data-testid="breadcrumb"]')
        if breadcrumb:
            links = breadcrumb.select('a')
            if len(links) > 1:
                return links[1].get_text().strip()
        return None