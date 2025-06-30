#!/usr/bin/env python3
"""
Setup script to populate database with fixed, working product URLs.
Uses 3 reliable URLs from Shop.ge, Amazon, and eBay.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import DatabaseManager

def setup_fixed_urls():
    """Add the 3 fixed URLs specified by user."""
    print("🔧 Setting up database with fixed product URLs...")
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize()
    
    with db_manager.get_session() as session:
        from src.data.models import Site, Product, ProductURL
        
        print("📋 Clearing existing data...")
        session.query(ProductURL).delete()
        session.query(Product).delete() 
        session.query(Site).delete()
        
        # 1. Create Shop.ge site and product
        print("🏬 Adding Shop.ge...")
        shopge_site = db_manager.create_site(
            name="Shop.ge",
            base_url="https://www.shop.ge",
            scraper_type="static", 
            rate_limit=1.5
        )
        session.flush()
        
        troika_pen = db_manager.create_product(
            name="Troika CONSTRUCTION LILIPUT Pen",
            category="office_supplies",
            brand="Troika"
        )
        session.flush()
        
        db_manager.create_product_url(
            product_id=troika_pen.id,
            site_id=shopge_site.id,
            url="https://www.shop.ge/online-shop/sakancelario-nivtebi/saweri-kalami/troika-kalami-troika-construction-liliput-697455.html"
        )
        
        # 2. Create Amazon site and product  
        print("📦 Adding Amazon...")
        amazon_site = db_manager.create_site(
            name="Amazon",
            base_url="https://www.amazon.com",
            scraper_type="static",
            rate_limit=2.0
        )
        session.flush()
        
        headphones = db_manager.create_product(
            name="BERIBES Bluetooth Headphones",
            category="electronics", 
            brand="BERIBES"
        )
        session.flush()
        
        db_manager.create_product_url(
            product_id=headphones.id,
            site_id=amazon_site.id,
            url="https://www.amazon.com/BERIBES-Bluetooth-Headphones-Microphone-Lightweight/dp/B09LYF2ST7?_encoding=UTF8&content-id=amzn1.sym.f0670b1b-e1fd-4c67-a2b1-b8a347243628&dib=eyJ2IjoiMSJ9.Pfix3I77yjMkN8wajdeQJx6zpcL_ntk5tWSLbZ9poiySHVVFus7OVw0EceEy_TaU-ITLULZcoxv0rXyPyX74Ups2mrVGaE6yAGEpTtourXld-fUJ7-1b82y0x-uk2MaQRD9-gabhvG7z76MH_BbUIuFrVGMXvx4dNNl3Lo_meQdPIpuoRivAYSwGCDiwU4Jm4OJ9w9JCRYu1JEVEUe6owWcCg3p1XF7XOvgEzXT1j_k.Skt0ZSDfpMJzhlvvZr3tN1KYLFJJSA4p1yxzgwLZRMs&dib_tag=se&keywords=headphones&pd_rd_r=ac801a6a-d84e-4903-9acf-52d1d479b268&pd_rd_w=h1ur4&pd_rd_wg=xSuye&qid=1751306960&sr=8-1"
        )
        
        # 3. Create eBay site and product
        print("🛒 Adding eBay...")
        ebay_site = db_manager.create_site(
            name="eBay", 
            base_url="https://www.ebay.com",
            scraper_type="static",
            rate_limit=3.0
        )
        session.flush()
        
        ebay_item = db_manager.create_product(
            name="eBay Listed Item",
            category="general",
            brand="Unknown"
        )
        session.flush()
        
        db_manager.create_product_url(
            product_id=ebay_item.id,
            site_id=ebay_site.id,
            url="https://www.ebay.com/itm/365662264378?_trksid=p4375194.c101959.m146925"
        )
        
        session.commit()
    
    print("✅ Database setup complete!")
    print("📊 Summary:")
    print("  • 3 sites: Shop.ge, Amazon, eBay")
    print("  • 3 products with fixed URLs")
    print("  • Ready for scraping with reliable data")

if __name__ == "__main__":
    setup_fixed_urls() 