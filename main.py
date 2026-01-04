import sys
import os
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers import (
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
    CNARSSScraper,
    QDNDRSSScraper,
    KinhTeNgoaiThuongScraper,
    ThoiBaoNganHangScraper,
    TaiChinhDoanhNghiepScraper,
    BaoChinhPhuScraper,
    TinNhanhChungKhoanScraper,
    NguoiQuanSatScraper,
    ThoiBaoTaiChinhScraper,
    Coin68Scraper,
    VietnamFinanceScraper,
    XaydungChinhsachScraper,
)
from database.models import db
from utils.exporters import export_to_csv, export_to_json

def scrape_xaydungchinhsach(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Xây dựng chính sách - Cổng thông tin Chính phủ"""
    print("\n" + "="*60)
    print("🏛️  XÂY DỰNG CHÍNH SÁCH")
    print("="*60)
    
    scraper = XaydungChinhsachScraper()
    articles = scraper.fetch_news(max_articles=10)
    
    if articles:
        _save_and_export(articles, "xaydungchinhsach", save_to_db, export_csv)
    else:
        print("⚠ Không lấy được dữ liệu từ Xây dựng chính sách.")
        
    return articles

def scrape_vietnamfinance(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VietnamFinance - Tin tức tài chính, đầu tư (Trang chủ)"""
    print("\n" + "="*60)
    print("📰  VIETNAMFINANCE (VIETNAMFINANCE.VN)")
    print("="*60)

    scraper = VietnamFinanceScraper()
    articles = scraper.fetch_news(max_articles=15)

    if articles:
        _save_and_export(articles, "vietnamfinance", save_to_db, export_csv)
    else:
        print("⚠ Không tìm thấy bài viết mới nào từ VietnamFinance (hoặc bài đã tồn tại).")

    return articles

def scrape_coin68(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Coin68 - Tin tức thị trường Tiền mã hóa (Mục Hot News)"""
    print("\n" + "="*60)
    print("🪙  COIN68 (COIN68.COM)")
    print("="*60)

    scraper = Coin68Scraper()
    articles = scraper.fetch_news(max_articles=10)

    if articles:
        _save_and_export(articles, "coin68", save_to_db, export_csv)
    else:
        print("⚠ Không tìm thấy bài viết mới nào từ Coin68.")

    return articles

def scrape_nguoiquansat(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Người Quan Sát với cấu trúc mới"""
    print("\n" + "="*60)
    print("📈 NGƯỜI QUAN SÁT (NGUOIQUANSAT.VN)")
    print("="*60)

    scraper = NguoiQuanSatScraper()
    articles = scraper.fetch_news(max_articles=10)

    _save_and_export(articles, "nguoiquansat", save_to_db, export_csv)
    return articles

def scrape_thoibaotaichinh(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Thời báo Tài chính Việt Nam (thoibaotaichinhvietnam.vn)"""
    print("\n" + "="*60)
    print("📈 THỜI BÁO TÀI CHÍNH (THOIBAOTAICHINHVN.VN)")
    print("="*60)

    scraper = ThoiBaoTaiChinhScraper()
    articles = scraper.fetch_news(max_articles=10)

    _save_and_export(articles, "thoibaotaichinh", save_to_db, export_csv)

    return articles


def scrape_taichinhdoanhnghiep(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Hàm điều phối quét tin từ Tài chính Doanh nghiệp (taichinhdoanhnghiep.net.vn)"""
    print("\n" + "="*60)
    print("💼 TÀI CHÍNH DOANH NGHIỆP SCRAPER")
    print("="*60)

    scraper = TaiChinhDoanhNghiepScraper()

    try:
        articles = scraper.fetch_news(max_articles=15)
    except Exception as e:
        print(f"❌ Lỗi khi quét tin: {str(e)}")
        return []

    if articles:
        print(f"✨ Đã thu thập tổng cộng {len(articles)} bài viết hợp lệ.")

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
    articles = scraper.fetch_news()
    
    _save_and_export(articles, "qdnd", save_to_db, export_csv)
    return articles


def scrape_cafef(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape CafeF"""
    print("\n" + "="*60)
    print("🔵 CAFEF.VN SCRAPER")
    print("="*60)

    scraper = CafeFScraper()
    articles = scraper.fetch_news(max_pages=1, max_articles_per_page=20)

    _save_and_export(articles, "cafef", save_to_db, export_csv)
    return articles


def scrape_cafeland(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Cafeland"""
    print("\n" + "="*60)
    print("🟠 CAFELAND.VN SCRAPER ")
    print("="*60)

    scraper = CafelandScraper()
    articles = scraper.fetch_news(max_pages=1, max_articles_per_page=20)

    _save_and_export(articles, "cafeland", save_to_db, export_csv)
    return articles


def scrape_vnexpress(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VnExpress"""
    print("\n" + "="*60)
    print("🟢 VNEXPRESS.NET SCRAPER ")
    print("="*60)

    scraper = VnExpressScraper()
    articles = scraper.fetch_news(max_pages=1)

    _save_and_export(articles, "vnexpress", save_to_db, export_csv)
    return articles


def scrape_tuoitre(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape TuoiTre sử dụng RSS"""
    print("\n" + "="*60)
    print("🟢 TUOITRE.VN RSS SCRAPER")
    print("="*60)

    scraper = TuoiTreRSSScraper()
    articles = scraper.fetch_news()

    _save_and_export(articles, "tuoitre", save_to_db, export_csv)
    return articles


def scrape_vneconomy(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VnEconomy using RSS feed"""
    print("\n" + "="*60)
    print("🟡 VNECONOMY.VN ")
    print("="*60)

    scraper = VnEconomyScraper()
    articles = scraper.fetch_news(max_articles=20)

    if not articles:
        print(f"⚠ No articles scraped from vneconomy! ")
        return []

    _save_and_export(articles, "vneconomy", save_to_db, export_csv)
    return articles


def scrape_vov(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape VOV"""
    print("\n" + "="*60)
    print("🔴 VOV.VN SCRAPER")
    print("="*60)

    scraper = VOVScraper()
    articles = scraper.fetch_news(max_pages=1)

    _save_and_export(articles, "vov", save_to_db, export_csv)
    return articles

def scrape_cna(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Channel NewsAsia (CNA) sử dụng RSS Feed"""
    print("\n" + "="*60)
    print("🔴 CHANNEL NEWSASIA (CNA)")
    print("="*60)

    scraper = CNARSSScraper()
    articles = scraper.fetch_news()

    _save_and_export(articles, "cna", save_to_db, export_csv)

    return articles


def scrape_vietnamnet(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape Vietnamnet"""
    print("\n" + "="*60)
    print("🟣 VIETNAMNET.VN SCRAPER ")
    print("="*60)

    scraper = VietnametScraper()
    articles = scraper.fetch_news()

    _save_and_export(articles, "vietnamnet", save_to_db, export_csv)
    return articles


def scrape_dantri(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape DanTri sử dụng RSS"""
    print("\n" + "="*60)
    print("🔴 DANTRI.COM.VN RSS SCRAPER")
    print("="*60)

    scraper = DanTriRSSScraper()
    articles = scraper.fetch_news()

    _save_and_export(articles, "dantri", save_to_db, export_csv)
    return articles


def scrape_thanhnien(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape ThanhNien sử dụng RSS"""
    print("\n" + "="*60)
    print("🔵 THANHNIEN.VN RSS SCRAPER")
    print("="*60)

    scraper = ThanhNienRSSScraper()
    articles = scraper.fetch_news()

    _save_and_export(articles, "thanhnien", save_to_db, export_csv)

    return articles


def scrape_laodong(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape LaoDong"""
    print("\n" + "="*60)
    print("🟡 LAODONG.VN SCRAPER")
    print("="*60)

    scraper = LaoDongScraper()
    articles = scraper.fetch_news(max_articles=20)

    _save_and_export(articles, "laodong", save_to_db, export_csv)

    return articles


def scrape_nld(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape NLD (Người Lao Động)"""
    print("\n" + "="*60)
    print("🔵 NLD.COM.VN SCRAPER")
    print("="*60)

    scraper = NLDScraper()
    articles = scraper.fetch_news(max_articles=20)

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
    articles = scraper.fetch_news(max_articles=15)

    _save_and_export(articles, "vietstock", save_to_db, export_csv)

    return articles

def scrape_antt(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Scrape ANTT.vn sử dụng RSS"""
    print("\n" + "="*60)
    print("🟠 ANTT.VN RSS SCRAPER")
    print("=" * 60)

    scraper = ANTTRSSScraper()
    articles = scraper.fetch_news()

    _save_and_export(articles, "antt", save_to_db, export_csv)
    return articles

def scrape_thoibaonganhang(save_to_db: bool = True, export_csv: bool = True) -> list:
    """Hàm điều phối Scraper cho Thời báo Ngân hàng (thoibaonganhang.vn)"""
    print("\n" + "="*60)
    print("🏦 THỜI BÁO NGÂN HÀNG (TBNH) SCRAPER")
    print("="*60)

    scraper = ThoiBaoNganHangScraper()
    articles = scraper.fetch_news(max_articles=15)

    if articles:
        _save_and_export(articles, "thoibaonganhang", save_to_db, export_csv)
    else:
        print("\n⚠ No articles scraped from thoibaonganhang!")

    return articles

def _save_and_export(articles: list, source_name: str, save_to_db: bool, export_csv: bool):
    """Helper function để save và export"""
    if not articles:
        print(f"\n⚠ No articles scraped from {source_name}!")
        return

    print(f"\n📊 Total articles scraped: {len(articles)}")

    if save_to_db:
        print("\n💾 Saving to database...")
        saved_count = 0
        for article in articles:
            # article tuple: (published_at, title, link, content, source, stock_related, sentiment_score, server_pushed, category)
            if len(article) == 9:
                data = article[:8]
                category = article[8]
                if db.insert_news_with_category(data, category):
                    saved_count += 1
            else:
                if db.insert_news(article):
                    saved_count += 1

        print(f"✓ Saved {saved_count}/{len(articles)} articles to database")

    if export_csv:
        print("\n📁 Exporting to CSV...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
        print(f"✓ Exported to: {csv_path}")


def scrape_all():
    """Scrape tất cả các nguồn"""
    print("\n" + "="*60)
    print("🚀 MULTISOURCE NEWS SCRAPER ")
    print("="*60)

    print("\n[1] Setting up database... ")
    try:
        db.create_tables()
    except Exception as e:
        print(f"⚠ Database warning: {e} ")
        print("Will export to CSV only... ")

    all_articles = []

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
    all_articles.extend(scrape_cna(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_qdnd(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_kinhte(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_thoibaonganhang(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_taichinhdoanhnghiep(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_baochinhphu(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_tinnhanhchungkhoan(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_nguoiquansat(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_thoibaotaichinh(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_coin68(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_vietnamfinance(save_to_db=True, export_csv=False))
    all_articles.extend(scrape_xaydungchinhsach(save_to_db=True, export_csv=False))

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

    return all_articles


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
        elif mode == 'vietnamfinance':
            db.create_tables()
            scrape_vietnamfinance()
        elif mode == 'vnexpress':
            db.create_tables()
            scrape_vnexpress()
        elif mode == 'thoibaonganhang':
            db.create_tables()
            scrape_thoibaonganhang()
        elif mode == 'coin68':
            db.create_tables()
            scrape_coin68()
        elif mode == 'vneconomy':
            db.create_tables()
            scrape_vneconomy()
        elif mode == 'xaydungchinhsach':
            db.create_tables()
            scrape_xaydungchinhsach()
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
        elif mode == 'cna':
            db.create_tables()
            scrape_cna()
        elif mode == 'nld':
            db.create_tables()
            scrape_nld()
        elif mode == 'vietstock':
            db.create_tables()
            scrape_vietstock()
        else:
            scrape_all()

    except KeyboardInterrupt:
        print("\n\n⚠ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
