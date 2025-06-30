"""Main entry point for the E-Commerce Price Monitoring System."""

import sys
from pathlib import Path

# Add src to path for imports to ensure modules are found
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.cli.utils.logger import LoggerManager
from src.data.database import DatabaseManager
from src.scrapers.concurrent_manager import ConcurrentScrapingManager
from src.data.models import ProductURL, Site
from sqlalchemy import func

def main():
    """Simple interactive main function for running scrapers."""
    print("🛒 E-Commerce Price Monitoring System")
    print("=" * 40)
    
    # Initialize logging and database
    try:
        logger_manager = LoggerManager()
        db = DatabaseManager()
        db.initialize()
        print("✅ System initialized successfully")
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return
    
    while True:
        print("\nChoose a site to scrape:")
        print("1. eBay")
        print("2. Amazon")
        print("3. Shop.ge")
        print("4. All sites")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            print("\n🏪 Running eBay scraper...")
            run_scraper_site("ebay")
        elif choice == "2":
            print("\n🛍️ Running Amazon scraper...")
            run_scraper_site("amazon")
        elif choice == "3":
            print("\n🏬 Running Shop.ge scraper...")
            run_scraper_site("shopge")
        elif choice == "4":
            print("\n🔄 Running all scrapers (Amazon, eBay, Shop.ge)...")
            for site in ["amazon", "ebay", "shopge"]:
                run_scraper_site(site)
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please enter 1, 2, 3, 4, or 5.")

def run_scraper_site(site_name):
    """Run scraper for a specific site."""
    try:
        print(f"🚀 Starting {site_name} scraper with 3 concurrent workers...")
        
        # Create concurrent manager
        manager = ConcurrentScrapingManager(max_workers=3, use_multiprocessing=False)
        
        # Get URLs from database for the specified site
        db = DatabaseManager()
        with db.get_session() as session:
            query = session.query(ProductURL).filter(ProductURL.is_active == True)
            # Normalize site name in DB (remove dots) for matching
            normalized_db_name = func.replace(func.lower(Site.name), '.', '')
            query = query.join(ProductURL.site).filter(
                normalized_db_name == site_name.lower()
            )
            urls_to_scrape = query.all()
            
            # Extract the data we need before leaving the session context
            jobs = []
            for product_url in urls_to_scrape:
                site_name_db = product_url.site.name.lower()
                jobs.append({
                    'site_name': site_name_db,
                    'url': product_url.url
                })
        
        if not jobs:
            print(f"⚠️ No active URLs found for {site_name} in the database.")
            return
        
        print(f"📄 Found {len(jobs)} URLs to scrape for {site_name}")
        
        # Add jobs and run
        manager.add_bulk_jobs(jobs)
        manager.start_workers()
        manager.wait_completion()
        manager.stop_workers()
        
        # Get statistics
        stats = manager.get_statistics()
        
        print(f"✅ {site_name.capitalize()} scraping completed!")
        print(f"📊 Results: {stats['jobs_completed']} completed, {stats['jobs_failed']} failed")
        print(f"⏱️ Total time: {stats['elapsed_time']:.2f}s")
        
    except Exception as e:
        print(f"❌ Error running {site_name} scraper: {e}")
        print(f"💡 You can also use the full CLI: python -m src.cli.interface scrape run --site {site_name}")

if __name__ == '__main__':
    main()