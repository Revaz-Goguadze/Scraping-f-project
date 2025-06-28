"""
Centralized logging system for the E-Commerce Price Monitoring System.
Implements comprehensive logging with session correlation and rotation.
"""

import os
import logging
import logging.handlers
from typing import Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime
import threading

from .config import config_manager


class SessionContextFilter(logging.Filter):
    """
    Custom logging filter to add session context to log records.
    Adds session_id and other contextual information to log messages.
    """
    
    def __init__(self):
        super().__init__()
        self.local = threading.local()
    
    def set_session_id(self, session_id: str):
        """Set session ID for current thread."""
        self.local.session_id = session_id
    
    def get_session_id(self) -> str:
        """Get session ID for current thread."""
        return getattr(self.local, 'session_id', 'NO_SESSION')
    
    def filter(self, record):
        """Add session context to log record."""
        record.session_id = self.get_session_id()
        return True


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Converts log records to JSON format for easier parsing and analysis.
    """
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'session_id': getattr(record, 'session_id', 'NO_SESSION'),
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry['extra'] = record.extra_data
        
        return json.dumps(log_entry, ensure_ascii=False)


class LoggerManager:
    """
    Centralized logger manager implementing Singleton pattern.
    Manages all logging configuration and provides logger instances.
    """
    
    _instance: Optional['LoggerManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'LoggerManager':
        """Implement Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger manager (only once due to Singleton pattern)."""
        if not self._initialized:
            self.session_filter = SessionContextFilter()
            self.loggers: Dict[str, logging.Logger] = {}
            self.handlers: Dict[str, logging.Handler] = {}
            self._initialized = True
            self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration based on settings."""
        try:
            # Load configuration
            config_manager.load_config()
            log_config = config_manager.get_log_config()
            
            # Set root logger level
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, log_config['level']))
            
            # Clear existing handlers
            root_logger.handlers.clear()
            
            # Create formatters
            console_format = log_config.get('format', 
                '[%(asctime)s] [%(levelname)s] [%(name)s] [%(session_id)s] - %(message)s')
            console_formatter = logging.Formatter(console_format)
            json_formatter = JsonFormatter()
            
            # Console handler
            if log_config.get('console_output', True):
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(console_formatter)
                console_handler.addFilter(self.session_filter)
                root_logger.addHandler(console_handler)
                self.handlers['console'] = console_handler
            
            # File handler with rotation
            log_file_path = log_config['file_path']
            log_dir = Path(log_file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Parse max file size
            max_size = self._parse_file_size(log_config.get('max_file_size', '10MB'))
            backup_count = log_config.get('backup_count', 5)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(console_formatter)
            file_handler.addFilter(self.session_filter)
            root_logger.addHandler(file_handler)
            self.handlers['file'] = file_handler
            
            # JSON log handler for structured logging
            json_log_path = log_file_path.replace('.log', '_json.log')
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_path,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            json_handler.setFormatter(json_formatter)
            json_handler.addFilter(self.session_filter)
            root_logger.addHandler(json_handler)
            self.handlers['json'] = json_handler
            
            # Log the initialization
            logger = self.get_logger('LoggerManager')
            logger.info("Logging system initialized successfully")
            
        except Exception as e:
            # Fallback to basic logging if configuration fails
            logging.basicConfig(
                level=logging.INFO,
                format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s'
            )
            logger = logging.getLogger('LoggerManager')
            logger.error(f"Failed to setup logging configuration: {e}")
            logger.info("Using fallback logging configuration")
    
    def _parse_file_size(self, size_str: str) -> int:
        """Parse file size string (e.g., '10MB') to bytes."""
        size_str = size_str.upper().strip()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # Assume bytes
            return int(size_str)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance for the specified name.
        
        Args:
            name: Logger name (usually module name)
            
        Returns:
            Logger instance
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            # Add session filter to the logger
            logger.addFilter(self.session_filter)
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def set_session_id(self, session_id: str):
        """Set session ID for current thread's logging context."""
        self.session_filter.set_session_id(session_id)
    
    def get_session_id(self) -> str:
        """Get current session ID."""
        return self.session_filter.get_session_id()
    
    def log_with_extra(self, logger_name: str, level: str, message: str, 
                      extra_data: Dict[str, Any] = None):
        """
        Log message with extra structured data.
        
        Args:
            logger_name: Name of the logger
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            extra_data: Additional structured data
        """
        logger = self.get_logger(logger_name)
        log_level = getattr(logging, level.upper())
        
        # Create log record with extra data
        if extra_data:
            record = logger.makeRecord(
                logger.name, log_level, '', 0, message, (), None
            )
            record.extra_data = extra_data
            logger.handle(record)
        else:
            logger.log(log_level, message)
    
    def log_scraping_start(self, session_id: str, site: str, product_count: int):
        """Log the start of a scraping session."""
        self.set_session_id(session_id)
        logger = self.get_logger('ScrapingSession')
        self.log_with_extra(
            'ScrapingSession', 'INFO',
            f"Starting scraping session for {site}",
            {
                'action': 'scraping_start',
                'site': site,
                'product_count': product_count,
                'session_id': session_id
            }
        )
    
    def log_scraping_success(self, url: str, price: float = None, 
                           response_time: float = None):
        """Log successful scraping operation."""
        logger = self.get_logger('ScrapingScraper')
        self.log_with_extra(
            'ScrapingScraper', 'INFO',
            f"Successfully scraped product from {url}",
            {
                'action': 'scraping_success',
                'url': url,
                'price': price,
                'response_time_ms': response_time * 1000 if response_time else None
            }
        )
    
    def log_scraping_error(self, url: str, error_type: str, error_message: str,
                          retry_count: int = 0):
        """Log scraping error with context."""
        logger = self.get_logger('ScrapingScraper')
        self.log_with_extra(
            'ScrapingScraper', 'ERROR',
            f"Scraping failed for {url}: {error_message}",
            {
                'action': 'scraping_error',
                'url': url,
                'error_type': error_type,
                'error_message': error_message,
                'retry_count': retry_count
            }
        )
    
    def log_price_change(self, product_id: int, old_price: float, 
                        new_price: float, change_percent: float):
        """Log significant price changes."""
        logger = self.get_logger('PriceMonitor')
        self.log_with_extra(
            'PriceMonitor', 'WARNING',
            f"Price change detected for product {product_id}: "
            f"{old_price} -> {new_price} ({change_percent:+.2f}%)",
            {
                'action': 'price_change',
                'product_id': product_id,
                'old_price': old_price,
                'new_price': new_price,
                'change_percent': change_percent
            }
        )
    
    def log_performance_metric(self, metric_name: str, value: float, 
                             unit: str = None):
        """Log performance metrics."""
        logger = self.get_logger('Performance')
        self.log_with_extra(
            'Performance', 'INFO',
            f"Performance metric: {metric_name} = {value} {unit or ''}",
            {
                'action': 'performance_metric',
                'metric_name': metric_name,
                'value': value,
                'unit': unit
            }
        )
    
    def log_database_operation(self, operation: str, table: str, 
                              record_count: int = None, duration: float = None):
        """Log database operations."""
        logger = self.get_logger('Database')
        message = f"Database {operation} on {table}"
        if record_count is not None:
            message += f" ({record_count} records)"
        if duration is not None:
            message += f" took {duration:.3f}s"
        
        self.log_with_extra(
            'Database', 'DEBUG',
            message,
            {
                'action': 'database_operation',
                'operation': operation,
                'table': table,
                'record_count': record_count,
                'duration_ms': duration * 1000 if duration else None
            }
        )
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics and health information."""
        stats = {
            'handlers_count': len(self.handlers),
            'loggers_count': len(self.loggers),
            'current_session': self.get_session_id(),
            'handlers': list(self.handlers.keys())
        }
        
        # Add file handler statistics if available
        if 'file' in self.handlers:
            file_handler = self.handlers['file']
            if hasattr(file_handler, 'stream') and hasattr(file_handler.stream, 'name'):
                log_file = Path(file_handler.stream.name)
                if log_file.exists():
                    stats['log_file_size'] = log_file.stat().st_size
                    stats['log_file_path'] = str(log_file)
        
        return stats


# Global logger manager instance (Singleton)
logger_manager = LoggerManager()

# Convenience function for getting loggers
def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger instance."""
    return logger_manager.get_logger(name)