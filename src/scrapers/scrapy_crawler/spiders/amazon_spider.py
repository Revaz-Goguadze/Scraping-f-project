"""
Scrapy spider for Amazon product scraping.
Implements the required Scrapy framework for at least one major crawler (Project.md line 106).
"""

import scrapy
from scrapy import Request
from itemloaders import ItemLoader
from datetime import datetime
import re
from urllib.parse import urljoin

from ..items import ProductItem


class AmazonSpider(scrapy.Spider):
    """
    Amazon spider for scraping product information using Scrapy framework.
    Implements concurrent scraping with built-in Scrapy features.
    """
    
    name = 'amazon'
    allowed_domains = ['amazon.com']
    
    # Custom settings for this spider
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    def __init__(self, urls=None, *args, **kwargs):
        """
        Initialize spider with URLs to scrape.
        
        Args:
            urls: List of Amazon product URLs to scrape
        """
        super(AmazonSpider, self).__init__(*args, **kwargs)
        self.start_urls = []
        
        if urls:
            if isinstance(urls, str):
                # Single URL or comma-separated URLs
                self.start_urls = [url.strip() for url in urls.split(',')]
            elif isinstance(urls, list):
                self.start_urls = urls
        
        # Default URLs for testing if none provided
        if not self.start_urls:
            self.start_urls = [
                'https://www.amazon.com/dp/B0863FR3S9',  # Sony headphones
                'https://www.amazon.com/dp/B08N5WRWNW',  # MacBook
            ]
        
        self.logger.info(f'Amazon spider initialized with {len(self.start_urls)} URLs')
    
    def start_requests(self):
        """Generate initial requests for all start URLs."""
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
                meta={'dont_cache': True}
            )
    
    def parse(self, response):
        """
        Parse Amazon product page and extract product information.
        
        Args:
            response: Scrapy response object
            
        Yields:
            ProductItem: Extracted product data
        """
        self.logger.info(f'Parsing Amazon product: {response.url}')
        
        # Create item loader for structured data extraction
        loader = ItemLoader(item=ProductItem(), response=response)
        
        # Basic information
        loader.add_value('url', response.url)
        loader.add_value('site_name', 'amazon')
        loader.add_value('scraper_name', self.name)
        loader.add_value('scraped_at', datetime.utcnow().isoformat())
        loader.add_value('currency', 'USD')
        
        # Extract title
        title_selectors = [
            '#productTitle::text',
            '.product-title::text',
            'h1 span::text'
        ]
        for selector in title_selectors:
            title = response.css(selector).getall()
            if title:
                loader.add_value('title', title)
                break
        
        # Extract price with multiple fallback selectors
        price_selectors = [
            '.a-price-whole::text',
            '.a-price .a-offscreen::text',
            '#priceblock_dealprice::text',
            '#priceblock_ourprice::text',
            '.a-price-range .a-offscreen::text'
        ]
        for selector in price_selectors:
            price = response.css(selector).getall()
            if price:
                loader.add_value('price', price)
                break
        
        # Extract availability
        availability_selectors = [
            '#availability span::text',
            '.a-size-medium.a-color-success::text',
            '.a-size-medium.a-color-price::text'
        ]
        for selector in availability_selectors:
            availability = response.css(selector).getall()
            if availability:
                loader.add_value('availability', availability)
                break
        
        # Extract brand
        brand_selectors = [
            '#bylineInfo::text',
            '.a-row .a-text-bold::text',
            '[data-feature-name="bylineInfo"] a::text'
        ]
        for selector in brand_selectors:
            brand = response.css(selector).getall()
            if brand:
                # Clean brand text (remove "by" prefix)
                brand_text = ' '.join(brand)
                brand_match = re.search(r'by\s+(.+)', brand_text)
                if brand_match:
                    loader.add_value('brand', brand_match.group(1))
                else:
                    loader.add_value('brand', brand)
                break
        
        # Extract image URL
        image_selectors = [
            '#landingImage::attr(src)',
            '#landingImage::attr(data-src)',
            '.a-dynamic-image::attr(src)'
        ]
        for selector in image_selectors:
            image = response.css(selector).get()
            if image:
                loader.add_value('image_url', image)
                break
        
        # Extract rating
        rating_selectors = [
            '.a-icon-alt::text',
            '[data-hook="rating-out-of-text"]::text'
        ]
        for selector in rating_selectors:
            rating = response.css(selector).getall()
            if rating:
                rating_text = ' '.join(rating)
                rating_match = re.search(r'(\d+\.?\d*)\s*out of', rating_text)
                if rating_match:
                    loader.add_value('rating', float(rating_match.group(1)))
                break
        
        # Extract reviews count
        reviews_selectors = [
            '#acrCustomerReviewText::text',
            '[data-hook="total-review-count"]::text'
        ]
        for selector in reviews_selectors:
            reviews = response.css(selector).getall()
            if reviews:
                reviews_text = ' '.join(reviews)
                reviews_match = re.search(r'(\d+)', reviews_text.replace(',', ''))
                if reviews_match:
                    loader.add_value('reviews_count', int(reviews_match.group(1)))
                break
        
        # Extract category from breadcrumbs
        breadcrumb_selectors = [
            '#wayfinding-breadcrumbs_feature_div a::text',
            '.a-breadcrumb a::text'
        ]
        for selector in breadcrumb_selectors:
            breadcrumbs = response.css(selector).getall()
            if breadcrumbs and len(breadcrumbs) > 1:
                # Take the second breadcrumb as main category
                loader.add_value('category', breadcrumbs[1])
                break
        
        # Extract description
        description_selectors = [
            '#feature-bullets ul li span::text',
            '.a-size-base-plus::text'
        ]
        for selector in description_selectors:
            description = response.css(selector).getall()
            if description:
                loader.add_value('description', description)
                break
        
        # Extract seller information
        seller_selectors = [
            '#merchant-info::text',
            '.a-size-small .a-link-normal::text'
        ]
        for selector in selector_selectors:
            seller = response.css(selector).getall()
            if seller:
                loader.add_value('seller_info', seller)
                break
        
        # Load and yield the item
        item = loader.load_item()
        
        # Log successful extraction
        title = item.get('title', 'Unknown')
        price = item.get('price', 'N/A')
        self.logger.info(f'Extracted: {title[:50]}... - ${price}')
        
        yield item
    
    def parse_search_results(self, response):
        """
        Parse Amazon search results page and extract product URLs.
        Can be used for bulk scraping of product categories.
        
        Args:
            response: Scrapy response object
            
        Yields:
            Request: Requests for individual product pages
        """
        # Extract product URLs from search results
        product_selectors = [
            '[data-component-type="s-search-result"] h2 a::attr(href)',
            '.s-result-item h2 a::attr(href)'
        ]
        
        for selector in product_selectors:
            product_urls = response.css(selector).getall()
            for url in product_urls:
                full_url = urljoin(response.url, url)
                yield Request(
                    url=full_url,
                    callback=self.parse,
                    headers=self.custom_settings.get('DEFAULT_REQUEST_HEADERS', {}),
                    meta={'dont_cache': True}
                )
            
            if product_urls:  # If we found products with first selector, no need to try others
                break
        
        # Follow pagination if available
        next_page = response.css('.a-pagination .a-next::attr(href)').get()
        if next_page:
            yield Request(
                url=urljoin(response.url, next_page),
                callback=self.parse_search_results
            )


class AmazonSearchSpider(AmazonSpider):
    """
    Amazon search spider for scraping products by search terms.
    Extends AmazonSpider to support search-based scraping.
    """
    
    name = 'amazon_search'
    
    def __init__(self, query=None, max_pages=3, *args, **kwargs):
        """
        Initialize search spider with search query.
        
        Args:
            query: Search term for Amazon products
            max_pages: Maximum number of search result pages to scrape
        """
        super(AmazonSearchSpider, self).__init__(*args, **kwargs)
        
        self.query = query or 'electronics'
        self.max_pages = int(max_pages)
        self.pages_scraped = 0
        
        # Generate search URL
        search_url = f"https://www.amazon.com/s?k={self.query.replace(' ', '+')}"
        self.start_urls = [search_url]
        
        self.logger.info(f'Amazon search spider initialized for query: "{self.query}"')
    
    def parse(self, response):
        """Parse search results and extract product URLs."""
        return self.parse_search_results(response)
    
    def parse_search_results(self, response):
        """Override to limit pagination."""
        self.pages_scraped += 1
        
        # Extract products from current page
        for request in super().parse_search_results(response):
            if request.callback == self.parse:  # Product page request
                yield request
            elif request.callback == self.parse_search_results and self.pages_scraped < self.max_pages:
                # Pagination request within limit
                yield request