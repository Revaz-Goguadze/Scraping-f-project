#!/usr/bin/env python3
"""
Script to populate the database with sample product data for testing.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data.database import db_manager
from src.data.models import Product, Site, ProductURL
from src.cli.utils.config import config_manager
from src.cli.utils.logger import get_logger

logger = get_logger(__name__)

def setup_sample_data():
    """Set up sample products and URLs for testing."""
    
    # Initialize database
    db_manager.initialize()
    
    with db_manager.get_session() as session:
        # Check if sites already exist, if not create them
        amazon_site = session.query(Site).filter(Site.name == "Amazon").first()
        if not amazon_site:
            amazon_site = db_manager.create_site(
                name="Amazon",
                base_url="https://www.amazon.com",
                scraper_type="static",
                rate_limit=2.0
            )
            session.refresh(amazon_site)
            print("✅ Created Amazon site")
        else:
            print("ℹ️  Amazon site already exists")
        
        ebay_site = session.query(Site).filter(Site.name == "eBay").first()
        if not ebay_site:
            ebay_site = db_manager.create_site(
                name="eBay", 
                base_url="https://www.ebay.com",
                scraper_type="static",
                rate_limit=1.5
            )
            session.refresh(ebay_site)
            print("✅ Created eBay site")
        else:
            print("ℹ️  eBay site already exists")
        
        walmart_site = session.query(Site).filter(Site.name == "Walmart").first()
        if not walmart_site:
            walmart_site = db_manager.create_site(
                name="Walmart",
                base_url="https://www.walmart.com", 
                scraper_type="selenium",
                rate_limit=2.5
            )
            session.refresh(walmart_site)
            print("✅ Created Walmart site")
        else:
            print("ℹ️  Walmart site already exists")
        
        # Check if products already exist
        headphones_product = session.query(Product).filter(Product.name.like("%Sony WH-1000XM4%")).first()
        if not headphones_product:
            headphones_product = db_manager.create_product(
                name="Sony WH-1000XM4 Wireless Headphones",
                category="electronics",
                brand="Sony",
                model="WH-1000XM4"
            )
            session.refresh(headphones_product)
            print("✅ Created Sony headphones product")
        else:
            print("ℹ️  Sony headphones product already exists")
        
        smartphone_product = session.query(Product).filter(Product.name.like("%iPhone 15 Pro%")).first()
        if not smartphone_product:
            smartphone_product = db_manager.create_product(
                name="iPhone 15 Pro",
                category="electronics", 
                brand="Apple",
                model="iPhone 15 Pro"
            )
            session.refresh(smartphone_product)
            print("✅ Created iPhone product")
        else:
            print("ℹ️  iPhone product already exists")
        
        # Create product URLs (check if they exist first)
        amazon_headphones_url = "https://www.amazon.com/dp/B0863FR3S9"
        existing_url = session.query(ProductURL).filter(
            ProductURL.url == amazon_headphones_url,
            ProductURL.product_id == headphones_product.id,
            ProductURL.site_id == amazon_site.id
        ).first()
        
        if not existing_url:
            db_manager.create_product_url(
                product_id=headphones_product.id,
                site_id=amazon_site.id,
                url=amazon_headphones_url
            )
            print("✅ Created Amazon headphones URL")
        else:
            print("ℹ️  Amazon headphones URL already exists")
        
        amazon_phone_url = "https://www.amazon.com/dp/B0CHX1W1XY"
        existing_url = session.query(ProductURL).filter(
            ProductURL.url == amazon_phone_url,
            ProductURL.product_id == smartphone_product.id,
            ProductURL.site_id == amazon_site.id
        ).first()
        
        if not existing_url:
            db_manager.create_product_url(
                product_id=smartphone_product.id,
                site_id=amazon_site.id, 
                url=amazon_phone_url
            )
            print("✅ Created Amazon iPhone URL")
        else:
            print("ℹ️  Amazon iPhone URL already exists")
        
        print(f"\n📊 Database Summary:")
        print(f"  Sites: {session.query(Site).count()}")
        print(f"  Products: {session.query(Product).count()}")
        print(f"  Product URLs: {session.query(ProductURL).count()}")
        
        print(f"\n🔍 Available product URLs:")
        for url in session.query(ProductURL).all():
            print(f"  - {url.site.name}: {url.url}")

if __name__ == "__main__":
    setup_sample_data() 