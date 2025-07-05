"""
CLI commands for database management.
"""

import click

from ...data.database import db_manager
from ...data.models import Product, ProductURL, PriceHistory, Site
from ...cli.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def db():
    """Commands for database management."""
    pass


@db.command()
def init():
    """Initialize the database and create tables."""
    try:
        click.echo("Initializing database...")
        db_manager.create_tables()
        click.echo("Database tables created successfully.")
        logger.info("Database initialized via CLI.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        click.echo(f"Error: {e}", err=True)


@db.command()
@click.confirmation_option(prompt='Are you sure you want to drop all data?')
def reset():
    """Drop all tables and re-initialize the database."""
    try:
        click.echo("Resetting database...")
        db_manager.drop_tables()
        db_manager.create_tables()
        click.echo("Database has been reset successfully.")
        logger.warning("Database reset via CLI.")
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        click.echo(f"Error: {e}", err=True)


@db.command('show-last-product')
def show_last_product():
    """Show details of the last scraped product."""
    logger.info("Attempting to retrieve last scraped product.")
    with db_manager.get_session() as session:
        last_price_entry = session.query(PriceHistory).order_by(PriceHistory.scraped_at.desc()).first()

        if last_price_entry:
            product_url = session.query(ProductURL).filter_by(id=last_price_entry.product_url_id).first()
            if product_url:
                product = session.query(Product).filter_by(id=product_url.product_id).first()
                site = session.query(Site).filter_by(id=product_url.site_id).first()

                click.echo(f"--- Last Scraped Product ---")
                click.echo(f"Product Name: {product.name if product else 'N/A'}")
                click.echo(f"Site: {site.name if site else 'N/A'}")
                click.echo(f"Price: ${last_price_entry.price:.2f}")
                click.echo(f"Scraped At: {last_price_entry.scraped_at.strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo(f"Availability: {last_price_entry.availability}")
                click.echo(f"Product URL: {product_url.url}")
            else:
                click.echo("Could not find product URL details for the last price entry.")
        else:
            click.echo("No product data found in the database. Please scrape some data first.")
    logger.info("Finished retrieving last scraped product.") 