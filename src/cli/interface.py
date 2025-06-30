"""
Command-line interface for the E-Commerce Price Monitoring System.
Provides a user-friendly interface to run scrapers, analyze data, and generate reports.
"""

import click
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from .commands import scrape_commands, analysis_commands, db_commands
from ..cli.utils.logger import get_logger, logger_manager
from ..cli.utils.config import config_manager
from ..data.database import db_manager
import uuid

logger = get_logger(__name__)


@click.group()
@click.option('--config-dir', default='config', help='Path to configuration directory.')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']), help='Set logging level.')
@click.pass_context
def cli(ctx, config_dir, log_level):
    """
    E-Commerce Price Monitoring System CLI.
    
    A comprehensive tool to scrape, analyze, and report on e-commerce product data.
    """
    # Initialize a session ID for this CLI execution
    session_id = str(uuid.uuid4())[:8]
    logger_manager.set_session_id(session_id)
    
    # Load configuration
    config_manager.config_paths['settings'] = f'{config_dir}/settings.yaml'
    config_manager.config_paths['scrapers'] = f'{config_dir}/scrapers.yaml'
    config_manager.load_config()

    # Override log level if provided
    if log_level:
        config_manager.set_setting('logging.level', log_level)
        logger_manager._setup_logging()  # Re-initialize logging with new level

    # Initialize database
    db_manager.initialize(database_url=config_manager.get_database_url())
    
    ctx.obj = {
        'session_id': session_id,
        'config_dir': config_dir
    }
    
    logger.info(f"CLI initialized with session ID: {session_id}")


# Add command groups to the main CLI
cli.add_command(scrape_commands.scrape)
cli.add_command(analysis_commands.analyze)
cli.add_command(db_commands.db)


if __name__ == '__main__':
    cli()
