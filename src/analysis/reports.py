"""
Report generation module for the E-Commerce Price Monitoring System.
Generates HTML reports with charts, tables, and data visualizations.
Implements the HTML report requirement from Project.md.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from jinja2 import Template
import base64
from io import BytesIO

from ..data.database import db_manager
from ..data.models import Product, Site, ProductURL, PriceHistory
from ..cli.utils.logger import get_logger
from .statistics import StatisticsAnalyzer

logger = get_logger(__name__)


class ReportGenerator:
    """
    Generates comprehensive HTML reports with charts and visualizations.
    Implements data visualization using matplotlib/seaborn (Project.md requirement).
    """
    
    def __init__(self):
        """Initialize report generator."""
        self.output_dir = "data_output/reports"
        self.template_dir = "templates"
        self.stats_analyzer = StatisticsAnalyzer()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        logger.info("ReportGenerator initialized")
    
    def generate_html_report(self, report_type: str = "comprehensive") -> str:
        """
        Generate comprehensive HTML report with charts and tables.
        
        Args:
            report_type: Type of report ('comprehensive', 'summary', 'trends')
            
        Returns:
            str: Path to generated HTML file
        """
        logger.info(f"Generating {report_type} HTML report")
        
        # Collect data for report
        report_data = self._collect_report_data()
        
        # Generate visualizations
        charts = self._generate_charts(report_data)
        
        # Generate HTML content
        html_content = self._generate_html_content(report_data, charts, report_type)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_report_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {filepath}")
        return filepath
    
    def _collect_report_data(self) -> Dict[str, Any]:
        """Collect all data needed for the report."""
        with db_manager.get_session() as session:
            # Overall statistics
            overall_stats = self.stats_analyzer.get_overall_database_statistics()
            
            # Price data for charts
            price_query = session.query(
                PriceHistory.price,
                PriceHistory.scraped_at,
                Product.name.label('product_name'),
                Site.name.label('site_name')
            ).join(ProductURL, PriceHistory.product_url_id == ProductURL.id)\
             .join(Product, ProductURL.product_id == Product.id)\
             .join(Site, ProductURL.site_id == Site.id)\
             .filter(PriceHistory.price.isnot(None))\
             .order_by(PriceHistory.scraped_at.desc())
            
            price_df = pd.read_sql(price_query.statement, session.bind)
            
            # Product statistics
            product_stats = []
            products = session.query(Product).limit(10).all()
            for product in products:
                stats = self.stats_analyzer.get_price_statistics_for_product(product.id)
                if stats:
                    product_stats.append(stats)
            
            # Recent price records with proper joins
            recent_prices_query = session.query(
                PriceHistory.id,
                PriceHistory.price,
                PriceHistory.availability,
                PriceHistory.scraped_at,
                Product.name.label('product_name'),
                Site.name.label('site_name')
            ).join(ProductURL, PriceHistory.product_url_id == ProductURL.id)\
             .join(Product, ProductURL.product_id == Product.id)\
             .join(Site, ProductURL.site_id == Site.id)\
             .order_by(PriceHistory.scraped_at.desc())\
             .limit(20)
            
            recent_prices_data = recent_prices_query.all()
            
            # Convert to list of dictionaries for template
            recent_prices = []
            for row in recent_prices_data:
                recent_prices.append({
                    'price': row.price,
                    'availability': row.availability,
                    'scraped_at': row.scraped_at,
                    'product_name': row.product_name,
                    'site_name': row.site_name
                })
            
            # Site performance
            site_stats = {}
            for site_name, count in overall_stats.get('price_records_per_site', {}).items():
                site_stats[site_name] = {
                    'total_records': count,
                    'avg_response_time': self._calculate_site_avg_response_time(site_name)
                }
        
        return {
            'overall_stats': overall_stats,
            'price_df': price_df,
            'product_stats': product_stats,
            'recent_prices': recent_prices,
            'site_stats': site_stats,
            'generation_time': datetime.now()
        }
    
    def _generate_charts(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all charts and return as base64 encoded images."""
        charts = {}
        
        if not report_data['price_df'].empty:
            # Price trend chart
            charts['price_trends'] = self._create_price_trend_chart(report_data['price_df'])
            
            # Price distribution chart
            charts['price_distribution'] = self._create_price_distribution_chart(report_data['price_df'])
            
            # Site comparison chart
            charts['site_comparison'] = self._create_site_comparison_chart(report_data['price_df'])
            
            # Product count by category
            charts['category_distribution'] = self._create_category_chart(report_data['overall_stats'])
        
        # Site performance chart
        if report_data['site_stats']:
            charts['site_performance'] = self._create_site_performance_chart(report_data['site_stats'])
        
        return charts
    
    def _create_price_trend_chart(self, price_df: pd.DataFrame) -> str:
        """Create price trend over time chart."""
        plt.figure(figsize=(12, 6))
        
        # Convert scraped_at to datetime
        price_df['scraped_at'] = pd.to_datetime(price_df['scraped_at'])
        
        # Group by site and plot trends
        for site in price_df['site_name'].unique():
            site_data = price_df[price_df['site_name'] == site]
            
            # Aggregate by date (average prices per day)
            daily_avg = site_data.groupby(site_data['scraped_at'].dt.date)['price'].mean()
            
            plt.plot(daily_avg.index, daily_avg.values, marker='o', label=site, linewidth=2)
        
        plt.title('Price Trends Over Time by Site', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Average Price ($)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        return self._fig_to_base64()
    
    def _create_price_distribution_chart(self, price_df: pd.DataFrame) -> str:
        """Create price distribution histogram."""
        plt.figure(figsize=(10, 6))
        
        # Create histogram
        plt.hist(price_df['price'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        
        # Add statistics lines
        mean_price = price_df['price'].mean()
        median_price = price_df['price'].median()
        
        plt.axvline(mean_price, color='red', linestyle='--', linewidth=2, label=f'Mean: ${mean_price:.2f}')
        plt.axvline(median_price, color='green', linestyle='--', linewidth=2, label=f'Median: ${median_price:.2f}')
        
        plt.title('Price Distribution', fontsize=16, fontweight='bold')
        plt.xlabel('Price ($)', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return self._fig_to_base64()
    
    def _create_site_comparison_chart(self, price_df: pd.DataFrame) -> str:
        """Create site comparison boxplot."""
        plt.figure(figsize=(10, 6))
        
        # Create boxplot
        sites = price_df['site_name'].unique()
        site_prices = [price_df[price_df['site_name'] == site]['price'] for site in sites]
        
        box_plot = plt.boxplot(site_prices, labels=sites, patch_artist=True)
        
        # Customize colors
        colors = sns.color_palette("husl", len(sites))
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        plt.title('Price Comparison by Site', fontsize=16, fontweight='bold')
        plt.xlabel('Site', fontsize=12)
        plt.ylabel('Price ($)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return self._fig_to_base64()
    
    def _create_category_chart(self, overall_stats: Dict[str, Any]) -> str:
        """Create product category distribution pie chart."""
        plt.figure(figsize=(8, 8))
        
        categories = overall_stats.get('products_per_category', {})
        if categories:
            labels = list(categories.keys())
            sizes = list(categories.values())
            colors = sns.color_palette("husl", len(labels))
            
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title('Product Distribution by Category', fontsize=16, fontweight='bold')
        else:
            plt.text(0.5, 0.5, 'No category data available', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=plt.gca().transAxes, fontsize=14)
            plt.title('Product Distribution by Category', fontsize=16, fontweight='bold')
        
        plt.axis('equal')
        plt.tight_layout()
        
        return self._fig_to_base64()
    
    def _create_site_performance_chart(self, site_stats: Dict[str, Any]) -> str:
        """Create site performance comparison chart."""
        plt.figure(figsize=(10, 6))
        
        sites = list(site_stats.keys())
        record_counts = [site_stats[site]['total_records'] for site in sites]
        
        bars = plt.bar(sites, record_counts, color=sns.color_palette("husl", len(sites)), alpha=0.8)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontweight='bold')
        
        plt.title('Total Price Records by Site', fontsize=16, fontweight='bold')
        plt.xlabel('Site', fontsize=12)
        plt.ylabel('Number of Records', fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        return self._fig_to_base64()
    
    def _fig_to_base64(self) -> str:
        """Convert current matplotlib figure to base64 string."""
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        return image_base64
    
    def _calculate_site_avg_response_time(self, site_name: str) -> float:
        """Calculate average response time for a site (placeholder)."""
        # This would require storing response times in the database
        # For now, return a simulated value
        return 2.5  # seconds
    
    def _generate_html_content(self, report_data: Dict[str, Any], charts: Dict[str, str], report_type: str) -> str:
        """Generate complete HTML content for the report."""
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Commerce Price Monitoring Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #007bff;
            margin: 0;
            font-size: 2.5em;
        }
        .header .subtitle {
            color: #666;
            font-size: 1.2em;
            margin-top: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            font-size: 2em;
        }
        .stat-card p {
            margin: 0;
            font-size: 1.1em;
        }
        .chart-section {
            margin: 30px 0;
        }
        .chart-section h2 {
            color: #007bff;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .table-container {
            overflow-x: auto;
            margin: 20px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #495057;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            color: #666;
        }
        .alert {
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            border: 1px solid transparent;
        }
        .alert-info {
            color: #0c5460;
            background-color: #d1ecf1;
            border-color: #bee5eb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛒 E-Commerce Price Monitoring Report</h1>
            <div class="subtitle">Generated on {{ generation_time.strftime('%B %d, %Y at %I:%M %p') }}</div>
        </div>

        <!-- Overall Statistics -->
        <div class="stats-grid">
            <div class="stat-card">
                <h3>{{ overall_stats.total_products }}</h3>
                <p>Total Products</p>
            </div>
            <div class="stat-card">
                <h3>{{ overall_stats.total_sites }}</h3>
                <p>Active Sites</p>
            </div>
            <div class="stat-card">
                <h3>{{ overall_stats.total_price_records }}</h3>
                <p>Price Records</p>
            </div>
            <div class="stat-card">
                <h3>${{ "{:.2f}".format(avg_price) if avg_price else "N/A" }}</h3>
                <p>Average Price</p>
            </div>
        </div>

        {% if charts %}
        <!-- Charts Section -->
        <div class="chart-section">
            <h2>📊 Data Visualizations</h2>
            
            {% if charts.price_trends %}
            <div class="chart-container">
                <h3>Price Trends Over Time</h3>
                <img src="data:image/png;base64,{{ charts.price_trends }}" alt="Price Trends Chart">
            </div>
            {% endif %}
            
            {% if charts.price_distribution %}
            <div class="chart-container">
                <h3>Price Distribution</h3>
                <img src="data:image/png;base64,{{ charts.price_distribution }}" alt="Price Distribution Chart">
            </div>
            {% endif %}
            
            {% if charts.site_comparison %}
            <div class="chart-container">
                <h3>Price Comparison by Site</h3>
                <img src="data:image/png;base64,{{ charts.site_comparison }}" alt="Site Comparison Chart">
            </div>
            {% endif %}
            
            {% if charts.category_distribution %}
            <div class="chart-container">
                <h3>Product Category Distribution</h3>
                <img src="data:image/png;base64,{{ charts.category_distribution }}" alt="Category Distribution Chart">
            </div>
            {% endif %}
            
            {% if charts.site_performance %}
            <div class="chart-container">
                <h3>Site Performance</h3>
                <img src="data:image/png;base64,{{ charts.site_performance }}" alt="Site Performance Chart">
            </div>
            {% endif %}
        </div>
        {% endif %}

        <!-- Product Statistics Table -->
        {% if product_stats %}
        <div class="chart-section">
            <h2>📈 Product Statistics</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Product Name</th>
                            <th>Data Points</th>
                            <th>Mean Price</th>
                            <th>Min Price</th>
                            <th>Max Price</th>
                            <th>Price Range</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for product in product_stats %}
                        <tr>
                            <td>{{ product.product_name[:50] }}{% if product.product_name|length > 50 %}...{% endif %}</td>
                            <td>{{ product.total_data_points }}</td>
                            <td>${{ "{:.2f}".format(product.mean_price) if product.mean_price else "N/A" }}</td>
                            <td>${{ "{:.2f}".format(product.min_price) if product.min_price else "N/A" }}</td>
                            <td>${{ "{:.2f}".format(product.max_price) if product.max_price else "N/A" }}</td>
                            <td>${{ "{:.2f}".format(product.price_range) if product.price_range else "N/A" }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endif %}

        <!-- Recent Price Updates -->
        {% if recent_prices %}
        <div class="chart-section">
            <h2>🕐 Recent Price Updates</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Site</th>
                            <th>Price</th>
                            <th>Availability</th>
                            <th>Scraped At</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for price in recent_prices[:10] %}
                        <tr>
                            <td>{{ price.product_name[:40] }}{% if price.product_name|length > 40 %}...{% endif %}</td>
                            <td>{{ price.site_name }}</td>
                            <td>${{ "{:.2f}".format(price.price) if price.price else "N/A" }}</td>
                            <td>{{ price.availability or "Unknown" }}</td>
                            <td>{{ price.scraped_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endif %}

        <!-- System Information -->
        <div class="alert alert-info">
            <h4>📋 Report Information</h4>
            <p><strong>Report Type:</strong> {{ report_type.title() }}</p>
            <p><strong>Data Coverage:</strong> {{ overall_stats.total_price_records }} price records from {{ overall_stats.total_sites }} sites</p>
            <p><strong>Products per Category:</strong> {{ overall_stats.products_per_category }}</p>
            <p><strong>Records per Site:</strong> {{ overall_stats.price_records_per_site }}</p>
        </div>

        <div class="footer">
            <p>Generated by E-Commerce Price Monitoring System</p>
            <p>Built with Python, SQLAlchemy, Matplotlib, and Seaborn</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Calculate average price for stats
        avg_price = None
        if not report_data['price_df'].empty:
            avg_price = report_data['price_df']['price'].mean()
        
        # Render template
        template = Template(html_template)
        html_content = template.render(
            generation_time=report_data['generation_time'],
            overall_stats=report_data['overall_stats'],
            product_stats=report_data['product_stats'],
            recent_prices=report_data['recent_prices'],
            charts=charts,
            report_type=report_type,
            avg_price=avg_price
        )
        
        return html_content
    
    def generate_csv_export(self, data_type: str = "price_history") -> str:
        """
        Export data to CSV format.
        
        Args:
            data_type: Type of data to export ('price_history', 'products', 'sites')
            
        Returns:
            str: Path to generated CSV file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{data_type}_export_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        with db_manager.get_session() as session:
            if data_type == "price_history":
                query = session.query(
                    PriceHistory.price,
                    PriceHistory.currency,
                    PriceHistory.availability,
                    PriceHistory.scraped_at,
                    Product.name.label('product_name'),
                    Product.brand,
                    Product.category,
                    Site.name.label('site_name')
                ).join(ProductURL, PriceHistory.product_url_id == ProductURL.id)\
                 .join(Product, ProductURL.product_id == Product.id)\
                 .join(Site, ProductURL.site_id == Site.id)
                
                df = pd.read_sql(query.statement, session.bind)
                
            elif data_type == "products":
                query = session.query(Product)
                df = pd.read_sql(query.statement, session.bind)
                
            elif data_type == "sites":
                query = session.query(Site)
                df = pd.read_sql(query.statement, session.bind)
            
            df.to_csv(filepath, index=False)
        
        logger.info(f"CSV export generated: {filepath}")
        return filepath
    
    def generate_json_export(self, data_type: str = "summary") -> str:
        """
        Export data to JSON format.
        
        Args:
            data_type: Type of data to export ('summary', 'full')
            
        Returns:
            str: Path to generated JSON file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{data_type}_export_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        if data_type == "summary":
            data = {
                'export_time': datetime.now().isoformat(),
                'statistics': self.stats_analyzer.get_overall_database_statistics(),
                'product_count': 0,
                'site_count': 0
            }
            
            with db_manager.get_session() as session:
                data['product_count'] = session.query(Product).count()
                data['site_count'] = session.query(Site).count()
        
        elif data_type == "full":
            # Full data export would be implemented here
            data = {"message": "Full export not implemented yet"}
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"JSON export generated: {filepath}")
        return filepath
