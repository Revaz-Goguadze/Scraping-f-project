"""
CLI commands for running scrapers.
"""

import click
from typing import List

from ...scrapers.concurrent_manager import ConcurrentScrapingManager
from ...cli.utils.logger import get_logger
from ...data.database import db_manager
from ...data.models import ProductURL, Site

logger = get_logger(__name__)


@click.group()
def scrape():
    """Commands for running scrapers."""
    pass


@scrape.command()
@click.option('--site', '-s', multiple=True, help='Run scraper for specific site(s). Can be used multiple times.')
@click.option('--workers', '-w', type=int, default=3, help='Number of concurrent workers.')
@click.option('--use-multiprocessing', is_flag=True, help='Use multiprocessing instead of threading.')
@click.option('--limit', '-l', type=int, help='Limit the number of URLs to scrape per site.')
def run(site: List[str], workers: int, use_multiprocessing: bool, limit: int):
    """Run scrapers for specified sites or all sites."""
    logger.info(f"Starting concurrent scraping run with {workers} workers.")
    
    manager = ConcurrentScrapingManager(
        max_workers=workers,
        use_multiprocessing=use_multiprocessing
    )

    # Get URLs from database
    with db_manager.get_session() as session:
        query = session.query(ProductURL).filter(ProductURL.is_active == True)
        
        if site:
            query = query.join(ProductURL.site).filter(Site.name.in_(site))
            
        urls_to_scrape = query.all()

    if not urls_to_scrape:
        logger.warning("No active URLs found in the database to scrape.")
        return

    # Add jobs to manager
    jobs = []
    for product_url in urls_to_scrape:
        if limit and len(jobs) >= limit:
            break
        jobs.append({
            'site_name': product_url.site.name.lower(),
            'url': product_url.url
        })

    manager.add_bulk_jobs(jobs)
    
    # Run scrapers
    manager.start_workers()
    manager.wait_completion()
    manager.stop_workers()
    
    stats = manager.get_statistics()
    logger.info(f"Scraping run completed. Results: {stats}")
    click.echo(f"Scraping completed. See logs for details.") 