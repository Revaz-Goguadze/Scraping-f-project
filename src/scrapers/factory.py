"""
Scraper factory for creating scraper instances.
"""

from typing import Dict, Type
from .base_scraper import AbstractScraper
from .static_scraper import AmazonScraper, EbayScraper, ShopGeScraper
from ..cli.utils.config import config_manager
from ..cli.utils.logger import get_logger

logger = get_logger(__name__)


class ScraperFactory:
    """
    Factory class for creating scraper instances.
    Implements the Factory pattern to dynamically create scrapers based on site configuration.
    """
    
    _scrapers: Dict[str, Type[AbstractScraper]] = {}
    _initialized = False
    
    @classmethod
    def _initialize(cls):
        """Initialize the factory with available scrapers."""
        if cls._initialized:
            return
        
        # Register static scrapers
        cls._scrapers['amazon'] = AmazonScraper
        cls._scrapers['ebay'] = EbayScraper
        cls._scrapers['shopge'] = ShopGeScraper
        cls._scrapers['shop.ge'] = ShopGeScraper  # Allow both shopge and shop.ge
        
        cls._initialized = True
        logger.info(f"ScraperFactory initialized with {len(cls._scrapers)} scrapers")
    
    @classmethod
    def register_scraper(cls, name: str, scraper_class: Type[AbstractScraper]):
        """
        Register a new scraper class.
        
        Args:
            name: Scraper name/identifier
            scraper_class: Scraper class that inherits from AbstractScraper
        """
        cls._initialize()
        
        if not issubclass(scraper_class, AbstractScraper):
            raise ValueError(f"Scraper class must inherit from AbstractScraper")
        
        cls._scrapers[name] = scraper_class
        logger.info(f"Registered scraper: {name} -> {scraper_class.__name__}")
    
    @classmethod
    def create_scraper(cls, site_name: str) -> AbstractScraper:
        """
        Create a scraper instance for the specified site.
        
        Args:
            site_name: Name of the site (amazon, ebay)
            
        Returns:
            Scraper instance
            
        Raises:
            ValueError: If site is not supported
        """
        cls._initialize()
        
        # Get site configuration to determine scraper type
        try:
            site_config = config_manager.get_scraper_config(site_name)
            scraper_type = site_config.get('scraper_type', 'static')
            requires_selenium = site_config.get('requires_selenium', False)
        except ValueError:
            raise ValueError(f"Unknown site: {site_name}")
        
        # Determine scraper key
        scraper_key = site_name
        if requires_selenium or scraper_type == 'selenium':
            scraper_key = f"{site_name}_selenium"
        elif scraper_type == 'static':
            # For static scrapers, use the site name directly
            pass
        
        # Fallback to site name if specific key not found
        if scraper_key not in cls._scrapers and site_name in cls._scrapers:
            scraper_key = site_name
        
        if scraper_key not in cls._scrapers:
            available_scrapers = list(cls._scrapers.keys())
            raise ValueError(
                f"No scraper available for '{scraper_key}'. "
                f"Available scrapers: {available_scrapers}"
            )
        
        scraper_class = cls._scrapers[scraper_key]
        logger.info(f"Creating scraper: {scraper_key} -> {scraper_class.__name__}")
        
        try:
            return scraper_class()
        except Exception as e:
            logger.error(f"Failed to create scraper {scraper_key}: {e}")
            raise
    
    @classmethod
    def get_available_scrapers(cls) -> Dict[str, str]:
        """
        Get list of available scrapers.
        
        Returns:
            Dictionary mapping scraper names to class names
        """
        cls._initialize()
        return {name: scraper_class.__name__ for name, scraper_class in cls._scrapers.items()}
    
    @classmethod
    def get_scrapers_for_sites(cls, site_names: list) -> Dict[str, AbstractScraper]:
        """
        Create scrapers for multiple sites.
        
        Args:
            site_names: List of site names
            
        Returns:
            Dictionary mapping site names to scraper instances
        """
        scrapers = {}
        
        for site_name in site_names:
            try:
                scraper = cls.create_scraper(site_name)
                scrapers[site_name] = scraper
                logger.info(f"Created scraper for {site_name}")
            except Exception as e:
                logger.error(f"Failed to create scraper for {site_name}: {e}")
                continue
        
        return scrapers
    
    @classmethod
    def get_supported_sites(cls) -> list:
        """Get list of supported site names."""
        # Extract unique site names from scraper keys
        sites = set()
        for scraper_key in cls.get_available_scrapers().keys():
            # Remove suffixes like '_selenium' or '_static'
            site_name = scraper_key.replace('_selenium', '').replace('_static', '')
            sites.add(site_name)
        
        return sorted(list(sites))


# Convenience functions for direct scraper creation
def create_amazon_scraper() -> AmazonScraper:
    """Create Amazon scraper instance."""
    return ScraperFactory.create_scraper('amazon')


def create_ebay_scraper() -> EbayScraper:
    """Create eBay scraper instance."""
    return ScraperFactory.create_scraper('ebay')


def create_shopge_scraper() -> ShopGeScraper:
    """Create ShopGe scraper instance."""
    return ScraperFactory.create_scraper('shopge')


def create_all_scrapers() -> Dict[str, AbstractScraper]:
    """Create scrapers for all supported sites."""
    sites = ['amazon', 'ebay', 'shopge']
    return ScraperFactory.get_scrapers_for_sites(sites) 