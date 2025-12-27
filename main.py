"""
News Scraper - Main Entry Point
Tool crawl tin tức từ nhiều nguồn và lưu vào PostgreSQL + Export CSV

Supported sources:
- CafeF.vn
- VnExpress.net
- VnEconomy.vn
- VOV.vn
- Vietnamnet.vn

Usage:
    python main.py                  # Scrape tất cả sources
    python main.py cafef            # Chỉ CafeF
    python main.py vnexpress        # Chỉ VnExpress
    python main.py vneconomy        # Chỉ VnEconomy
    python main.py vov              # Chỉ VOV
    python main.py vietnamnet       # Chỉ Vietnamnet
    python main.py csv              # Scrape CafeF và export CSV only
    python main.py test             # Test mode
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.multi_source_scraper import (
    CafeFScraper,
    VnExpressScraper,
    VnEconomyScraper,
    VOVScraper,
    VietnametScraper,
)
from database.models import db
from utils.exporters import export_to_csv, export_to_json


def scrape_cafef(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape CafeF"""
    print("\n" + "="*60)
    print("🔵 CAFEF.VN SCRAPER")
    print("="*60)

    scraper = CafeFScraper()
    articles = scraper.fetch_news(max_pages=4, max_articles_per_page=20)
    
    _save_and_export(articles, "cafef", save_to_db, export_csv)
    return articles


def scrape_vnexpress(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VnExpress"""
    print("\n" + "="*60)
    print("🟢 VNEXPRESS.NET SCRAPER")
    print("="*60)
    
    scraper = VnExpressScraper()
    articles = scraper.fetch_news(max_pages=2)
    
    _save_and_export(articles, "vnexpress", save_to_db, export_csv)
    return articles


def scrape_vneconomy(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VnEconomy"""
    print("\n" + "="*60)
    print("🟡 VNECONOMY.VN SCRAPER")
    print("="*60)
    
    scraper = VnEconomyScraper()
    articles = scraper.fetch_news(max_pages=2)
    
    _save_and_export(articles, "vneconomy", save_to_db, export_csv)
    return articles


def scrape_vov(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VOV"""
    print("\n" + "="*60)
    print("🔴 VOV.VN SCRAPER")
    print("="*60)
    
    scraper = VOVScraper()
    articles = scraper.fetch_news()
    
    _save_and_export(articles, "vov", save_to_db, export_csv)
    return articles


def scrape_vietnamnet(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Vietnamnet"""
    print("\n" + "="*60)
    print("🟣 VIETNAMNET.VN SCRAPER")
    print("="*60)

    scraper = VietnametScraper()
    articles = scraper.fetch_news()  # Crawl tất cả các pages

    _save_and_export(articles, "vietnamnet", save_to_db, export_csv)
    return articles


def _save_and_export(articles: list, source_name: str, save_to_db: bool, export_csv: bool):
    """Helper function để save và export"""
    if not articles:
        print(f"\n⚠ No articles scraped from {source_name}!")
        return
    
    print(f"\n📊 Total articles scraped: {len(articles)}")
    
    # Save to database
    if save_to_db:
        print("\n💾 Saving to database...")
        saved_count = 0
        for article in articles:
            # article tuple: (published_at, title, link, content, source, stock_related, sentiment_score, server_pushed, category)
            if len(article) == 9:
                data = article[:8]  # Exclude category for basic insert
                category = article[8]
                if db.insert_news_with_category(data, category):
                    saved_count += 1
            else:
                if db.insert_news(article):
                    saved_count += 1
        
        print(f"  ✓ Saved {saved_count}/{len(articles)} articles to database")
    
    # Export to CSV
    if export_csv:
        print("\n📁 Exporting to CSV...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Convert tuples to dicts for export
        articles_dict = []
        for a in articles:
            articles_dict.append({
                'published_at': a[0],
                'title': a[1],
                'link': a[2],
                'content': a[3],
                'source': a[4],
                'stock_related': a[5],
                'sentiment_score': a[6],
                'server_pushed': a[7],
                'category': a[8] if len(a) > 8 else '',
            })
        
        csv_path = export_to_csv(articles_dict, filename=f"{source_name}_{timestamp}")
        print(f"  ✓ Exported to: {csv_path}")


def scrape_all():
    """Scrape tất cả các nguồn"""
    print("="*60)
    print("🚀 MULTI-SOURCE NEWS SCRAPER")
    print("="*60)
    
    # Setup database
    print("\n[1] Setting up database...")
    try:
        db.create_tables()
    except Exception as e:
        print(f"⚠ Database warning: {e}")
        print("Will export to CSV only...")
    
    all_articles = []
    
    # Scrape từng source
    all_articles.extend(scrape_cafef(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_vnexpress(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_vneconomy(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_vov(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_vietnamnet(save_to_db=True, export_csv=False))
    
    # Export all to CSV
    print("\n" + "="*60)
    print("📁 FINAL EXPORT")
    print("="*60)
    
    if all_articles:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        articles_dict = []
        for a in all_articles:
            articles_dict.append({
                'published_at': a[0],
                'title': a[1],
                'link': a[2],
                'content': a[3],
                'source': a[4],
                'stock_related': a[5],
                'sentiment_score': a[6],
                'server_pushed': a[7],
                'category': a[8] if len(a) > 8 else '',
            })
        
        csv_path = export_to_csv(articles_dict, filename=f"all_news_{timestamp}")
        json_path = export_to_json(articles_dict, filename=f"all_news_{timestamp}")
        
        print(f"\n{'='*60}")
        print(f"✅ DONE!")
        print(f"{'='*60}")
        print(f"Total articles: {len(all_articles)}")
        print(f"CSV: {csv_path}")
        print(f"JSON: {json_path}")


def test_mode():
    """Test với một source"""
    print("="*60)
    print("🧪 TEST MODE - CafeF Only")
    print("="*60)

    scraper = CafeFScraper()
    scraper.delay = 1  # Faster for testing

    print("\nFetching 3 articles for testing...")
    articles = scraper.fetch_news(max_pages=1, max_articles_per_page=3)
    
    print(f"\n📊 Results: {len(articles)} articles")
    for i, article in enumerate(articles, 1):
        print(f"\n--- Article {i} ---")
        print(f"Title: {article[1][:60]}...")
        print(f"Link: {article[2][:60]}...")
        print(f"Published: {datetime.fromtimestamp(article[0]) if article[0] else 'N/A'}")
        print(f"Content: {len(article[3])} chars")
        print(f"Source: {article[4]}")


def show_help():
    """Hiển thị hướng dẫn"""
    print("""
MULTI-SOURCE NEWS SCRAPER
=========================

Usage:
    python main.py                  Scrape tất cả sources (CafeF, VnExpress, VnEconomy, VOV, Vietnamnet)
    python main.py cafef            Chỉ scrape CafeF
    python main.py vnexpress        Chỉ scrape VnExpress
    python main.py vneconomy        Chỉ scrape VnEconomy
    python main.py vov              Chỉ scrape VOV
    python main.py vietnamnet       Chỉ scrape Vietnamnet
    python main.py csv              Scrape CafeF, export CSV only (không cần DB)
    python main.py test             Test mode (3 bài từ CafeF)
    python main.py help             Hiển thị hướng dẫn này

Database Schema:
    Table: news
    - id (UUID, primary key)
    - published_at (bigint, Unix timestamp)
    - title (text, NOT NULL, UNIQUE)
    - link (text)
    - content (text)
    - source (text)
    - stock_related (text)
    - sentiment_score (text)
    - server_pushed (boolean)
    - created_at (timestamp)
    - category (text)

Output:
    - Database: PostgreSQL table 'news'
    - CSV files: exports/
    - JSON files: exports/
""")


if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else 'all'
    
    try:
        if mode == 'cafef':
            db.create_tables()
            scrape_cafef()
        elif mode == 'vnexpress':
            db.create_tables()
            scrape_vnexpress()
        elif mode == 'vneconomy':
            db.create_tables()
            scrape_vneconomy()
        elif mode == 'vov':
            db.create_tables()
            scrape_vov()
        elif mode == 'vietnamnet':
            db.create_tables()
            scrape_vietnamnet()
        elif mode == 'csv':
            scrape_cafef(save_to_db=False, export_csv=True)
        elif mode == 'test':
            test_mode()
        elif mode in ['help', '-h', '--help']:
            show_help()
        else:
            scrape_all()
            
    except KeyboardInterrupt:
        print("\n\n⚠ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
