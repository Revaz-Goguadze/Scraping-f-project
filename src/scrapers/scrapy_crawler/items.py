"""
Scrapy items for the E-Commerce Price Monitoring System.
Defines data structures for scraped product information.
"""

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags
import re


def clean_price(value):
    """Clean and extract numeric price value."""
    if not value:
        return None
    # Remove currency symbols and extract numbers
    price_text = re.sub(r'[^\d.,]', '', ''.join(value))
    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
    if price_match:
        try:
            return float(price_match.group().replace(',', ''))
        except ValueError:
            return None
    return None


def clean_text(value):
    """Clean HTML tags and normalize whitespace."""
    if not value:
        return None
    cleaned = remove_tags(''.join(value))
    return ' '.join(cleaned.split())


def extract_availability(value):
    """Normalize availability status."""
    if not value:
        return 'unknown'
    
    text = ''.join(value).lower()
    if any(term in text for term in ['in stock', 'available', 'ships']):
        return 'in_stock'
    elif any(term in text for term in ['out of stock', 'unavailable']):
        return 'out_of_stock'
    elif 'limited' in text:
        return 'limited'
    else:
        return 'unknown'


class ProductItem(scrapy.Item):
    """
    Product item for scraped e-commerce data.
    Defines all fields that can be extracted from product pages.
    """
    
    # Basic product information
    url = scrapy.Field()
    title = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    price = scrapy.Field(
        input_processor=MapCompose(clean_price),
        output_processor=TakeFirst()
    )
    currency = scrapy.Field(
        output_processor=TakeFirst()
    )
    availability = scrapy.Field(
        input_processor=MapCompose(extract_availability),
        output_processor=TakeFirst()
    )
    
    # Product details
    brand = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    model = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    category = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # Media and reviews
    image_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    rating = scrapy.Field(
        output_processor=TakeFirst()
    )
    reviews_count = scrapy.Field(
        output_processor=TakeFirst()
    )
    
    # Metadata
    site_name = scrapy.Field(
        output_processor=TakeFirst()
    )
    scraped_at = scrapy.Field(
        output_processor=TakeFirst()
    )
    scraper_name = scrapy.Field(
        output_processor=TakeFirst()
    )
    
    # Additional data
    description = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(' ')
    )
    specifications = scrapy.Field()
    seller_info = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    shipping_info = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )