"""
Configuration management system implementing Singleton pattern.
Handles loading and accessing settings from YAML configuration files.
"""

import os
import yaml
import logging
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Singleton configuration manager for centralized settings management.
    Loads and manages settings from YAML files with validation and caching.
    """
    
    _instance: Optional['ConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'ConfigManager':
        """Implement Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration manager (only once due to Singleton pattern)."""
        if not self._initialized:
            self.settings: Dict[str, Any] = {}
            self.scrapers_config: Dict[str, Any] = {}
            self.config_paths = {
                'settings': 'config/settings.yaml',
                'scrapers': 'config/scrapers.yaml'
            }
            self._initialized = True
            logger.info("ConfigManager initialized")
    
    def load_config(self, force_reload: bool = False) -> None:
        """
        Load configuration from YAML files.
        
        Args:
            force_reload: Force reload even if already loaded
        """
        if self.settings and self.scrapers_config and not force_reload:
            return
        
        try:
            # Load main settings
            settings_path = Path(self.config_paths['settings'])
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    self.settings = yaml.safe_load(f) or {}
                logger.info(f"Loaded settings from {settings_path}")
            else:
                logger.warning(f"Settings file not found: {settings_path}")
                self.settings = self._get_default_settings()
            
            # Load scrapers configuration
            scrapers_path = Path(self.config_paths['scrapers'])
            if scrapers_path.exists():
                with open(scrapers_path, 'r', encoding='utf-8') as f:
                    self.scrapers_config = yaml.safe_load(f) or {}
                logger.info(f"Loaded scrapers config from {scrapers_path}")
            else:
                logger.warning(f"Scrapers config file not found: {scrapers_path}")
                self.scrapers_config = self._get_default_scrapers_config()
                
            self._validate_config()
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value using dot notation (e.g., 'database.type').
        
        Args:
            key: Setting key in dot notation
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        if not self.settings:
            self.load_config()
        
        keys = key.split('.')
        value = self.settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.debug(f"Setting not found: {key}, using default: {default}")
            return default
    
    def get_scraper_config(self, site_name: str) -> Dict[str, Any]:
        """
        Get scraper configuration for a specific site.
        
        Args:
            site_name: Name of the site (amazon, ebay, walmart)
            
        Returns:
            Scraper configuration dictionary
        """
        if not self.scrapers_config:
            self.load_config()
        
        sites = self.scrapers_config.get('sites', {})
        if site_name not in sites:
            logger.error(f"Scraper configuration not found for site: {site_name}")
            raise ValueError(f"Unknown site: {site_name}")
        
        return sites[site_name]
    
    def get_all_sites(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all sites."""
        if not self.scrapers_config:
            self.load_config()
        
        return self.scrapers_config.get('sites', {})
    
    def get_product_categories(self) -> Dict[str, Any]:
        """Get product categories configuration."""
        if not self.scrapers_config:
            self.load_config()
        
        return self.scrapers_config.get('product_categories', {})
    
    def get_sample_products(self) -> Dict[str, Any]:
        """Get sample product URLs for testing."""
        if not self.scrapers_config:
            self.load_config()
        
        return self.scrapers_config.get('sample_products', {})
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get data validation rules."""
        if not self.scrapers_config:
            self.load_config()
        
        return self.scrapers_config.get('validation', {})
    
    def get_error_handling_config(self) -> Dict[str, Any]:
        """Get error handling configuration."""
        if not self.scrapers_config:
            self.load_config()
        
        return self.scrapers_config.get('error_handling', {})
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a setting value (runtime only, not saved to file).
        
        Args:
            key: Setting key in dot notation
            value: Value to set
        """
        if not self.settings:
            self.load_config()
        
        keys = key.split('.')
        current = self.settings
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the final key
        current[keys[-1]] = value
        logger.debug(f"Setting updated: {key} = {value}")
    
    def reload_config(self) -> None:
        """Reload configuration from files."""
        logger.info("Reloading configuration files")
        self.load_config(force_reload=True)
    
    def _validate_config(self) -> None:
        """Validate loaded configuration for required fields and correct types."""
        # Validate database configuration
        db_config = self.settings.get('database', {})
        if not db_config.get('type'):
            logger.warning("Database type not specified in configuration")
        
        # Validate scraping configuration
        scraping_config = self.settings.get('scraping', {})
        if scraping_config.get('concurrent_workers', 0) <= 0:
            logger.warning("Invalid concurrent_workers setting, using default: 3")
            self.set_setting('scraping.concurrent_workers', 3)
        
        # Validate sites configuration
        sites = self.scrapers_config.get('sites', {})
        required_sites = ['amazon', 'ebay', 'walmart']
        for site in required_sites:
            if site not in sites:
                logger.error(f"Required site configuration missing: {site}")
                raise ValueError(f"Missing configuration for required site: {site}")
            
            site_config = sites[site]
            if not site_config.get('base_url'):
                logger.error(f"Base URL not configured for site: {site}")
                raise ValueError(f"Missing base_url for site: {site}")
        
        logger.info("Configuration validation completed successfully")
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings if configuration file is missing."""
        return {
            'database': {
                'type': 'sqlite',
                'path': 'data/price_monitor.db',
                'connection_pool_size': 5
            },
            'scraping': {
                'concurrent_workers': 3,
                'default_delay': 2.0,
                'max_retries': 3,
                'timeout': 30
            },
            'logging': {
                'level': 'INFO',
                'file_path': 'logs/price_monitor.log',
                'console_output': True
            }
        }
    
    def _get_default_scrapers_config(self) -> Dict[str, Any]:
        """Get default scrapers configuration if file is missing."""
        return {
            'sites': {
                'amazon': {
                    'name': 'Amazon',
                    'base_url': 'https://www.amazon.com',
                    'scraper_type': 'static',
                    'rate_limit': 2.0
                },
                'ebay': {
                    'name': 'eBay',
                    'base_url': 'https://www.ebay.com',
                    'scraper_type': 'static',
                    'rate_limit': 1.5
                },
                'walmart': {
                    'name': 'Walmart',
                    'base_url': 'https://www.walmart.com',
                    'scraper_type': 'selenium',
                    'rate_limit': 2.5
                }
            }
        }
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        db_type = self.get_setting('database.type', 'sqlite')
        
        if db_type == 'sqlite':
            db_path = self.get_setting('database.path', 'data/price_monitor.db')
            # Ensure directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{db_path}"
        elif db_type == 'postgresql':
            host = self.get_setting('database.host', 'localhost')
            port = self.get_setting('database.port', 5432)
            name = self.get_setting('database.name', 'price_monitor')
            user = self.get_setting('database.user', 'postgres')
            password = self.get_setting('database.password', '')
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        log_config = {
            'level': self.get_setting('logging.level', 'INFO'),
            'file_path': self.get_setting('logging.file_path', 'logs/price_monitor.log'),
            'max_file_size': self.get_setting('logging.max_file_size', '10MB'),
            'backup_count': self.get_setting('logging.backup_count', 5),
            'console_output': self.get_setting('logging.console_output', True),
            'format': self.get_setting('logging.format', 
                '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s')
        }
        
        # Ensure log directory exists
        log_path = Path(log_config['file_path'])
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        return log_config


# Global configuration manager instance (Singleton)
config_manager = ConfigManager()