"""
Unit tests for the ScraperFactory.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.scrapers.factory import ScraperFactory
from src.scrapers.static_scraper import AmazonScraper, EbayScraper, ShopGeScraper


def test_get_available_scrapers():
    """Test that the factory can list available scrapers."""
    scrapers = ScraperFactory.get_available_scrapers()
    assert isinstance(scrapers, dict)
    assert 'amazon' in scrapers
    assert 'ebay' in scrapers
    assert 'shopge' in scrapers


def test_create_amazon_scraper():
    """Test creating an Amazon scraper."""
    scraper = ScraperFactory.create_scraper('amazon')
    assert isinstance(scraper, AmazonScraper)


def test_create_ebay_scraper():
    """Test creating an eBay scraper."""
    scraper = ScraperFactory.create_scraper('ebay')
    assert isinstance(scraper, EbayScraper)


def test_create_shopge_scraper():
    """Test creating a Shop.ge scraper."""
    scraper = ScraperFactory.create_scraper('shopge')
    assert isinstance(scraper, ShopGeScraper)


def test_create_unknown_scraper_raises_error():
    """Test that creating an unknown scraper raises a ValueError."""
    with pytest.raises(ValueError, match="Unknown site: unknown_site"):
        ScraperFactory.create_scraper('unknown_site') 