"""
Database models for the E-Commerce Price Monitoring System.
Implements the SQLAlchemy ORM models for products, sites, URLs, price history, and scraping sessions.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DECIMAL, Boolean, DateTime, 
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()


class Product(Base):
    """
    Master product catalog table.
    Stores product information independent of any specific e-commerce site.
    """
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False)  # electronics, smartphones, laptops, tablets
    brand = Column(String(100), nullable=True)
    model = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default='active')  # active, inactive, discontinued
    
    # Relationships
    product_urls = relationship("ProductURL", back_populates="product", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_product_category', 'category'),
        Index('idx_product_brand', 'brand'),
        Index('idx_product_status', 'status'),
        UniqueConstraint('name', 'brand', 'model', name='uq_product_identity'),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', brand='{self.brand}')>"


class Site(Base):
    """
    E-commerce site configuration table.
    Stores site-specific settings and scraping configurations.
    """
    __tablename__ = 'sites'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)  # Amazon, eBay, Walmart
    base_url = Column(String(200), nullable=False)
    scraper_type = Column(String(50), nullable=False)  # static, selenium, scrapy
    rate_limit = Column(DECIMAL(4, 2), default=2.0)  # seconds between requests
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product_urls = relationship("ProductURL", back_populates="site", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Site(id={self.id}, name='{self.name}', scraper_type='{self.scraper_type}')>"


class ProductURL(Base):
    """
    Product-specific URLs for each site.
    Links products to their URLs on different e-commerce sites.
    """
    __tablename__ = 'product_urls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    site_id = Column(Integer, ForeignKey('sites.id'), nullable=False)
    url = Column(Text, nullable=False)
    selector_config = Column(Text, nullable=True)  # JSON string with site-specific selectors
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="product_urls")
    site = relationship("Site", back_populates="product_urls")
    price_history = relationship("PriceHistory", back_populates="product_url", cascade="all, delete-orphan")
    scraping_errors = relationship("ScrapingError", back_populates="product_url", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_product_url_product_id', 'product_id'),
        Index('idx_product_url_site_id', 'site_id'),
        Index('idx_product_url_active', 'is_active'),
        UniqueConstraint('product_id', 'site_id', name='uq_product_site'),
    )
    
    def __repr__(self):
        return f"<ProductURL(id={self.id}, product_id={self.product_id}, site_id={self.site_id})>"


class PriceHistory(Base):
    """
    Historical price tracking table.
    Stores price data points over time for each product URL.
    """
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_url_id = Column(Integer, ForeignKey('product_urls.id'), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=True)  # Null if product unavailable
    currency = Column(String(3), default='USD')
    availability = Column(String(50), nullable=True)  # in_stock, out_of_stock, limited, unknown
    scraped_at = Column(DateTime, default=datetime.utcnow)
    scraper_metadata = Column(Text, nullable=True)  # JSON with additional scraping data
    
    # Relationships
    product_url = relationship("ProductURL", back_populates="price_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_price_history_product_url_id', 'product_url_id'),
        Index('idx_price_history_scraped_at', 'scraped_at'),
        Index('idx_price_history_availability', 'availability'),
    )
    
    def __repr__(self):
        return f"<PriceHistory(id={self.id}, price={self.price}, scraped_at={self.scraped_at})>"


class ScrapingSession(Base):
    """
    Scraping job tracking and monitoring table.
    Tracks each scraping run with metadata and statistics.
    """
    __tablename__ = 'scraping_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, unique=True)  # UUID
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False)  # running, completed, failed, cancelled
    products_scraped = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    session_metadata = Column(Text, nullable=True)  # JSON with session configuration and stats
    
    # Relationships
    scraping_errors = relationship("ScrapingError", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_scraping_session_id', 'session_id'),
        Index('idx_scraping_session_started_at', 'started_at'),
        Index('idx_scraping_session_status', 'status'),
    )
    
    def __repr__(self):
        return f"<ScrapingSession(session_id='{self.session_id}', status='{self.status}')>"


class ScrapingError(Base):
    """
    Error tracking and debugging table.
    Stores errors encountered during scraping for analysis and debugging.
    """
    __tablename__ = 'scraping_errors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('scraping_sessions.id'), nullable=False)
    product_url_id = Column(Integer, ForeignKey('product_urls.id'), nullable=True)
    error_type = Column(String(100), nullable=False)  # network, parsing, validation, system
    error_message = Column(Text, nullable=False)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    
    # Relationships
    session = relationship("ScrapingSession", back_populates="scraping_errors")
    product_url = relationship("ProductURL", back_populates="scraping_errors")
    
    # Indexes
    __table_args__ = (
        Index('idx_scraping_error_session_id', 'session_id'),
        Index('idx_scraping_error_type', 'error_type'),
        Index('idx_scraping_error_occurred_at', 'occurred_at'),
        Index('idx_scraping_error_resolved', 'resolved'),
    )
    
    def __repr__(self):
        return f"<ScrapingError(id={self.id}, error_type='{self.error_type}', resolved={self.resolved})>"


# Database configuration and utility functions
class DatabaseConfig:
    """Database configuration and session management."""
    
    def __init__(self, database_url: str = "sqlite:///data/price_monitor.db"):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
    
    def initialize(self):
        """Initialize database engine and session factory."""
        self.engine = create_engine(
            self.database_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,
            connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all database tables."""
        if self.engine is None:
            self.initialize()
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        if self.engine is None:
            self.initialize()
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Get a new database session."""
        if self.SessionLocal is None:
            self.initialize()
        return self.SessionLocal()


# Global database instance (Singleton pattern will be implemented in database.py)
db_config = DatabaseConfig()