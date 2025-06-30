"""
CLI commands for running data analysis.
"""

import click
import pandas as pd
import os

from ...analysis.statistics import StatisticsAnalyzer
from ...analysis.trends import TrendAnalyzer
from ...cli.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def analyze():
    """Commands for analyzing scraped data."""
    pass


@analyze.command()
@click.argument('product_id', type=int)
def product(product_id: int):
    """Get price statistics for a specific product."""
    analyzer = StatisticsAnalyzer()
    stats = analyzer.get_price_statistics_for_product(product_id)
    
    if not stats:
        click.echo(f"No statistics found for product ID {product_id}.")
        return
        
    click.echo(f"--- Statistics for Product: {stats['product_name']} (ID: {product_id}) ---")
    click.echo(f"  Overall Mean Price: ${stats['mean_price']:.2f}")
    click.echo(f"  Overall Median Price: ${stats['median_price']:.2f}")
    click.echo(f"  Price Range: ${stats['min_price']:.2f} - ${stats['max_price']:.2f}")
    click.echo(f"  Last Recorded Price: ${stats['last_price']:.2f}")
    click.echo("\n  Stats by Site:")
    for site, site_stats in stats['stats_by_site'].items():
        click.echo(f"    - {site}: Mean=${site_stats['mean']:.2f}, Min=${site_stats['min']:.2f}, Max=${site_stats['max']:.2f} ({int(site_stats['count'])} records)")
        

@analyze.command()
@click.option('--top-n', default=10, help='Number of volatile products to show.')
def volatility(top_n: int):
    """Identify products with the most volatile prices."""
    analyzer = StatisticsAnalyzer()
    df = analyzer.get_price_volatility(top_n=top_n)
    
    if df is None or df.empty:
        click.echo("Could not calculate price volatility. Not enough data.")
        return
        
    click.echo(f"--- Top {top_n} Most Volatile Products ---")
    click.echo(df.to_string())


@analyze.command()
@click.argument('product_id', type=int)
def trend(product_id: int):
    """Analyze the price trend for a specific product."""
    analyzer = TrendAnalyzer()
    trend_data = analyzer.analyze_price_trend(product_id)
    
    if not trend_data:
        click.echo(f"Could not analyze trend for product ID {product_id}. Not enough data.")
        return
        
    click.echo(f"--- Price Trend for Product ID: {product_id} ---")
    click.echo(f"  Trend Direction: {trend_data['trend_direction']}")
    click.echo(f"  Slope (Price Change/Day): ${trend_data['slope']:.4f}")
    click.echo(f"  Analysis Period: {trend_data['start_date'].date()} to {trend_data['end_date'].date()}")


@analyze.command()
@click.option('--type', default='comprehensive', help='Report type (comprehensive, summary, trends)')
def generate_report(type):
    """Generate HTML report with charts and visualizations."""
    logger = get_logger(__name__)
    logger.info(f"Generating {type} report...")
    
    try:
        from src.analysis.reports import ReportGenerator
        
        generator = ReportGenerator()
        report_path = generator.generate_html_report(type)
        
        print(f"✅ Report generated successfully!")
        print(f"📄 Location: {report_path}")
        print(f"🌐 Open in browser: file://{os.path.abspath(report_path)}")
        
    except ImportError as e:
        print(f"❌ Missing dependencies for report generation: {e}")
        print("Install with: pip install matplotlib seaborn jinja2")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        print(f"❌ Report generation failed: {e}") 