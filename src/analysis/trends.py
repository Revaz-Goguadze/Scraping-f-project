"""
Time-based trend analysis for the E-Commerce Price Monitoring System.
Analyzes price history to identify trends, moving averages, and significant changes.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any

from ..data.database import db_manager
from ..data.models import Product, PriceHistory, ProductURL, Site
from ..cli.utils.logger import get_logger

logger = get_logger(__name__)


class TrendAnalyzer:
    """
    Performs time-based trend analysis on price data.
    """

    def __init__(self):
        """Initialize the trend analyzer."""
        logger.info("TrendAnalyzer initialized.")

    def get_price_history_dataframe(self, product_id: int, site_name: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Retrieve the price history for a product as a pandas DataFrame.

        Args:
            product_id: The ID of the product.
            site_name: Optional site name to filter results.

        Returns:
            A DataFrame with price history, or None if no data.
        """
        with db_manager.get_session() as session:
            query = session.query(
                PriceHistory.scraped_at,
                PriceHistory.price,
                Site.name.label('site')
            ).join(ProductURL, PriceHistory.product_url_id == ProductURL.id)\
             .join(Product, ProductURL.product_id == Product.id)\
             .join(Site, ProductURL.site_id == Site.id)\
             .filter(Product.id == product_id)\
             .filter(PriceHistory.price.isnot(None))\
             .order_by(PriceHistory.scraped_at)

            if site_name:
                query = query.filter(Site.name == site_name)

            df = pd.read_sql(query.statement, query.session.bind)

            if df.empty:
                return None

            df['scraped_at'] = pd.to_datetime(df['scraped_at'])
            df.set_index('scraped_at', inplace=True)
            
            return df

    def calculate_moving_average(self, product_id: int, window: int = 7) -> Optional[pd.Series]:
        """
        Calculate the moving average for a product's price.

        Args:
            product_id: The ID of the product.
            window: The rolling window size in days.

        Returns:
            A pandas Series with the moving average, or None.
        """
        df = self.get_price_history_dataframe(product_id)
        if df is None:
            return None

        # Resample to daily frequency, taking the mean for days with multiple scrapes
        daily_prices = df['price'].resample('D').mean().ffill()
        
        # Calculate rolling average
        moving_avg = daily_prices.rolling(window=f'{window}D').mean()
        
        return moving_avg

    def analyze_price_trend(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Analyze the price trend for a product using linear regression.

        Args:
            product_id: The ID of the product.

        Returns:
            A dictionary with trend analysis results, or None.
        """
        df = self.get_price_history_dataframe(product_id)
        if df is None or len(df) < 2:
            return None

        # Convert timestamps to numeric values for regression
        df['time_ordinal'] = df.index.map(pd.Timestamp.toordinal)
        
        # Perform linear regression
        X = df['time_ordinal'].values
        y = df['price'].values
        
        # Add a constant for the intercept
        A = np.vstack([X, np.ones(len(X))]).T
        
        # Solve for slope and intercept
        slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
        
        trend_direction = "stable"
        if slope > 0.01:  # Threshold to avoid noise
            trend_direction = "increasing"
        elif slope < -0.01:
            trend_direction = "decreasing"

        return {
            'product_id': product_id,
            'trend_direction': trend_direction,
            'slope': slope,  # Price change per day
            'intercept': intercept,
            'start_date': df.index.min(),
            'end_date': df.index.max(),
            'data_points': len(df)
        }

    def detect_significant_price_changes(self, product_id: int, period_days: int = 30, threshold: float = 0.10) -> List[Dict[str, Any]]:
        """
        Detect significant price drops or increases over a period.

        Args:
            product_id: The ID of the product.
            period_days: The time window in days to look for changes.
            threshold: The percentage change to be considered significant (e.g., 0.10 for 10%).

        Returns:
            A list of dictionaries, each representing a significant price change.
        """
        df = self.get_price_history_dataframe(product_id)
        if df is None:
            return []
        
        # Resample to daily prices
        daily_prices = df['price'].resample('D').mean().ffill()
        
        # Calculate percentage change over the period
        price_changes = daily_prices.pct_change(periods=period_days)
        
        significant_changes = []
        for date, change in price_changes.dropna().items():
            if abs(change) >= threshold:
                change_type = "drop" if change < 0 else "increase"
                significant_changes.append({
                    'date': date,
                    'change_percent': change * 100,
                    'change_type': change_type,
                    'price_before': daily_prices.loc[date - pd.Timedelta(days=period_days)],
                    'price_after': daily_prices.loc[date]
                })
                
        return significant_changes
