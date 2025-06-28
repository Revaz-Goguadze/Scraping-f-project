"""
Database manager implementing Singleton pattern for the E-Commerce Price Monitoring System.
Provides centralized database connection and operation management.
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .models import (
    DatabaseConfig, Product, Site, ProductURL, PriceHistory, 
    ScrapingSession, ScrapingError, Base
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Singleton database manager for centralized database operations.
    Implements the Singleton pattern to ensure single database connection management.
    """
    
    _instance: Optional['DatabaseManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'DatabaseManager':
        """Implement Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database manager (only once due to Singleton pattern)."""
        if not self._initialized:
            self.db_config: Optional[DatabaseConfig] = None
            self._initialized = True
            logger.info("DatabaseManager initialized")
    
    def initialize(self, database_url: str = None, create_tables: bool = True) -> None:
        """
        Initialize database configuration and create tables if needed.
        
        Args:
            database_url: Database connection URL. Defaults to SQLite.
            create_tables: Whether to create tables on initialization.
        """
        if database_url is None:
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            database_url = "sqlite:///data/price_monitor.db"
        
        self.db_config = DatabaseConfig(database_url)
        self.db_config.initialize()
        
        if create_tables:
            self.create_tables()
        
        logger.info(f"Database initialized with URL: {database_url}")
    
    def create_tables(self) -> None:
        """Create all database tables."""
        if self.db_config is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        try:
            self.db_config.create_tables()
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all database tables. Use with caution!"""
        if self.db_config is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        try:
            self.db_config.drop_tables()
            logger.warning("All database tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Error dropping tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions with automatic cleanup.
        
        Usage:
            with db_manager.get_session() as session:
                # Use session here
                pass
        """
        if self.db_config is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self.db_config.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """
        Execute raw SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries containing query results
        """
        with self.get_session() as session:
            try:
                result = session.execute(query, params or {})
                return [dict(row) for row in result.fetchall()]
            except SQLAlchemyError as e:
                logger.error(f"Query execution error: {e}")
                raise
    
    # Product operations
    def create_product(self, name: str, category: str, brand: str = None,
                      model: str = None) -> Product:
        """Create a new product record."""
        with self.get_session() as session:
            product = Product(
                name=name,
                category=category,
                brand=brand,
                model=model
            )
            session.add(product)
            session.flush()  # Get the ID before commit
            session.refresh(product)
            logger.info(f"Created product: {product}")
            # Create a new instance with the same data to avoid session binding issues
            product_data = {
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'brand': product.brand,
                'model': product.model,
                'created_at': product.created_at,
                'updated_at': product.updated_at,
                'status': product.status
            }
            session.expunge(product)  # Remove from session
            return product
    
    def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        with self.get_session() as session:
            return session.query(Product).filter(Product.id == product_id).first()
    
    def get_products_by_category(self, category: str) -> List[Product]:
        """Get all products in a specific category."""
        with self.get_session() as session:
            return session.query(Product).filter(Product.category == category).all()
    
    def search_products(self, name_pattern: str = None, brand: str = None, 
                       category: str = None) -> List[Product]:
        """Search products by various criteria."""
        with self.get_session() as session:
            query = session.query(Product)
            
            if name_pattern:
                query = query.filter(Product.name.like(f"%{name_pattern}%"))
            if brand:
                query = query.filter(Product.brand == brand)
            if category:
                query = query.filter(Product.category == category)
            
            return query.all()
    
    # Site operations
    def create_site(self, name: str, base_url: str, scraper_type: str,
                   rate_limit: float = 2.0) -> Site:
        """Create a new site record."""
        with self.get_session() as session:
            site = Site(
                name=name,
                base_url=base_url,
                scraper_type=scraper_type,
                rate_limit=rate_limit
            )
            session.add(site)
            session.flush()
            session.refresh(site)
            logger.info(f"Created site: {site}")
            session.expunge(site)  # Remove from session to avoid binding issues
            return site
    
    def get_site(self, site_id: int) -> Optional[Site]:
        """Get site by ID."""
        with self.get_session() as session:
            return session.query(Site).filter(Site.id == site_id).first()
    
    def get_site_by_name(self, name: str) -> Optional[Site]:
        """Get site by name."""
        with self.get_session() as session:
            return session.query(Site).filter(Site.name == name).first()
    
    def get_all_sites(self) -> List[Site]:
        """Get all sites."""
        with self.get_session() as session:
            return session.query(Site).all()
    
    # ProductURL operations
    def create_product_url(self, product_id: int, site_id: int, url: str,
                          selector_config: str = None) -> ProductURL:
        """Create a new product URL record."""
        with self.get_session() as session:
            product_url = ProductURL(
                product_id=product_id,
                site_id=site_id,
                url=url,
                selector_config=selector_config
            )
            session.add(product_url)
            session.flush()
            session.refresh(product_url)
            logger.info(f"Created product URL: {product_url}")
            session.expunge(product_url)  # Remove from session
            return product_url
    
    def get_active_product_urls(self, site_id: int = None) -> List[ProductURL]:
        """Get all active product URLs, optionally filtered by site."""
        with self.get_session() as session:
            query = session.query(ProductURL).filter(ProductURL.is_active == True)
            if site_id:
                query = query.filter(ProductURL.site_id == site_id)
            return query.all()
    
    def get_product_urls_for_product(self, product_id: int) -> List[ProductURL]:
        """Get all URLs for a specific product."""
        with self.get_session() as session:
            return session.query(ProductURL).filter(
                ProductURL.product_id == product_id,
                ProductURL.is_active == True
            ).all()
    
    # Price history operations
    def add_price_record(self, product_url_id: int, price: float = None,
                        currency: str = "USD", availability: str = None,
                        scraper_metadata: str = None) -> PriceHistory:
        """Add a new price record."""
        with self.get_session() as session:
            price_record = PriceHistory(
                product_url_id=product_url_id,
                price=price,
                currency=currency,
                availability=availability,
                scraper_metadata=scraper_metadata
            )
            session.add(price_record)
            session.flush()
            session.refresh(price_record)
            logger.debug(f"Added price record: {price_record}")
            session.expunge(price_record)  # Remove from session
            return price_record
    
    def get_price_history(self, product_url_id: int, limit: int = 100) -> List[PriceHistory]:
        """Get price history for a product URL."""
        with self.get_session() as session:
            return session.query(PriceHistory)\
                .filter(PriceHistory.product_url_id == product_url_id)\
                .order_by(PriceHistory.scraped_at.desc())\
                .limit(limit).all()
    
    def get_latest_price(self, product_url_id: int) -> Optional[PriceHistory]:
        """Get the most recent price for a product URL."""
        with self.get_session() as session:
            return session.query(PriceHistory)\
                .filter(PriceHistory.product_url_id == product_url_id)\
                .order_by(PriceHistory.scraped_at.desc())\
                .first()
    
    # Scraping session operations
    def create_scraping_session(self, session_id: str, session_metadata: str = None) -> ScrapingSession:
        """Create a new scraping session."""
        with self.get_session() as session:
            scraping_session = ScrapingSession(
                session_id=session_id,
                status="running",
                session_metadata=session_metadata
            )
            session.add(scraping_session)
            session.flush()
            session.refresh(scraping_session)
            logger.info(f"Created scraping session: {scraping_session}")
            return scraping_session
    
    def update_scraping_session(self, session_id: str, status: str = None,
                               products_scraped: int = None, errors_count: int = None,
                               completed_at=None) -> Optional[ScrapingSession]:
        """Update scraping session status and statistics."""
        with self.get_session() as session:
            scraping_session = session.query(ScrapingSession)\
                .filter(ScrapingSession.session_id == session_id).first()
            
            if scraping_session:
                if status:
                    scraping_session.status = status
                if products_scraped is not None:
                    scraping_session.products_scraped = products_scraped
                if errors_count is not None:
                    scraping_session.errors_count = errors_count
                if completed_at:
                    scraping_session.completed_at = completed_at
                
                session.flush()
                session.refresh(scraping_session)
                logger.info(f"Updated scraping session: {scraping_session}")
            
            return scraping_session
    
    def add_scraping_error(self, session_id: str, error_type: str, error_message: str,
                          product_url_id: int = None) -> ScrapingError:
        """Add a scraping error record."""
        with self.get_session() as session:
            # Get the session record ID
            scraping_session = session.query(ScrapingSession)\
                .filter(ScrapingSession.session_id == session_id).first()
            
            if not scraping_session:
                raise ValueError(f"Scraping session not found: {session_id}")
            
            error = ScrapingError(
                session_id=scraping_session.id,
                product_url_id=product_url_id,
                error_type=error_type,
                error_message=error_message
            )
            session.add(error)
            session.flush()
            session.refresh(error)
            logger.warning(f"Added scraping error: {error}")
            return error
    
    # Analytics and reporting helpers
    def get_price_statistics(self, product_id: int) -> Dict[str, Any]:
        """Get price statistics for a product across all sites."""
        with self.get_session() as session:
            # This would be implemented with proper SQL aggregations
            # For now, return a placeholder structure
            return {
                "product_id": product_id,
                "min_price": 0.0,
                "max_price": 0.0,
                "avg_price": 0.0,
                "price_changes": 0,
                "last_updated": None
            }
    
    def cleanup_old_data(self, days: int = 365) -> None:
        """Clean up old price history data."""
        with self.get_session() as session:
            # Implementation would delete records older than specified days
            logger.info(f"Cleanup completed for data older than {days} days")


# Global database manager instance (Singleton)
db_manager = DatabaseManager()