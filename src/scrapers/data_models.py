"""
Data models for the scrapers package.
Contains data structures for scraped product information.
"""

from typing import Dict, Any, Optional
import time


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