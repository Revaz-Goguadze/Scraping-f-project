#!/usr/bin/env python3
"""
Script to add a specific Shop.ge URL to the database for scraping.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data.database import DatabaseManager
from src.data.models import Site, Product, ProductURL

def add_shopge_url():
    """Add a specific Shop.ge URL to the database."""
    db = DatabaseManager()
    db.initialize()
    
    shopge_url = "https://www.shop.ge/online-shop/sakancelario-nivtebi/saweri-kalami/troika-kalami-troika-construction-liliput-697455.html"
    
    with db.get_session() as session:
        # Check if Shop.ge site exists, if not create it
        shopge_site = session.query(Site).filter_by(name="Shop.ge").first()
        if not shopge_site:
            shopge_site = Site(
                name="Shop.ge",
                base_url="https://www.shop.ge",
                scraper_type="static",
                rate_limit=1.5
            )
            session.add(shopge_site)
            session.flush()
            print("🏬 Added Shop.ge site to database.")
        else:
            print("🏬 Shop.ge site already exists in database.")
        
        # Check if a product needs to be created or linked
        product_name = "Troika Construction Liliput Pen"
        product = session.query(Product).filter_by(name=product_name).first()
        if not product:
            product = Product(
                name=product_name,
                category="Stationery",
                brand="Troika",
                model="Liliput"
            )
            session.add(product)
            session.flush()
            print(f"🖊️ Added product '{product_name}' to database.")
        else:
            print(f"🖊️ Product '{product_name}' already exists in database.")
        
        # Check if the URL already exists for this product and site
        product_url = session.query(ProductURL).filter_by(url=shopge_url, site_id=shopge_site.id).first()
        if not product_url:
            product_url = ProductURL(
                product_id=product.id,
                site_id=shopge_site.id,
                url=shopge_url,
                is_active=True
            )
            session.add(product_url)
            session.commit()
            print(f"🔗 Added URL '{shopge_url}' for Shop.ge to database.")
        else:
            print(f"🔗 URL '{shopge_url}' for Shop.ge already exists in database.")

if __name__ == "__main__":
    try:
        add_shopge_url()
    except Exception as e:
        print(f"❌ Error adding Shop.ge URL to database: {e}")
