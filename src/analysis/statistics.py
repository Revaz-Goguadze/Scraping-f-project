"""
Statistical analysis module for the E-Commerce Price Monitoring System.
Performs statistical calculations on scraped data using pandas and numpy.
"""

import pandas as pd
import numpy as np
from sqlalchemy import func, case
from typing import Dict, Any, List, Optional

from ..data.database import db_manager
from ..data.models import Product, PriceHistory, ProductURL, Site
from ..cli.utils.logger import get_logger

logger = get_logger(__name__)


class StatisticsAnalyzer:
    """
    Performs statistical analysis on the price data stored in the database.
    Uses pandas for data manipulation and analysis.
    """

    def __init__(self):
        """Initialize the statistics analyzer."""
        logger.info("StatisticsAnalyzer initialized.")

    def get_price_statistics_for_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Calculate price statistics for a single product across all sites.

        Args:
            product_id: The ID of the product to analyze.

        Returns:
            A dictionary with price statistics, or None if no data.
        """
        with db_manager.get_session() as session:
            # Get product details
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"Product with ID {product_id} not found.")
                return None

            # Query to get price history for the product across all its URLs
            query = session.query(
                PriceHistory.price,
                PriceHistory.scraped_at,
                Site.name.label('site_name')
            ).join(ProductURL, PriceHistory.product_url_id == ProductURL.id)\
             .join(Site, ProductURL.site_id == Site.id)\
             .filter(ProductURL.product_id == product_id)\
             .filter(PriceHistory.price.isnot(None))

            df = pd.read_sql(query.statement, query.session.bind)

            if df.empty:
                logger.info(f"No price history found for product ID {product_id}.")
                return None

            # Calculate statistics
            stats = {
                'product_id': product_id,
                'product_name': product.name,
                'total_data_points': len(df),
                'mean_price': df['price'].mean(),
                'median_price': df['price'].median(),
                'min_price': df['price'].min(),
                'max_price': df['price'].max(),
                'std_dev_price': df['price'].std(),
                'last_price': df.sort_values('scraped_at', ascending=False)['price'].iloc[0],
                'price_range': df['price'].max() - df['price'].min(),
                'stats_by_site': df.groupby('site_name')['price'].agg(['mean', 'min', 'max', 'count']).to_dict('index')
            }

            return stats

    def get_overall_database_statistics(self) -> Dict[str, Any]:
        """
        Calculate overall statistics for the entire database.

        Returns:
            A dictionary with database-wide statistics.
        """
        with db_manager.get_session() as session:
            num_products = session.query(Product).count()
            num_sites = session.query(Site).count()
            num_price_records = session.query(PriceHistory).count()
            
            # Products per category
            products_per_category = session.query(
                Product.category,
                func.count(Product.id)
            ).group_by(Product.category).all()
            
            # Prices per site
            prices_per_site = session.query(
                Site.name,
                func.count(PriceHistory.id)
            ).join(ProductURL, Site.id == ProductURL.site_id)\
             .join(PriceHistory, ProductURL.id == PriceHistory.product_url_id)\
             .group_by(Site.name).all()

            stats = {
                'total_products': num_products,
                'total_sites': num_sites,
                'total_price_records': num_price_records,
                'products_per_category': dict(products_per_category),
                'price_records_per_site': dict(prices_per_site)
            }
            
            return stats

    def get_price_volatility(self, top_n: int = 10) -> Optional[pd.DataFrame]:
        """
        Identify products with the most volatile prices.
        Volatility is measured by the coefficient of variation (std_dev / mean).

        Args:
            top_n: The number of most volatile products to return.

        Returns:
            A pandas DataFrame with the most volatile products, or None.
        """
        with db_manager.get_session() as session:
            # Query to get price data for each product (SQLite compatible)
            query = session.query(
                Product.id.label('product_id'),
                Product.name.label('product_name'),
                PriceHistory.price,
                func.count(PriceHistory.id).over(partition_by=Product.id).label('data_points')
            ).join(ProductURL, Product.id == ProductURL.product_id)\
             .join(PriceHistory, ProductURL.id == PriceHistory.product_url_id)

            df = pd.read_sql(query.statement, query.session.bind)

            if df.empty:
                return None

            # Filter for products with enough data points
            df = df[df['data_points'] > 5]
            
            if df.empty:
                return None

            # Calculate statistics using pandas (which has better statistical functions)
            volatility_stats = df.groupby(['product_id', 'product_name']).agg({
                'price': ['mean', 'std', 'count']
            }).reset_index()
            
            # Flatten column names
            volatility_stats.columns = ['product_id', 'product_name', 'mean_price', 'std_dev_price', 'data_points']
            
            # Calculate coefficient of variation
            volatility_stats['volatility_coeff'] = volatility_stats['std_dev_price'] / volatility_stats['mean_price']
            
            # Remove invalid entries (where std_dev is 0 or mean is 0)
            volatility_stats = volatility_stats[
                (volatility_stats['std_dev_price'] > 0) & 
                (volatility_stats['mean_price'] > 0) &
                (volatility_stats['volatility_coeff'].notna())
            ]
            
            # Sort by volatility and return top N
            most_volatile = volatility_stats.sort_values('volatility_coeff', ascending=False).head(top_n)
            
            return most_volatile

    def get_best_deals(self, category: Optional[str] = None, top_n: int = 10) -> Optional[pd.DataFrame]:
        """
        Find products that are currently priced significantly below their average.

        Args:
            category: The product category to search within.
            top_n: The number of best deals to return.

        Returns:
            A pandas DataFrame with the best deals, or None.
        """
        with db_manager.get_session() as session:
            # Subquery to get the latest price for each product URL
            latest_price_subq = session.query(
                PriceHistory.product_url_id,
                func.max(PriceHistory.scraped_at).label('latest_scrape')
            ).group_by(PriceHistory.product_url_id).subquery()

            # Query to get product details, average price, and latest price
            query = session.query(
                Product.id.label('product_id'),
                Product.name.label('product_name'),
                Site.name.label('site_name'),
                func.avg(PriceHistory.price).label('avg_price'),
                # Correlated subquery to get the latest price
                (
                    session.query(PriceHistory.price)
                           .filter(PriceHistory.product_url_id == ProductURL.id)
                           .filter(PriceHistory.scraped_at == latest_price_subq.c.latest_scrape)
                           .scalar_subquery()
                ).label('latest_price')
            ).join(ProductURL, Product.id == ProductURL.product_id)\
             .join(PriceHistory, ProductURL.id == PriceHistory.product_url_id)\
             .join(Site, ProductURL.site_id == Site.id)\
             .group_by(Product.id, Product.name, Site.name)
            
            if category:
                query = query.filter(Product.category == category)
            
            df = pd.read_sql(query.statement, query.session.bind)

            if df.empty or 'latest_price' not in df.columns or df['latest_price'].isnull().all():
                return None

            # Calculate price difference
            df['price_diff_percent'] = ((df['latest_price'] - df['avg_price']) / df['avg_price']) * 100
            
            # Filter for deals (latest price is lower than average)
            deals = df[df['price_diff_percent'] < 0].copy()
            deals.sort_values('price_diff_percent', ascending=True, inplace=True)
            
            return deals.head(top_n)
