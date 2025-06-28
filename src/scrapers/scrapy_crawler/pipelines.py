"""
Scrapy pipelines for the E-Commerce Price Monitoring System.
Handles data validation, database storage, and statistics collection.
"""

import sys
import logging
from datetime import datetime
from typing import Dict, Any
from itemadapter import ItemAdapter

# Add src to path for imports
sys.path.insert(0, 'src')

from src.data.database import db_manager
from src.data.models import Product, Site, ProductURL, PriceHistory
from src.cli.utils.logger import get_logger


class ValidationPipeline:
    """
    Pipeline for validating scraped item data.
    Implements data quality checks and validation (Project.md requirement).
    """
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.stats = {
            'items_processed': 0,
            'items_valid': 0,
            'items_invalid': 0,
            'validation_errors': {}
        }
    
    def process_item(self, item, spider):
        """
        Validate item data quality and completeness.
        
        Args:
            item: Scraped item
            spider: Spider instance
            
        Returns:
            item: Validated item
            
        Raises:
            DropItem: If item fails validation
        """
        adapter = ItemAdapter(item)
        self.stats['items_processed'] += 1
        
        # Required fields validation
        required_fields = ['url', 'site_name', 'scraped_at']
        missing_fields = []
        
        for field in required_fields:
            if not adapter.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f"Missing required fields: {missing_fields}"
            self._record_validation_error('missing_fields', error_msg)
            self.logger.warning(f"Validation failed for {adapter.get('url', 'unknown')}: {error_msg}")
            self.stats['items_invalid'] += 1
            raise DropItem(error_msg)
        
        # Title validation
        title = adapter.get('title')
        if not title or len(title.strip()) < 5:
            error_msg = "Title too short or missing"
            self._record_validation_error('invalid_title', error_msg)
            self.stats['items_invalid'] += 1
            raise DropItem(error_msg)
        
        # Price validation
        price = adapter.get('price')
        if price is not None:
            try:
                price_float = float(price)
                if price_float < 0.01 or price_float > 100000:
                    error_msg = f"Price out of valid range: {price_float}"
                    self._record_validation_error('invalid_price', error_msg)
                    self.stats['items_invalid'] += 1
                    raise DropItem(error_msg)
            except (ValueError, TypeError):
                error_msg = f"Invalid price format: {price}"
                self._record_validation_error('invalid_price_format', error_msg)
                self.stats['items_invalid'] += 1
                raise DropItem(error_msg)
        
        # URL validation
        url = adapter.get('url')
        if not url.startswith(('http://', 'https://')):
            error_msg = f"Invalid URL format: {url}"
            self._record_validation_error('invalid_url', error_msg)
            self.stats['items_invalid'] += 1
            raise DropItem(error_msg)
        
        self.stats['items_valid'] += 1
        self.logger.debug(f"Validation passed for: {title[:50]}...")
        
        return item
    
    def _record_validation_error(self, error_type: str, message: str):
        """Record validation error for statistics."""
        if error_type not in self.stats['validation_errors']:
            self.stats['validation_errors'][error_type] = 0
        self.stats['validation_errors'][error_type] += 1
    
    def close_spider(self, spider):
        """Log validation statistics when spider closes."""
        self.logger.info(f"Validation Pipeline Stats:")
        self.logger.info(f"  Items processed: {self.stats['items_processed']}")
        self.logger.info(f"  Items valid: {self.stats['items_valid']}")
        self.logger.info(f"  Items invalid: {self.stats['items_invalid']}")
        if self.stats['validation_errors']:
            self.logger.info(f"  Validation errors: {self.stats['validation_errors']}")


class DatabasePipeline:
    """
    Pipeline for storing validated items to database.
    Implements database storage requirement (Project.md line 122).
    """
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.stats = {
            'items_stored': 0,
            'items_failed': 0,
            'products_created': 0,
            'urls_created': 0,
            'prices_recorded': 0
        }
    
    def open_spider(self, spider):
        """Initialize database connection when spider opens."""
        try:
            # Initialize database if not already done
            db_manager.initialize()
            self.logger.info("Database pipeline initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def process_item(self, item, spider):
        """
        Store item data to database.
        
        Args:
            item: Validated scraped item
            spider: Spider instance
            
        Returns:
            item: Processed item
        """
        adapter = ItemAdapter(item)
        
        try:
            with db_manager.get_session() as session:
                # Get or create site
                site_name = adapter['site_name']
                site = session.query(Site).filter(Site.name == site_name).first()
                
                if not site:
                    # Create new site
                    site = Site(
                        name=site_name,
                        base_url=f"https://www.{site_name.lower()}.com",
                        scraper_type="scrapy",
                        rate_limit=2.0
                    )
                    session.add(site)
                    session.flush()
                    self.logger.info(f"Created new site: {site_name}")
                
                # Create or find product
                title = adapter['title']
                brand = adapter.get('brand', '')
                category = adapter.get('category', 'electronics')
                
                # Try to find existing product
                product = session.query(Product).filter(
                    Product.name == title,
                    Product.brand == brand
                ).first()
                
                if not product:
                    # Create new product
                    product = Product(
                        name=title,
                        category=category,
                        brand=brand,
                        model=adapter.get('model', ''),
                        status='active'
                    )
                    session.add(product)
                    session.flush()
                    self.stats['products_created'] += 1
                    self.logger.debug(f"Created new product: {title[:50]}...")
                
                # Create or find product URL
                url = adapter['url']
                product_url = session.query(ProductURL).filter(
                    ProductURL.product_id == product.id,
                    ProductURL.site_id == site.id
                ).first()
                
                if not product_url:
                    # Create new product URL
                    product_url = ProductURL(
                        product_id=product.id,
                        site_id=site.id,
                        url=url,
                        selector_config='{}',
                        is_active=True
                    )
                    session.add(product_url)
                    session.flush()
                    self.stats['urls_created'] += 1
                else:
                    # Update URL if it changed
                    if product_url.url != url:
                        product_url.url = url
                
                # Add price record
                price = adapter.get('price')
                if price is not None:
                    price_record = PriceHistory(
                        product_url_id=product_url.id,
                        price=float(price),
                        currency=adapter.get('currency', 'USD'),
                        availability=adapter.get('availability', 'unknown'),
                        scraper_metadata=self._build_metadata(adapter)
                    )
                    session.add(price_record)
                    self.stats['prices_recorded'] += 1
                
                session.commit()
                self.stats['items_stored'] += 1
                
                self.logger.debug(f"Stored item: {title[:30]}... - ${price}")
                
        except Exception as e:
            self.stats['items_failed'] += 1
            self.logger.error(f"Failed to store item {adapter.get('url', 'unknown')}: {e}")
            # Don't raise exception to avoid stopping the spider
        
        return item
    
    def _build_metadata(self, adapter: ItemAdapter) -> str:
        """Build metadata JSON for price record."""
        import json
        
        metadata = {
            'scraper_name': adapter.get('scraper_name'),
            'image_url': adapter.get('image_url'),
            'rating': adapter.get('rating'),
            'reviews_count': adapter.get('reviews_count'),
            'description': adapter.get('description'),
            'seller_info': adapter.get('seller_info'),
            'shipping_info': adapter.get('shipping_info')
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return json.dumps(metadata)
    
    def close_spider(self, spider):
        """Log database statistics when spider closes."""
        self.logger.info(f"Database Pipeline Stats:")
        self.logger.info(f"  Items stored: {self.stats['items_stored']}")
        self.logger.info(f"  Items failed: {self.stats['items_failed']}")
        self.logger.info(f"  Products created: {self.stats['products_created']}")
        self.logger.info(f"  URLs created: {self.stats['urls_created']}")
        self.logger.info(f"  Prices recorded: {self.stats['prices_recorded']}")


class StatisticsPipeline:
    """
    Pipeline for collecting scraping statistics and performance metrics.
    Implements comprehensive logging and monitoring (Project.md requirement).
    """
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.stats = {
            'start_time': None,
            'end_time': None,
            'items_processed': 0,
            'items_with_price': 0,
            'items_without_price': 0,
            'sites_scraped': set(),
            'categories_found': set(),
            'brands_found': set(),
            'price_range': {'min': None, 'max': None},
            'avg_processing_time': 0,
            'processing_times': []
        }
        self.item_start_times = {}
    
    def open_spider(self, spider):
        """Initialize statistics when spider opens."""
        self.stats['start_time'] = datetime.utcnow()
        self.logger.info(f"Statistics pipeline started for spider: {spider.name}")
    
    def process_item(self, item, spider):
        """
        Collect statistics from processed items.
        
        Args:
            item: Processed item
            spider: Spider instance
            
        Returns:
            item: Unchanged item
        """
        adapter = ItemAdapter(item)
        item_id = id(item)
        
        # Record processing time
        if item_id in self.item_start_times:
            processing_time = (datetime.utcnow() - self.item_start_times[item_id]).total_seconds()
            self.stats['processing_times'].append(processing_time)
        
        # Basic counting
        self.stats['items_processed'] += 1
        
        # Price statistics
        price = adapter.get('price')
        if price is not None:
            self.stats['items_with_price'] += 1
            price_float = float(price)
            
            if self.stats['price_range']['min'] is None or price_float < self.stats['price_range']['min']:
                self.stats['price_range']['min'] = price_float
            
            if self.stats['price_range']['max'] is None or price_float > self.stats['price_range']['max']:
                self.stats['price_range']['max'] = price_float
        else:
            self.stats['items_without_price'] += 1
        
        # Categorical data
        site_name = adapter.get('site_name')
        if site_name:
            self.stats['sites_scraped'].add(site_name)
        
        category = adapter.get('category')
        if category:
            self.stats['categories_found'].add(category)
        
        brand = adapter.get('brand')
        if brand:
            self.stats['brands_found'].add(brand)
        
        return item
    
    def close_spider(self, spider):
        """Generate final statistics report when spider closes."""
        self.stats['end_time'] = datetime.utcnow()
        
        if self.stats['start_time']:
            total_time = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        else:
            total_time = 0
        
        if self.stats['processing_times']:
            self.stats['avg_processing_time'] = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
        
        # Generate comprehensive report
        self.logger.info("=" * 60)
        self.logger.info(f"SCRAPING STATISTICS REPORT - {spider.name}")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Runtime: {total_time:.2f} seconds")
        self.logger.info(f"Items Processed: {self.stats['items_processed']}")
        self.logger.info(f"Items with Price: {self.stats['items_with_price']}")
        self.logger.info(f"Items without Price: {self.stats['items_without_price']}")
        
        if self.stats['items_processed'] > 0:
            success_rate = (self.stats['items_with_price'] / self.stats['items_processed']) * 100
            self.logger.info(f"Price Extraction Success Rate: {success_rate:.1f}%")
        
        if self.stats['price_range']['min'] is not None:
            self.logger.info(f"Price Range: ${self.stats['price_range']['min']:.2f} - ${self.stats['price_range']['max']:.2f}")
        
        self.logger.info(f"Sites Scraped: {', '.join(self.stats['sites_scraped'])}")
        self.logger.info(f"Categories Found: {len(self.stats['categories_found'])}")
        self.logger.info(f"Brands Found: {len(self.stats['brands_found'])}")
        
        if self.stats['processing_times']:
            self.logger.info(f"Avg Processing Time: {self.stats['avg_processing_time']:.3f}s per item")
        
        self.logger.info("=" * 60)


# Import DropItem here to avoid circular imports
from scrapy.exceptions import DropItem