"""
Data processing and validation pipeline for scraped product data.
Implements data cleaning, validation, and normalization based on configurable rules.
"""

from typing import Dict, Any, Optional
import re

from ..scrapers.base_scraper import ProductData
from ..cli.utils.config import config_manager
from ..cli.utils.logger import get_logger

logger = get_logger(__name__)


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class DataProcessor:
    """
    Handles cleaning, validation, and normalization of scraped product data.
    Uses rules defined in configuration files to ensure data quality.
    """

    def __init__(self):
        """Initialize the data processor and load validation rules."""
        self.validation_rules = config_manager.get_validation_rules()
        logger.info("DataProcessor initialized with validation rules.")

    def process(self, product_data: ProductData) -> ProductData:
        """
        Run the full processing pipeline on product data.

        Args:
            product_data: The scraped product data object.

        Returns:
            The processed and validated product data object.

        Raises:
            DataValidationError: If the data fails validation.
        """
        if not isinstance(product_data, ProductData):
            raise TypeError("Input must be a ProductData object.")

        # Step 1: Normalize data
        normalized_data = self.normalize(product_data)

        # Step 2: Validate data
        is_valid, errors = self.validate(normalized_data)
        if not is_valid:
            error_message = f"Data validation failed for URL {product_data.url}: {', '.join(errors)}"
            logger.error(error_message)
            raise DataValidationError(error_message)

        logger.debug(f"Data for {product_data.url} processed successfully.")
        return normalized_data

    def validate(self, product_data: ProductData) -> (bool, list):
        """
        Validate product data against rules from configuration.

        Args:
            product_data: The product data to validate.

        Returns:
            A tuple containing a boolean (True if valid) and a list of error messages.
        """
        errors = []

        # Validate title
        title_rules = self.validation_rules.get('title', {})
        if title_rules:
            title = product_data.title
            if not title:
                errors.append("Title is missing.")
            else:
                if len(title) < title_rules.get('min_length', 3):
                    errors.append(f"Title is too short (min: {title_rules['min_length']}).")
                if len(title) > title_rules.get('max_length', 500):
                    errors.append(f"Title is too long (max: {title_rules['max_length']}).")

        # Validate price
        price_rules = self.validation_rules.get('price', {})
        if price_rules and product_data.price is not None:
            price = product_data.price
            if not (price_rules.get('min_value', 0.01) <= price <= price_rules.get('max_value', 10000)):
                errors.append(f"Price is out of range ({price}).")

        # Validate availability
        availability_rules = self.validation_rules.get('availability', {})
        if availability_rules and product_data.availability:
            valid_statuses = availability_rules.get('valid_statuses', [])
            if product_data.availability not in valid_statuses:
                errors.append(f"Invalid availability status: {product_data.availability}.")

        return not errors, errors

    def normalize(self, product_data: ProductData) -> ProductData:
        """
        Normalize and clean product data fields.

        Args:
            product_data: The product data to normalize.

        Returns:
            The normalized product data object.
        """
        # Normalize title
        if product_data.title:
            product_data.title = ' '.join(product_data.title.strip().split())

        # Normalize availability
        if product_data.availability:
            product_data.availability = self._normalize_availability(product_data.availability)

        # Normalize image URL
        if product_data.image_url:
            # Potentially resolve relative URLs here if needed
            pass

        # Normalize rating (ensure it's a float between 0 and 5)
        if product_data.rating is not None:
            try:
                rating = float(product_data.rating)
                if not (0 <= rating <= 5):
                    product_data.rating = None
            except (ValueError, TypeError):
                product_data.rating = None

        # Normalize reviews count (ensure it's an integer)
        if product_data.reviews_count is not None:
            try:
                product_data.reviews_count = int(product_data.reviews_count)
            except (ValueError, TypeError):
                product_data.reviews_count = None

        return product_data

    def _normalize_availability(self, status: str) -> str:
        """
        Normalize availability string to a standard set of statuses.

        Args:
            status: The raw availability string.

        Returns:
            A normalized availability status.
        """
        if not status:
            return 'unknown'

        status_lower = status.lower()
        valid_statuses = self.validation_rules.get('availability', {}).get('valid_statuses', [])

        if any(term in status_lower for term in ['in stock', 'available', 'ships', 'add to cart']):
            return 'in_stock'
        if any(term in status_lower for term in ['out of stock', 'unavailable']):
            return 'out_of_stock'
        if 'limited' in status_lower:
            return 'limited'

        # Return the original if it's already a valid status, otherwise unknown
        return status if status in valid_statuses else 'unknown'
