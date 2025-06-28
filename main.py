from src.scrapers.static_scraper import AmazonStaticScraper, EbayStaticScraper

def main():
    # Replace with a valid Amazon product URL
    amazon_url = "https://www.amazon.com/dp/B0863FR3S9"
    
    amazon_scraper = AmazonStaticScraper(amazon_url)
    amazon_scraper.fetch_page()
    amazon_product_info = amazon_scraper.get_product_info()
    
    if amazon_product_info:
        print("Amazon Product Information:")
        print(f"  Name: {amazon_product_info['name']}")
        print(f"  Price: {amazon_product_info['price']}")

    # Replace with a valid eBay product URL
    ebay_url = "https://www.ebay.com/itm/335930354247" # Replace with a real eBay URL
    
    ebay_scraper = EbayStaticScraper(ebay_url)
    ebay_scraper.fetch_page()
    ebay_product_info = ebay_scraper.get_product_info()

    if ebay_product_info:
        print("\nEbay Product Information:")
        print(f"  Name: {ebay_product_info['name']}")
        print(f"  Price: {ebay_product_info['price']}")

if __name__ == "__main__":
    main()