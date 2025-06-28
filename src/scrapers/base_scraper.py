"""
Abstract base scraper implementing the Strategy pattern.
Provides the template method pattern for common scraping workflow.
"""

import time
import json
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ..cli.utils.config import config_manager
from ..cli.utils.logger import get_logger
from ..data.processors import DataProcessor, DataValidationError


class ProductData:
    """
    Data class representing scraped product information.
    Standardizes product data across different sites.
    """
    
    def __init__(self, url: str):
        self.url = url
        self.title: Optional[str] = None
        self.price: Optional[float] = None
        self.currency: str = "USD"
        self.availability: Optional[str] = None
        self.brand: Optional[str] = None
        self.model: Optional[str] = None
        self.image_url: Optional[str] = None
        self.rating: Optional[float] = None
        self.reviews_count: Optional[int] = None
        self.scraped_at: str = time.strftime('%Y-%m-%d %H:%M:%S')
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product data to dictionary."""
        return {
            'url': self.url,
            'title': self.title,
            'price': self.price,
            'currency': self.currency,
            'availability': self.availability,
            'brand': self.brand,
            'model': self.model,
            'image_url': self.image_url,
            'rating': self.rating,
            'reviews_count': self.reviews_count,
            'scraped_at': self.scraped_at,
            'metadata': self.metadata
        }
    
    def is_valid(self) -> bool:
        """Check if product data meets minimum validation requirements."""
        return bool(self.title and len(self.title.strip()) >= 5)


class ScrapingError(Exception):
    """Custom exception for scraping-related errors."""
    
    def __init__(self, message: str, error_type: str = "general", 
                 url: str = None, response_code: int = None):
        super().__init__(message)
        self.error_type = error_type
        self.url = url
        self.response_code = response_code


class AbstractScraper(ABC):
    """
    Abstract base scraper implementing the Strategy pattern.
    Defines the interface and common functionality for all scrapers.
    """
    
    def __init__(self, site_name: str):
        self.site_name = site_name
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # Load site configuration
        self.config = config_manager.get_scraper_config(site_name)
        self.selectors = self.config.get('selectors', {})
        self.headers = self.config.get('headers', {})
        self.rate_limit = self.config.get('rate_limit', 2.0)
        
        # Initialize session with retry strategy
        self.session = self._create_session()
        
        # Initialize data processor
        self.processor = DataProcessor()
        
        # Rate limiting
        self.last_request_time = 0
        
        # Error handling configuration
        error_config = config_manager.get_error_handling_config()
        self.max_retries = error_config.get('max_retries', 3)
        self.retry_delays = error_config.get('retry_delays', [1, 2, 4])
        self.timeout = error_config.get('network_timeout', 30)
        
        self.logger.info(f"Initialized {site_name} scraper")
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy and headers."""
        session = requests.Session()
        
        # Set default headers
        default_headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        default_headers.update(self.headers)
        session.headers.update(default_headers)
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # Updated from method_whitelist
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from configuration."""
        user_agents = config_manager.get_setting('scraping.user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ])
        return random.choice(user_agents)
    
    def _respect_rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last_request
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch page content with error handling and retries.
        Template method that can be overridden by subclasses.
        """
        self._respect_rate_limit()
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Fetching page: {url} (attempt {attempt + 1})")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                self.logger.debug(f"Successfully fetched page: {url}")
                return response.text
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed for {url}: {e}")
                
                if attempt < self.max_retries:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    raise ScrapingError(
                        f"Failed to fetch page after {self.max_retries + 1} attempts",
                        error_type="network",
                        url=url,
                        response_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                    )
        
        return None
    
    @abstractmethod
    def parse_page(self, html_content: str, url: str) -> ProductData:
        """
        Parse page content and extract product information.
        Must be implemented by concrete scrapers.
        """
        pass
    
    def handle_error(self, error: Exception, url: str) -> None:
        """
        Handle scraping errors with appropriate logging and classification.
        Can be overridden by subclasses for site-specific error handling.
        """
        if isinstance(error, (ScrapingError, DataValidationError)):
            self.logger.error(
                f"Scraping error for {url}: {getattr(error, 'error_type', 'processing')} - {str(error)}"
            )
        else:
            self.logger.error(f"Unexpected error for {url}: {str(error)}")
    
    def scrape_product(self, url: str) -> Optional[ProductData]:
        """
        Main scraping method implementing the template method pattern.
        This is the public interface that orchestrates the scraping process.
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting to scrape product: {url}")
            
            # Step 1: Fetch page content
            html_content = self.fetch_page(url)
            if not html_content:
                raise ScrapingError("Failed to fetch page content", "network", url)
            
            # Step 2: Parse product data
            product_data = self.parse_page(html_content, url)
            if not product_data:
                raise ScrapingError("Failed to parse product data", "parsing", url)
            
            # Step 3: Process (validate and normalize) data
            processed_data = self.processor.process(product_data)
            
            # Step 4: Add metadata
            elapsed_time = time.time() - start_time
            processed_data.metadata.update({
                'scraper_class': self.__class__.__name__,
                'site_name': self.site_name,
                'scraping_time_seconds': elapsed_time,
                'user_agent': self.session.headers.get('User-Agent', '')
            })
            
            self.logger.info(
                f"Successfully scraped product: {processed_data.title[:50]}... "
                f"(Price: {processed_data.price}, Time: {elapsed_time:.2f}s)"
            )
            
            return processed_data
            
        except Exception as e:
            self.handle_error(e, url)
            return None
    
    def scrape_multiple_products(self, urls: List[str]) -> List[ProductData]:
        """
        Scrape multiple products sequentially.
        Can be overridden for batch processing optimizations.
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Scraping product {i}/{len(urls)}: {url}")
            
            try:
                product_data = self.scrape_product(url)
                if product_data:
                    results.append(product_data)
            except Exception as e:
                self.logger.error(f"Failed to scrape product {i}: {e}")
                continue
        
        self.logger.info(f"Completed scraping {len(results)}/{len(urls)} products")
        return results
    
    def get_scraper_stats(self) -> Dict[str, Any]:
        """Get scraper statistics and health information."""
        return {
            'site_name': self.site_name,
            'scraper_class': self.__class__.__name__,
            'rate_limit': self.rate_limit,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'session_headers': dict(self.session.headers)
        }
    
    def __del__(self):
        """Cleanup resources when scraper is destroyed."""
        if hasattr(self, 'session'):
            self.session.close()