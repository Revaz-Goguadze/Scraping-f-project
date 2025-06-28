"""
Scrapy settings for the E-Commerce Price Monitoring System.
"""

# Scrapy settings for price_monitor project
BOT_NAME = 'price_monitor'

SPIDER_MODULES = ['src.scrapers.scrapy_crawler.spiders']
NEWSPIDER_MODULE = 'src.scrapers.scrapy_crawler.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure a delay for requests (required by Project.md for ethical scraping)
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# Reduce concurrent requests to be respectful
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Auto-throttling settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# HTTP cache settings for development
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 505, 500, 400, 403, 404]

# Configure pipelines
ITEM_PIPELINES = {
    'src.scrapers.scrapy_crawler.pipelines.ValidationPipeline': 300,
    'src.scrapers.scrapy_crawler.pipelines.DatabasePipeline': 400,
    'src.scrapers.scrapy_crawler.pipelines.StatisticsPipeline': 500,
}

# Configure middlewares
DOWNLOADER_MIDDLEWARES = {
    'src.scrapers.scrapy_crawler.middlewares.RotateUserAgentMiddleware': 400,
    'src.scrapers.scrapy_crawler.middlewares.ProxyMiddleware': 410,
}

# User agent rotation
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
]

# Default headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/scrapy.log'

# Extensions
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    'src.scrapers.scrapy_crawler.extensions.StatsExtension': 500,
}

# Feed exports for data output
FEEDS = {
    'data_output/raw/scrapy_%(name)s_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': None,
        'indent': 2,
    },
    'data_output/raw/scrapy_%(name)s_%(time)s.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
    },
}

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# Twisted reactor
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Cookies
COOKIES_ENABLED = True

# Compression
COMPRESSION_ENABLED = True

# Memory usage monitoring
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 512
MEMUSAGE_WARNING_MB = 400

# Stats collection
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'

# Telnet console (disable for security)
TELNETCONSOLE_ENABLED = False

# DNS timeout
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 60

# Media pipelines (for images if needed)
MEDIA_ALLOW_REDIRECTS = True

# Close spider on specific conditions
CLOSESPIDER_TIMEOUT = 3600  # 1 hour max
CLOSESPIDER_ITEMCOUNT = 1000  # Max items per spider run
CLOSESPIDER_PAGECOUNT = 100   # Max pages per spider run
CLOSESPIDER_ERRORCOUNT = 50   # Max errors before stopping