"""
Report generation module for the E-Commerce Price Monitoring System.
Generates reports in various formats (HTML, CSV, JSON) with visualizations.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any, List
from pathlib import Path
import json

from .statistics import StatisticsAnalyzer
from .trends import TrendAnalyzer
from ..cli.utils.config import config_manager
from ..cli.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """
    Generates comprehensive reports from analyzed price data.
    Supports HTML, CSV, and JSON formats.
    """

    def __init__(self):
        """Initialize the report generator."""
        self.stats_analyzer = StatisticsAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        
        # Configure report output directory
        self.report_dir = Path(config_manager.get_setting('reporting.report_directory', 'data_output/reports'))
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure Jinja2 for HTML templates
        self.template_env = Environment(loader=FileSystemLoader(searchpath="./templates/"))
        logger.info(f"ReportGenerator initialized. Reports will be saved to {self.report_dir}")

    def generate_product_report(self, product_id: int, formats: List[str] = None):
        """
        Generate a full report for a single product.

        Args:
            product_id: The ID of the product.
            formats: List of formats to generate (e.g., ['html', 'json']).
        """
        if formats is None:
            formats = ['html', 'json', 'csv']

        # Get data
        stats = self.stats_analyzer.get_price_statistics_for_product(product_id)
        price_history = self.trend_analyzer.get_price_history_dataframe(product_id)
        trend = self.trend_analyzer.analyze_price_trend(product_id)
        
        if not stats:
            logger.error(f"Cannot generate report: No data for product ID {product_id}")
            return

        report_data = {
            'stats': stats,
            'trend': trend
        }
        
        # Generate plot for HTML report
        plot_path = None
        if 'html' in formats and price_history is not None:
            plot_path = self._generate_price_history_plot(price_history, product_id)

        # Generate reports in specified formats
        for fmt in formats:
            try:
                if fmt == 'html':
                    self._generate_html_report(report_data, plot_path, product_id)
                elif fmt == 'json':
                    self._generate_json_report(report_data, product_id)
                elif fmt == 'csv':
                    if price_history is not None:
                        self._generate_csv_report(price_history, product_id)
                else:
                    logger.warning(f"Unsupported report format: {fmt}")
            except Exception as e:
                logger.error(f"Failed to generate {fmt} report for product {product_id}: {e}")

    def _generate_price_history_plot(self, df: pd.DataFrame, product_id: int) -> str:
        """Generate and save a price history plot."""
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12, 6))

        for site in df['site'].unique():
            site_df = df[df['site'] == site]
            ax.plot(site_df.index, site_df['price'], marker='o', linestyle='-', label=site)

        ax.set_title(f'Price History for Product ID: {product_id}')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price (USD)')
        ax.legend()
        ax.grid(True)
        
        plot_path = self.report_dir / f"product_{product_id}_price_history.png"
        plt.savefig(plot_path)
        plt.close(fig)
        
        logger.info(f"Generated plot: {plot_path}")
        return str(plot_path)

    def _generate_html_report(self, data: Dict[str, Any], plot_path: str, product_id: int):
        """Generate HTML report from template."""
        try:
            template = self.template_env.get_template('product_report.html')
        except:
            logger.error("HTML template 'product_report.html' not found. Creating a basic one.")
            self._create_basic_html_template()
            template = self.template_env.get_template('product_report.html')
            
        html_content = template.render(
            product_id=product_id,
            product_name=data['stats']['product_name'],
            data=data,
            plot_path=os.path.basename(plot_path) if plot_path else None
        )
        
        report_path = self.report_dir / f"product_{product_id}_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logger.info(f"Generated HTML report: {report_path}")

    def _generate_json_report(self, data: Dict[str, Any], product_id: int):
        """Generate JSON report."""
        report_path = self.report_dir / f"product_{product_id}_report.json"
        
        # Convert non-serializable types
        def default_converter(o):
            if isinstance(o, (pd.Timestamp, np.generic)):
                return str(o)
            raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=default_converter)
            
        logger.info(f"Generated JSON report: {report_path}")

    def _generate_csv_report(self, df: pd.DataFrame, product_id: int):
        """Generate CSV report of price history."""
        report_path = self.report_dir / f"product_{product_id}_price_history.csv"
        df.to_csv(report_path)
        logger.info(f"Generated CSV report: {report_path}")

    def _create_basic_html_template(self):
        """Create a fallback HTML template if one doesn't exist."""
        template_dir = Path("./templates")
        template_dir.mkdir(exist_ok=True)
        template_path = template_dir / "product_report.html"
        
        if not template_path.exists():
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Product Report: {{ product_name }}</title>
                <style>
                    body { font-family: sans-serif; }
                    .container { max-width: 800px; margin: auto; padding: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Product Report for {{ product_name }} (ID: {{ product_id }})</h1>
                    <h2>Price Statistics</h2>
                    <pre>{{ data.stats | tojson(indent=4) }}</pre>
                    <h2>Price Trend</h2>
                    <pre>{{ data.trend | tojson(indent=4) }}</pre>
                    {% if plot_path %}
                        <h2>Price History</h2>
                        <img src="{{ plot_path }}" alt="Price History Plot" style="max-width: 100%;">
                    {% endif %}
                </div>
            </body>
            </html>
            """
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Created basic HTML template at {template_path}")
