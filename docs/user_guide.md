# E-Commerce Price Monitoring System - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Configuration](#configuration)
5. [Data Analysis](#data-analysis)
6. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Chrome browser (for Selenium)
- 512MB+ available RAM
- 100MB+ disk space

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd final-project
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database:**
   ```bash
   python setup_sample_data.py
   ```

4. **Verify installation:**
   ```bash
   python test_implementation.py
   ```

## Basic Usage

### Interactive Interface

The easiest way to use the system is through the interactive menu:

```bash
python main.py
```

This will present you with options:
- Scrape eBay products
- Scrape Amazon products  
- Scrape both sites
- Exit

### Command-Line Interface

For advanced users, use the CLI directly:

```bash
python -m src.cli.interface [COMMAND] [OPTIONS]
```

#### Available Commands

- `scrape` - Run scrapers
- `analyze` - Perform data analysis  
- `db` - Database management

#### Scraping Commands

```bash
# Scrape all sites with default settings
python -m src.cli.interface scrape run

# Scrape specific site
python -m src.cli.interface scrape run --site amazon

# Use multiple workers
python -m src.cli.interface scrape run --site ebay --workers 5

# Limit number of URLs per site
python -m src.cli.interface scrape run --limit 10
```

#### Analysis Commands

```bash
# Get statistics for a specific product
python -m src.cli.interface analyze product --id 1

# Find most volatile products
python -m src.cli.interface analyze volatility

# Analyze price trends
python -m src.cli.interface analyze trend --product-id 1
```

#### Database Commands

```bash
# Initialize database
python -m src.cli.interface db init

# Reset database (WARNING: Deletes all data)
python -m src.cli.interface db reset
```

## Advanced Features

### Using Scrapy Framework

The system includes a full Scrapy implementation for advanced crawling:

```bash
cd src/scrapers/scrapy_crawler

# Crawl Amazon products
scrapy crawl amazon -a urls="https://www.amazon.com/dp/B0863FR3S9"

# Search Amazon by keyword
scrapy crawl amazon_search -a query="headphones" -a max_pages=3

# Output to specific format
scrapy crawl amazon -o data_output/amazon_products.json
```

### Concurrent Processing

The system automatically uses concurrent processing for faster scraping:

- **Threading**: Default mode for I/O-bound operations
- **Workers**: Configurable number (default: 3)
- **Rate Limiting**: Automatic per-site rate limiting
- **Queue Management**: Intelligent job scheduling

### Configuration Customization

#### System Settings (config/settings.yaml)

```yaml
scraping:
  concurrent_workers: 3      # Number of concurrent workers
  default_delay: 2.0        # Default delay between requests
  max_retries: 3            # Maximum retry attempts
  timeout: 30               # Request timeout in seconds

database:
  type: sqlite              # Database type
  path: data/price_monitor.db  # Database file path

logging:
  level: INFO               # Logging level
  file_path: logs/price_monitor.log
```

#### Scraper Settings (config/scrapers.yaml)

```yaml
sites:
  amazon:
    rate_limit: 2.0         # Seconds between requests
    selectors:
      title: "#productTitle"  # CSS selector for title
      price: ".a-price-whole" # CSS selector for price
```

## Data Analysis

### Statistical Analysis

The system provides comprehensive statistical analysis:

#### Price Statistics
- Mean, median, standard deviation
- Min/max price ranges
- Price volatility (coefficient of variation)
- Trend analysis over time

#### Market Analysis
- Cross-platform price comparison
- Category-wise analytics
- Brand comparison
- Availability tracking

### Data Export

Export data in multiple formats:

```bash
# Export via Scrapy (automatic)
# Outputs: data_output/raw/scrapy_amazon_[timestamp].json
# Outputs: data_output/raw/scrapy_amazon_[timestamp].csv

# Manual database queries
sqlite3 data/price_monitor.db "SELECT * FROM price_history WHERE price > 100;"
```

### Generated Reports

The system generates automated reports in the `data_output/reports/` directory:

- **Statistics Reports**: Overall system statistics
- **Price Analysis**: Detailed price breakdowns
- **Trend Reports**: Time-based analysis
- **Comparison Reports**: Cross-platform comparisons

## Troubleshooting

### Common Issues

#### 1. "No active URLs found in the database"

**Solution:**
```bash
python setup_sample_data.py
```

This populates the database with sample URLs for testing.

#### 2. "ChromeDriver not found"

**Solution:**
Install ChromeDriver for your system:

**Ubuntu/Debian:**
```bash
sudo apt-get install chromium-chromedriver
```

**macOS:**
```bash
brew install chromedriver
```

**Windows:**
Download from https://chromedriver.chromium.org/

#### 3. "Module import errors"

**Solution:**
Ensure Python path is set correctly:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

Or run from project root directory.

#### 4. "Database is locked"

**Solution:**
Close any existing database connections:
```bash
# Kill any Python processes using the database
pkill -f python

# Or restart the application
```

#### 5. "Request failed with 429 (Too Many Requests)"

**Solution:**
The site is rate-limiting. Increase delays in config:
```yaml
sites:
  amazon:
    rate_limit: 5.0  # Increase from 2.0 to 5.0 seconds
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
python -m src.cli.interface --log-level DEBUG scrape run --site amazon
```

Check logs in:
- `logs/price_monitor.log` - Main application log
- `logs/price_monitor_json.log` - Structured JSON logs
- `logs/scrapy.log` - Scrapy-specific logs

### Performance Issues

#### Slow Scraping

1. **Reduce concurrent workers:**
   ```yaml
   scraping:
     concurrent_workers: 1
   ```

2. **Increase delays:**
   ```yaml
   scraping:
     default_delay: 5.0
   ```

3. **Use headless mode:**
   ```yaml
   selenium:
     headless: true
   ```

#### Memory Issues

1. **Reduce worker count:**
   ```yaml
   scraping:
     concurrent_workers: 1
   ```

2. **Set memory limits:**
   ```yaml
   performance:
     memory_limit: 256  # MB
   ```

### Getting Help

1. **Check logs** for error details
2. **Run test script** to verify system health:
   ```bash
   python test_implementation.py
   ```
3. **Review configuration** files for correct settings
4. **Check database** status:
   ```bash
   sqlite3 data/price_monitor.db "SELECT COUNT(*) FROM products;"
   ```

### Advanced Troubleshooting

#### Database Issues

```bash
# Check database schema
sqlite3 data/price_monitor.db ".schema"

# Check data integrity
sqlite3 data/price_monitor.db "PRAGMA integrity_check;"

# Backup database
cp data/price_monitor.db data/price_monitor_backup.db
```

#### Network Issues

```bash
# Test connectivity
curl -I https://www.amazon.com
curl -I https://www.ebay.com

# Check proxy settings (if applicable)
env | grep -i proxy
```

#### Configuration Validation

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"
python -c "import yaml; yaml.safe_load(open('config/scrapers.yaml'))"
```

## Tips for Best Results

1. **Start small** - Test with a few URLs before scaling up
2. **Monitor logs** - Watch for rate limiting or blocking
3. **Respect websites** - Use appropriate delays
4. **Regular maintenance** - Clean old data periodically
5. **Backup data** - Save important price history
6. **Test changes** - Run tests after configuration changes

---

For more detailed technical information, see the [Architecture Design](ARCHITECTURE_DESIGN.md) document.
