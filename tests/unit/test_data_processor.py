"""
Unit tests for the DataProcessor.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data.processors import DataProcessor, DataValidationError
from src.scrapers.base_scraper import ProductData


@pytest.fixture
def data_processor():
    """Fixture to provide a DataProcessor instance."""
    return DataProcessor()


def test_valid_product_data_processing(data_processor):
    """Test that valid product data is processed successfully."""
    product = ProductData(url="http://example.com/product")
    product.title = "  Valid Product Title  "
    product.price = 99.99
    product.availability = "In Stock"
    
    processed_product = data_processor.process(product)
    
    assert processed_product.title == "Valid Product Title"
    assert processed_product.price == 99.99
    assert processed_product.availability == "in_stock"


def test_invalid_title_raises_error(data_processor):
    """Test that a product with an invalid title raises a DataValidationError."""
    product = ProductData(url="http://example.com/product")
    product.title = "shrt"
    product.price = 99.99
    
    with pytest.raises(DataValidationError, match="Title is too short"):
        data_processor.process(product)


def test_invalid_price_raises_error(data_processor):
    """Test that a product with an out-of-range price raises a DataValidationError."""
    product = ProductData(url="http://example.com/product")
    product.title = "Product with invalid price"
    product.price = 15000.00
    
    with pytest.raises(DataValidationError, match="Price is out of range"):
        data_processor.process(product)


def test_normalization(data_processor):
    """Test various normalization scenarios."""
    product = ProductData(url="http://example.com/product")
    product.title = "  Product with extra spaces  "
    product.availability = "Currently unavailable"
    product.rating = "4.5"
    product.reviews_count = "1,234"
    
    normalized_product = data_processor.normalize(product)
    
    assert normalized_product.title == "Product with extra spaces"
    assert normalized_product.availability == "out_of_stock"
    assert normalized_product.rating == 4.5
    assert normalized_product.reviews_count == 1234 