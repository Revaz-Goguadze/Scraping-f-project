"""
This package contains the scrapers for the E-Commerce Price Monitoring System.
"""

from .base_scraper import AbstractScraper
from .static_scraper import AmazonScraper, EbayScraper, ShopGeScraper
from .factory import (
    ScraperFactory,
    create_amazon_scraper,
    create_ebay_scraper,
    create_all_scrapers,
    create_shopge_scraper
)

# Export main classes and functions
__all__ = [
    'ScraperFactory',
    'AbstractScraper',
    'AmazonScraper',
    'EbayScraper',
    'ShopGeScraper',
    'create_amazon_scraper',
    'create_ebay_scraper',
    'create_all_scrapers',
    'create_shopge_scraper'
]