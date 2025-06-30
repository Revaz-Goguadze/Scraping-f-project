# E-Commerce Price Monitoring System - API Reference

## Table of Contents

1. [Core Modules](#core-modules)
2. [Scrapers](#scrapers)
3. [Data Models](#data-models)
4. [Analysis](#analysis)
5. [CLI Interface](#cli-interface)
6. [Utilities](#utilities)

## Core Modules

### src.data.database

#### DatabaseManager

**Class**: `DatabaseManager`

Main database management class implementing singleton pattern.

```python
from src.data.database import db_manager

# Initialize database
db_manager.initialize()

# Get session
with db_manager.get_session() as session:
    # Database operations
    pass
```

**Methods:**

- `initialize()` - Initialize database and create tables
- `get_session()` - Get SQLAlchemy session context manager
- `create_site(name, base_url, scraper_type, rate_limit)` - Create new site
- `create_product(name, category, brand, model)` - Create new product
- `create_product_url(product_id, site_id, url)` - Create product URL mapping
- `add_price_record(product_url_id, price, currency, availability)` - Add price data

### src.data.models

#### Product

**Class**: `Product`

SQLAlchemy model for product information.

```python
from src.data.models import Product

product = Product(
    name="iPhone 15 Pro",
    category="smartphones",
    brand="Apple",
    model="iPhone 15 Pro"
)
```

**Attributes:**
- `id` (int) - Primary key
- `name` (str) - Product name
- `category` (str) - Product category
- `brand` (str) - Brand name
- `model` (str) - Model identifier
- `status` (str) - Status (active/inactive)
- `created_at` (datetime) - Creation timestamp

#### Site

**Class**: `Site`

SQLAlchemy model for e-commerce sites.

```python
from src.data.models import Site

site = Site(
    name="Amazon",
    base_url="https://www.amazon.com",
    scraper_type="static",
    rate_limit=2.0
)
```

**Attributes:**
- `id` (int) - Primary key
- `name` (str) - Site name
- `base_url` (str) - Base URL
- `scraper_type` (str) - Scraper type (static/selenium/scrapy)
- `rate_limit` (float) - Rate limit in seconds
- `created_at` (datetime) - Creation timestamp

#### PriceHistory

**Class**: `PriceHistory`

SQLAlchemy model for price tracking.

```python
from src.data.models import PriceHistory

price_record = PriceHistory(
    product_url_id=1,
    price=99.99,
    currency="USD",
    availability="in_stock"
)
```

**Attributes:**
- `id` (int) - Primary key
- `product_url_id` (int) - Foreign key to ProductURL
- `price` (decimal) - Product price
- `currency` (str) - Currency code
- `availability` (str) - Availability status
- `scraped_at` (datetime) - Scraping timestamp
- `scraper_metadata` (text) - JSON metadata

## Scrapers

### src.scrapers.factory

#### ScraperFactory

**Class**: `ScraperFactory`

Factory pattern implementation for creating scrapers.

```python
from src.scrapers.factory import ScraperFactory

# Create scraper
scraper = ScraperFactory.create_scraper('amazon')

# Get available scrapers
scrapers = ScraperFactory.get_available_scrapers()
```

**Methods:**
- `create_scraper(site_name)` - Create scraper instance
- `get_available_scrapers()` - Get dict of available scrapers
- `get_supported_sites()` - Get list of supported sites

### src.scrapers.base_scraper

#### AbstractScraper

**Class**: `AbstractScraper`

Abstract base class for all scrapers implementing strategy pattern.

```python
from src.scrapers.base_scraper import AbstractScraper

class CustomScraper(AbstractScraper):
    def parse_page(self, html_content, url):
        # Implementation
        pass
```

**Methods:**
- `scrape_product(url)` - Main scraping method
- `fetch_page(url)` - Fetch page content
- `parse_page(html_content, url)` - Parse page (abstract)
- `handle_error(error, url)` - Error handling
- `get_scraper_stats()` - Get statistics

### src.scrapers.concurrent_manager

#### ConcurrentScrapingManager

**Class**: `ConcurrentScrapingManager`

Manages concurrent scraping operations.

```python
from src.scrapers.concurrent_manager import ConcurrentScrapingManager

manager = ConcurrentScrapingManager(max_workers=3)
manager.add_job('amazon', 'https://amazon.com/dp/123')
manager.start_workers()
manager.wait_completion()
manager.stop_workers()
```

**Methods:**
- `add_job(site_name, url, priority=1)` - Add single job
- `add_bulk_jobs(jobs)` - Add multiple jobs
- `start_workers()` - Start worker threads
- `stop_workers()` - Stop workers
- `wait_completion(timeout=None)` - Wait for completion
- `get_statistics()` - Get performance statistics

### src.scrapers.static_scraper

#### AmazonScraper

**Class**: `AmazonScraper`

BeautifulSoup-based scraper for Amazon products.

```python
from src.scrapers.static_scraper import AmazonScraper

scraper = AmazonScraper()
product_data = scraper.scrape_product('https://amazon.com/dp/123')
```

#### EbayScraper

**Class**: `EbayScraper`

BeautifulSoup-based scraper for eBay products.

```python
from src.scrapers.static_scraper import EbayScraper

scraper = EbayScraper()
product_data = scraper.scrape_product('https://ebay.com/itm/123')
```

### src.scrapers.selenium_scraper

#### WalmartSeleniumScraper

**Class**: `WalmartSeleniumScraper`

Selenium-based scraper for Walmart products.

```python
from src.scrapers.selenium_scraper import WalmartSeleniumScraper

scraper = WalmartSeleniumScraper()
product_data = scraper.scrape_product('https://walmart.com/ip/123')
scraper.cleanup()  # Important: clean up driver
```

## Data Models

### src.scrapers.data_models

#### ProductData

**Class**: `ProductData`

Data structure for scraped product information.

```python
from src.scrapers.data_models import ProductData

product = ProductData('https://example.com/product')
product.title = "Product Name"
product.price = 99.99
product.availability = "in_stock"
```

**Attributes:**
- `url` (str) - Product URL
- `title` (str) - Product title
- `price` (float) - Product price
- `currency` (str) - Currency code
- `availability` (str) - Availability status
- `brand` (str) - Brand name
- `model` (str) - Model identifier
- `image_url` (str) - Image URL
- `rating` (float) - Product rating
- `metadata` (dict) - Additional metadata

## Analysis

### src.analysis.statistics

#### StatisticsAnalyzer

**Class**: `StatisticsAnalyzer`

Performs statistical analysis on price data.

```python
from src.analysis.statistics import StatisticsAnalyzer

analyzer = StatisticsAnalyzer()

# Get overall statistics
stats = analyzer.get_overall_database_statistics()

# Get product-specific statistics
product_stats = analyzer.get_price_statistics_for_product(product_id=1)

# Get price volatility
volatility = analyzer.get_price_volatility(top_n=10)
```

**Methods:**
- `get_overall_database_statistics()` - Database-wide statistics
- `get_price_statistics_for_product(product_id)` - Product statistics
- `get_price_volatility(top_n=10)` - Most volatile products
- `get_best_deals(category=None, top_n=10)` - Best price deals

### src.analysis.trends

#### TrendAnalyzer

**Class**: `TrendAnalyzer`

Analyzes price trends over time.

```python
from src.analysis.trends import TrendAnalyzer

analyzer = TrendAnalyzer()
trend_data = analyzer.analyze_price_trend(product_id=1, days=30)
```

### src.analysis.reports

#### ReportGenerator

**Class**: `ReportGenerator`

Generates various types of reports.

```python
from src.analysis.reports import ReportGenerator

generator = ReportGenerator()
html_report = generator.generate_html_report()
```

## CLI Interface

### src.cli.interface

#### CLI Commands

**Functions:**

```python
# Main CLI entry point
from src.cli.interface import cli

# Scraping commands
from src.cli.commands.scrape_commands import run

# Analysis commands  
from src.cli.commands.analysis_commands import product, volatility

# Database commands
from src.cli.commands.db_commands import init, reset
```

### src.cli.commands.scrape_commands

#### run()

Run scrapers for specified sites.

```bash
python -m src.cli.interface scrape run --site amazon --workers 3
```

**Parameters:**
- `--site` - Target site(s)
- `--workers` - Number of concurrent workers
- `--use-multiprocessing` - Use multiprocessing
- `--limit` - Limit URLs per site

### src.cli.commands.analysis_commands

#### product()

Get price statistics for specific product.

```bash
python -m src.cli.interface analyze product --id 1
```

#### volatility()

Find products with most volatile prices.

```bash
python -m src.cli.interface analyze volatility --top 10
```

### src.cli.commands.db_commands

#### init()

Initialize database.

```bash
python -m src.cli.interface db init
```

#### reset()

Reset database (WARNING: Deletes all data).

```bash
python -m src.cli.interface db reset
```

## Utilities

### src.cli.utils.config

#### ConfigManager

**Class**: `ConfigManager`

Configuration management singleton.

```python
from src.cli.utils.config import config_manager

# Load configuration
config_manager.load_config()

# Get setting
workers = config_manager.get_setting('scraping.concurrent_workers')

# Get scraper config
amazon_config = config_manager.get_scraper_config('amazon')
```

**Methods:**
- `load_config()` - Load configuration files
- `get_setting(key, default=None)` - Get configuration setting
- `get_scraper_config(site_name)` - Get site-specific configuration
- `get_all_sites()` - Get all configured sites

### src.cli.utils.logger

#### LoggerManager

**Class**: `LoggerManager`

Logging system manager.

```python
from src.cli.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

**Functions:**
- `get_logger(name)` - Get logger instance
- `LoggerManager.set_session_id(session_id)` - Set session ID

### src.data.processors

#### DataProcessor

**Class**: `DataProcessor`

Data validation and processing.

```python
from src.data.processors import DataProcessor

processor = DataProcessor()
processed_data = processor.process(raw_product_data)
```

**Methods:**
- `process(product_data)` - Process and validate data
- `validate_price(price)` - Validate price data
- `validate_title(title)` - Validate title data
- `clean_text(text)` - Clean text data

## Error Handling

### Custom Exceptions

#### ScrapingError

**Class**: `ScrapingError`

Custom exception for scraping errors.

```python
from src.scrapers.data_models import ScrapingError

raise ScrapingError("Error message", "error_type", "url")
```

**Attributes:**
- `message` (str) - Error message
- `error_type` (str) - Error type (network, parsing, etc.)
- `url` (str) - Associated URL
- `response_code` (int) - HTTP response code

## Usage Examples

### Basic Scraping

```python
from src.scrapers.factory import ScraperFactory
from src.data.database import db_manager

# Initialize database
db_manager.initialize()

# Create and use scraper
scraper = ScraperFactory.create_scraper('amazon')
product_data = scraper.scrape_product('https://amazon.com/dp/B0863FR3S9')

if product_data:
    print(f"Title: {product_data.title}")
    print(f"Price: ${product_data.price}")
```

### Concurrent Scraping

```python
from src.scrapers.concurrent_manager import ConcurrentScrapingManager

manager = ConcurrentScrapingManager(max_workers=3)

jobs = [
    {'site_name': 'amazon', 'url': 'https://amazon.com/dp/123'},
    {'site_name': 'ebay', 'url': 'https://ebay.com/itm/456'}
]

manager.add_bulk_jobs(jobs)
manager.start_workers()
manager.wait_completion()

stats = manager.get_statistics()
print(f"Completed: {stats['jobs_completed']}")
```

### Data Analysis

```python
from src.analysis.statistics import StatisticsAnalyzer

analyzer = StatisticsAnalyzer()

# Overall statistics
overall_stats = analyzer.get_overall_database_statistics()
print(f"Total products: {overall_stats['total_products']}")

# Product-specific analysis
product_stats = analyzer.get_price_statistics_for_product(1)
if product_stats:
    print(f"Average price: ${product_stats['mean_price']:.2f}")
```

### Configuration

```python
from src.cli.utils.config import config_manager

# Load configuration
config_manager.load_config()

# Get setting
workers = config_manager.get_setting('scraping.concurrent_workers', 3)

# Get scraper configuration
amazon_config = config_manager.get_scraper_config('amazon')
rate_limit = amazon_config.get('rate_limit', 2.0)
```

## Return Types

### Common Return Types

- **ProductData**: Scraped product information
- **Dict[str, Any]**: Statistics and configuration data
- **List[ProductData]**: Multiple product results
- **bool**: Success/failure status
- **Optional[T]**: Nullable return values

### HTTP Status Codes

The system handles standard HTTP status codes:

- **200**: Success
- **404**: Not found
- **429**: Rate limited
- **500-504**: Server errors

### Error Codes

Custom error types:

- **"network"**: Network/connection errors
- **"parsing"**: HTML parsing errors
- **"validation"**: Data validation errors
- **"timeout"**: Request timeout errors

---

For more examples and detailed usage, see the [User Guide](user_guide.md).
