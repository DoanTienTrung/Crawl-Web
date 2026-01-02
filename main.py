"""
News Scraper - Main Entry Point
Tool crawl tin tức từ nhiều nguồn và lưu vào PostgreSQL + Export CSV

Supported sources:
- CafeF.vn
- Cafeland.vn
- VnExpress.net
- VnEconomy.vn
- VOV.vn
- Vietnamnet.vn

Usage:
    python main.py qdnd
    python main.py agromonitor
    python main.py vietstock
    python main.py antt
    python main.py tuoitre
    python main.py laodong
    python main.py thanhnien
    python main.py dantri
    python main.py                  # Scrape tất cả sources
    python main.py cafef            # Chỉ CafeF
    python main.py cafeland         # Chỉ Cafeland
    python main.py vnexpress        # Chỉ VnExpress
    python main.py vneconomy        # Chỉ VnEconomy
    python main.py vov              # Chỉ VOV
    python main.py vietnamnet       # Chỉ Vietnamnet
    python main.py csv              # Scrape CafeF và export CSV only
    python main.py test             # Test mode
"""

import sys
import os
import io
from datetime import datetime

# Fix Unicode encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.multi_source_scraper import (
    CafeFScraper,
    CafelandScraper,
    VnExpressScraper,
    VnEconomyScraper,
    VOVScraper,
    VietnametScraper,
    DanTriRSSScraper,
    ThanhNienRSSScraper,
    TuoiTreRSSScraper,
    LaoDongScraper,
    NLDScraper,
    VietStockScraper,
    ANTTRSSScraper,
    # AgroMonitorScraper,
    CNARSSScraper,
    QDNDRSSScraper,
    KinhTeNgoaiThuongScraper,
    ThoiBaoNganHangScraper,
    TaiChinhDoanhNghiepScraper,
    BaoChinhPhuScraper,
    TinNhanhChungKhoanScraper,
    NguoiQuanSatScraper,
    ThoiBaoTaiChinhScraper,
)
from database.models import db
from utils.exporters import export_to_csv, export_to_json

def scrape_nguoiquansat(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Người Quan Sát với cấu trúc mới"""
    print("\n" + "="*60)
    print("📈 NGƯỜI QUAN SÁT (NGUOIQUANSAT.VN) - main.py")
    print("="*60)
    
    scraper = NguoiQuanSatScraper()
    # Quét 10 bài mới nhất
    articles = scraper.fetch_news(max_articles=10)
    
    _save_and_export(articles, "nguoiquansat", save_to_db, export_csv)
    return articles

def scrape_thoibaotaichinh(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Thời báo Tài chính Việt Nam (thoibaotaichinhvietnam.vn)"""
    print("\n" + "="*60)
    print("📈 THỜI BÁO TÀI CHÍNH (THOIBAOTAICHINHVN.VN) - main.py")
    print("="*60)
    
    scraper = ThoiBaoTaiChinhScraper()
    
    # Crawl 10 bài mới nhất từ trang chủ
    # (nếu muốn theo chuyên mục, thay url trong scraper.fetch_news())
    articles = scraper.fetch_news(max_articles=10)
    
    # Lưu và xuất CSV giống cấu trúc cũ
    _save_and_export(articles, "thoibaotaichinh", save_to_db, export_csv)
    
    return articles


def scrape_taichinhdoanhnghiep(save_to_db: bool = True, export_csv: bool = True) -> list:
    """
    Hàm điều phối quét tin từ Tài chính Doanh nghiệp (taichinhdoanhnghiep.net.vn)
    """
    print("\n" + "="*60)
    print("💼 TÀI CHÍNH DOANH NGHIỆP SCRAPER")
    print("="*60)

    # 1. Khởi tạo scraper
    scraper = TaiChinhDoanhNghiepScraper()
    
    # 2. Lấy dữ liệu bài viết (mặc định lấy 15 bài mới nhất từ trang chủ)
    try:
        articles = scraper.fetch_news(max_articles=15)
    except Exception as e:
        print(f"❌ Lỗi khi quét tin: {str(e)}")
        return []

    # 3. Xử lý lưu trữ
    if articles:
        print(f"✨ Đã thu thập tổng cộng {len(articles)} bài viết hợp lệ.")
        
        # Gọi hàm helper dùng chung để save vào DB và xuất CSV
        # Lưu ý: Đảm bảo bạn đã có hàm _save_and_export hoặc logic tương tự trong main.py
        if save_to_db or export_csv:
            _save_and_export(articles, "taichinhdoanhnghiep", save_to_db, export_csv)
    else:
        print("⚠️ Không tìm thấy bài viết mới nào hoặc cấu hình Selector bị sai.")

    return articles

def scrape_kinhte(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Kinh tế và Ngoại thương"""
    print("\n" + "="*60)
    print("📈 KINH TẾ NGOẠI THƯƠNG SCRAPER")
    print("="*60)

    scraper = KinhTeNgoaiThuongScraper()
    articles = scraper.fetch_news()
    
    _save_and_export(articles, "kinhte", save_to_db, export_csv)
    return articles

def scrape_qdnd(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape báo Quân đội nhân dân qua RSS"""
    print("\n" + "="*60)
    print("🎖️ QUÂN ĐỘI NHÂN DÂN (QDND) RSS SCRAPER")
    print("="*60)

    scraper = QDNDRSSScraper()
    # Hàm fetch_news() trong class RSS không cần tham số max_articles 
    # vì nó đã giới hạn 20 bài bên trong logic.
    articles = scraper.fetch_news()
    
    _save_and_export(articles, "qdnd", save_to_db, export_csv)
    return articles


def scrape_cafef(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape CafeF"""
    print("\n - main.py:58" + "="*60)
    print("🔵 CAFEF.VN SCRAPER - main.py:59")
    print("="*60)

    scraper = CafeFScraper()
    articles = scraper.fetch_news(max_pages=1, max_articles_per_page=20)
    
    _save_and_export(articles, "cafef", save_to_db, export_csv)
    return articles

# def scrape_agromonitor(save_to_db: bool = True, export_csv: bool = True, max_articles: int = 20) -> list:
#     """Scrape AgroMonitor.vn"""
#     print("\n" + "="*60)
#     print("🟢 AGROMONITOR.VN SCRAPER")
#     print("="*60)

#     # Khởi tạo scraper chuyên biệt cho AgroMonitor
#     scraper = AgroMonitorScraper()

#     # Lấy tin từ trang chủ/tin mới nhất (category 16)
#     # Lưu ý: Nếu trang này yêu cầu login để thấy nội dung,
#     # bạn cần đảm bảo self.headers trong class scraper đã có Cookie.
#     articles = scraper.fetch_news(max_pages=1, max_articles_per_page=max_articles)

#     # Sử dụng hàm tiện ích chung của bạn để lưu và xuất dữ liệu
#     _save_and_export(articles, "agromonitor", save_to_db, export_csv)

#     return articles

def scrape_cafeland(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Cafeland"""
    print("\n" + "="*60)
    print("🟠 CAFELAND.VN SCRAPER - main.py:72")
    print("="*60)

    scraper = CafelandScraper()
    articles = scraper.fetch_news(max_pages=1, max_articles_per_page=20)

    _save_and_export(articles, "cafeland", save_to_db, export_csv)
    return articles


def scrape_vnexpress(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VnExpress"""
    print("\n" + "="*60)
    print("🟢 VNEXPRESS.NET SCRAPER - main.py:85")
    print("="*60)

    scraper = VnExpressScraper()
    articles = scraper.fetch_news(max_pages=1)  # Crawl page đầu tiên
    
    _save_and_export(articles, "vnexpress", save_to_db, export_csv)
    return articles


def scrape_tuoitre(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape TuoiTre sử dụng RSS"""
    print("\n" + "="*60)
    print("🟢 TUOITRE.VN RSS SCRAPER - main.py:98")
    print("="*60)

    scraper = TuoiTreRSSScraper()
    articles = scraper.fetch_news()
    
    _save_and_export(articles, "tuoitre", save_to_db, export_csv)
    return articles


def scrape_vneconomy(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VnEconomy using RSS feed"""
    print("\n" + "="*60)
    print("🟡 VNECONOMY.VN RSS SCRAPER - main.py:111")
    print("="*60)
    
    scraper = VnEconomyScraper()
    
    # Với RSS, chúng ta chỉ cần truyền tổng số bài viết muốn lấy (max_articles)
    # Không cần chia trang (max_pages) vì RSS trả về danh sách tin mới nhất tập trung
    articles = scraper.fetch_news(max_articles=20)
    
    if not articles:
        print(f"⚠ No articles scraped from vneconomy! - main.py")
        return []

    _save_and_export(articles, "vneconomy", save_to_db, export_csv)
    return articles


def scrape_vov(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VOV"""
    print("\n" + "="*60)
    print("🔴 VOV.VN SCRAPER - main.py:124")
    print("="*60)

    scraper = VOVScraper()
    articles = scraper.fetch_news(max_pages=1)  # Crawl page đầu tiên

    _save_and_export(articles, "vov", save_to_db, export_csv)
    return articles

def scrape_cna(save_to_db: bool = True, export_csv: bool = True) -> list:
    """
    Scrape Channel NewsAsia (CNA) sử dụng RSS Feed
    """
    print("\n" + "="*60)
    print("🔴 CHANNEL NEWSASIA (CNA) RSS SCRAPER")
    print("="*60)

    scraper = CNARSSScraper()
    articles = scraper.fetch_news()
    
    _save_and_export(articles, "cna", save_to_db, export_csv)
    
    return articles


def scrape_vietnamnet(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Vietnamnet"""
    print("\n" + "="*60)
    print("🟣 VIETNAMNET.VN SCRAPER - main.py:137")
    print("="*60)

    scraper = VietnametScraper()
    articles = scraper.fetch_news()  # Crawl page đầu tiên

    _save_and_export(articles, "vietnamnet", save_to_db, export_csv)
    return articles


def scrape_dantri(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape DanTri sử dụng RSS"""
    print("\n" + "="*60)
    print("🔴 DANTRI.COM.VN RSS SCRAPER - main.py:150")
    print("="*60)

    scraper = DanTriRSSScraper()
    # RSS của Dân trí không cần truyền số trang như cào HTML thông thường
    articles = scraper.fetch_news() 
    
    _save_and_export(articles, "dantri", save_to_db, export_csv)
    return articles


def scrape_thanhnien(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape ThanhNien sử dụng RSS"""
    print("\n" + "="*60)
    print("🔵 THANHNIEN.VN RSS SCRAPER - main.py:164")
    print("="*60)

    # Khởi tạo scraper chuyên biệt cho Thanh Niên
    scraper = ThanhNienRSSScraper()

    # Lấy tin tức từ RSS (mặc định lấy 20 bài mới nhất như đã thiết lập trong Class)
    articles = scraper.fetch_news()

    # Gọi hàm helper để lưu và xuất dữ liệu
    _save_and_export(articles, "thanhnien", save_to_db, export_csv)

    return articles


def scrape_laodong(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape LaoDong"""
    print("\n" + "="*60)
    print("🟡 LAODONG.VN SCRAPER")
    print("="*60)

    scraper = LaoDongScraper()

    # Lấy 20 bài mới nhất từ trang tin mới
    articles = scraper.fetch_news(max_articles=20)

    # Gọi hàm helper để lưu và xuất dữ liệu
    _save_and_export(articles, "laodong", save_to_db, export_csv)

    return articles


def scrape_nld(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape NLD (Người Lao Động)"""
    print("\n" + "="*60)
    print("🔵 NLD.COM.VN SCRAPER")
    print("="*60)

    scraper = NLDScraper()

    # Lấy 20 bài mới nhất từ trang tin 24h
    articles = scraper.fetch_news(max_articles=20)

    # Gọi hàm helper để lưu và xuất dữ liệu
    _save_and_export(articles, "nld", save_to_db, export_csv)

    return articles

def scrape_baochinhphu(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Điều phối quét tin từ Báo Chính phủ"""
    print("\n" + "="*60)
    print("🏛️ BÁO CHÍNH PHỦ SCRAPER")
    print("="*60)

    scraper = BaoChinhPhuScraper()
    articles = scraper.fetch_news(max_articles=15)

    if articles:
        # Sử dụng hàm helper của bạn để lưu
        _save_and_export(articles, "baochinhphu", save_to_db, export_csv)
    return articles


def scrape_tinnhanhchungkhoan(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Tin nhanh chứng khoán"""
    print("\n" + "="*60)
    print("📈 TIN NHANH CHỨNG KHOÁN SCRAPER")
    print("="*60)

    scraper = TinNhanhChungKhoanScraper()
    articles = scraper.fetch_news(max_articles=10)

    _save_and_export(articles, "tinnhanhchungkhoan", save_to_db, export_csv)
    return articles


def scrape_vietstock(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VietStock"""
    print("\n" + "="*60)
    print("🟢 VIETSTOCK.VN SCRAPER")
    print("="*60)

    scraper = VietStockScraper()

    # Lấy 15 bài mới nhất từ trang mới cập nhật
    articles = scraper.fetch_news(max_articles=15)

    # Gọi hàm helper để lưu và xuất dữ liệu
    _save_and_export(articles, "vietstock", save_to_db, export_csv)

    return articles

def scrape_antt(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape ANTT.vn sử dụng RSS"""
    print("\n" + "="*60)
    print("🟠 ANTT.VN RSS SCRAPER")
    print("=" * 60)

    # Khởi tạo class scraper 
    scraper = ANTTRSSScraper()
    
    # Lấy tin từ RSS
    articles = scraper.fetch_news() 
    
    _save_and_export(articles, "antt", save_to_db, export_csv)
    return articles

def scrape_thoibaonganhang(save_to_db: bool = True, export_csv: bool = True) -> list:
    """
    Hàm điều phối Scraper cho Thời báo Ngân hàng (thoibaonganhang.vn)
    """
    print("\n" + "="*60)
    print("🏦 THỜI BÁO NGÂN HÀNG (TBNH) SCRAPER")
    print("="*60)

    # Khởi tạo class scraper (đảm bảo bạn đã import class ThoiBaoNganHangScraper)
    scraper = ThoiBaoNganHangScraper()
    
    # Thực hiện bóc tách dữ liệu
    articles = scraper.fetch_news(max_articles=15)
    
    # Lưu và xuất dữ liệu (Sử dụng hàm dùng chung trong dự án của bạn)
    if articles:
        _save_and_export(articles, "thoibaonganhang", save_to_db, export_csv)
    else:
        print("\n⚠ No articles scraped from thoibaonganhang!")
        
    return articles

def _save_and_export(articles: list, source_name: str, save_to_db: bool, export_csv: bool):
    """Helper function để save và export"""
    if not articles:
        print(f"\n⚠ No articles scraped from {source_name}! - main.py:197")
        return
    
    print(f"\n📊 Total articles scraped: {len(articles)} - main.py:200")
    
    # Save to database
    if save_to_db:
        print("\n💾 Saving to database... - main.py:204")
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
        
        print(f"✓ Saved {saved_count}/{len(articles)} articles to database - main.py:217")
    
    # Export to CSV
    if export_csv:
        print("\n📁 Exporting to CSV... - main.py:221")
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
        print(f"✓ Exported to: {csv_path} - main.py:240")


def scrape_all():
    """Scrape tất cả các nguồn"""
    print("\n" + "="*60)
    print("🚀 MULTISOURCE NEWS SCRAPER - main.py:246")
    print("="*60)
    
    # Setup database
    print("\n[1] Setting up database... - main.py:250")
    try:
        db.create_tables()
    except Exception as e:
        print(f"⚠ Database warning: {e} - main.py:254")
        print("Will export to CSV only... - main.py:255")
    
    all_articles = []
    
    # Scrape từng source
    all_articles.extend(scrape_cafef(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_cafeland(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_vnexpress(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_vneconomy(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_vov(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_vietnamnet(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_dantri(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_thanhnien(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_tuoitre(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_laodong(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_nld(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_vietstock(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_antt(save_to_db=True, export_csv=False))
    # all_articles.extend(scrape_agromonitor(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_cna(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_qdnd(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_kinhte(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_thoibaonganhang(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_taichinhdoanhnghiep(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_baochinhphu(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_tinnhanhchungkhoan(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_nguoiquansat(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_thoibaotaichinh(save_to_db=True, export_csv=False))

    # Export all to CSV
    print("\n" + "="*60)
    print("📁 FINAL EXPORT - main.py:273")
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
        
        print(f"\n{'='*60} - main.py:295")
        print(f"✅ DONE! - main.py:296")
        print(f"{'='*60} - main.py:297")
        print(f"Total articles: {len(all_articles)} - main.py:298")
        print(f"CSV: {csv_path} - main.py:299")
        print(f"JSON: {json_path} - main.py:300")

    return all_articles



def test_mode():
    """Test với một source"""
    print("= - main.py:305"*60)
    print("🧪 TEST MODE  CafeF Only - main.py:306")
    print("= - main.py:307"*60)

    scraper = CafeFScraper()
    scraper.delay = 1  # Faster for testing

    print("\nFetching 3 articles for testing... - main.py:312")
    articles = scraper.fetch_news(max_pages=1, max_articles_per_page=3)
    
    print(f"\n📊 Results: {len(articles)} articles - main.py:315")
    for i, article in enumerate(articles, 1):
        print(f"\n Article {i} - main.py:317")
        print(f"Title: {article[1][:60]}... - main.py:318")
        print(f"Link: {article[2][:60]}... - main.py:319")
        print(f"Published: {datetime.fromtimestamp(article[0]) if article[0] else 'N/A'} - main.py:320")
        print(f"Content: {len(article[3])} chars - main.py:321")
        print(f"Source: {article[4]} - main.py:322")


def show_help():
    """Hiển thị hướng dẫn"""
    print("""
MULTI-SOURCE NEWS SCRAPER
=========================

Usage:
    python main.py                  Scrape tất cả sources (CafeF, Cafeland, VnExpress, VnEconomy, VOV, Vietnamnet)
    python main.py cafef            Chỉ scrape CafeF
    python main.py cafeland         Chỉ scrape Cafeland
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
        elif mode == 'dantri':       
            db.create_tables()
            scrape_dantri()
        elif mode == 'thanhnien':
            db.create_tables()
            scrape_thanhnien()
        elif mode == 'cafeland':
            db.create_tables()
            scrape_cafeland()
        elif mode == 'vnexpress':
            db.create_tables()
            scrape_vnexpress()
        elif mode == 'thoibaonganhang':
            db.create_tables()
            scrape_thoibaonganhang()
        elif mode == 'vneconomy':
            db.create_tables()
            scrape_vneconomy()
        elif mode == 'nguoiquansat':
            db.create_tables()
            scrape_nguoiquansat()
        elif mode == 'taichinhdoanhnghiep':
            db.create_tables()
            scrape_taichinhdoanhnghiep()
        elif mode == 'antt':
            db.create_tables()
            scrape_antt()
        elif mode == 'baochinhphu':
            db.create_tables()
            scrape_baochinhphu()
        elif mode == 'tinnhanhchungkhoan':
            db.create_tables()
            scrape_tinnhanhchungkhoan()
        elif mode == 'qdnd':
            db.create_tables()
            scrape_qdnd()
        elif mode == 'thoibaotaichinh':
            db.create_tables()
            scrape_thoibaotaichinh()
        elif mode == 'tuoitre':
            db.create_tables()
            scrape_tuoitre()
        elif mode == 'vov':
            db.create_tables()
            scrape_vov()
        elif mode == 'kinhte':
            db.create_tables()
            scrape_kinhte()
        elif mode == 'vietnamnet':
            db.create_tables()
            scrape_vietnamnet()
        elif mode == 'laodong':
            db.create_tables()
            scrape_laodong()
        # elif mode == 'agromonitor':
        #     db.create_tables()
        #     scrape_agromonitor()
        elif mode == 'cna':
            db.create_tables()
            scrape_cna()
        elif mode == 'nld':
            db.create_tables()
            scrape_nld()
        elif mode == 'vietstock':
            db.create_tables()
            scrape_vietstock()
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
