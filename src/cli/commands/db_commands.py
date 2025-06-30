"""
CLI commands for database management.
"""

import click

from ...data.database import db_manager
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