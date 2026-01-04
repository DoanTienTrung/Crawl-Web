"""
News Scrapers Package - Organized by scraper type
"""

from scrapers.base import NewsScraperBase

# Import from RSS scrapers
from scrapers.rss import (
    VnEconomyScraper,
    DanTriRSSScraper,
    ThanhNienRSSScraper,
    TuoiTreRSSScraper,
    ANTTRSSScraper,
    CNARSSScraper,
    QDNDRSSScraper,
)

# Import from HTML scrapers
from scrapers.html import (
    VnExpressScraper,
    VOVScraper,
    VietnametScraper,
    CafelandScraper,
    CafeFScraper,
    NLDScraper,
    LaoDongScraper,
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

# Import from Selenium scrapers
from scrapers.selenium import (
    VietStockScraper,
)

__all__ = [
    'NewsScraperBase',
    # RSS Scrapers
    'VnEconomyScraper',
    'DanTriRSSScraper',
    'ThanhNienRSSScraper',
    'TuoiTreRSSScraper',
    'ANTTRSSScraper',
    'CNARSSScraper',
    'QDNDRSSScraper',
    # HTML Scrapers
    'VnExpressScraper',
    'VOVScraper',
    'VietnametScraper',
    'CafelandScraper',
    'CafeFScraper',
    'NLDScraper',
    'LaoDongScraper',
    'KinhTeNgoaiThuongScraper',
    'ThoiBaoNganHangScraper',
    'TaiChinhDoanhNghiepScraper',
    'BaoChinhPhuScraper',
    'TinNhanhChungKhoanScraper',
    'NguoiQuanSatScraper',
    'ThoiBaoTaiChinhScraper',
    'Coin68Scraper',
    'VietnamFinanceScraper',
    'XaydungChinhsachScraper',
    # Selenium Scrapers
    'VietStockScraper',
    # Registry
    'SCRAPERS',
]

# Registry - để dễ sử dụng
SCRAPERS = {
    # RSS Scrapers
    'vneconomy': VnEconomyScraper,
    'dantri': DanTriRSSScraper,
    'thanhnien': ThanhNienRSSScraper,
    'tuoitre': TuoiTreRSSScraper,
    'antt': ANTTRSSScraper,
    'cna': CNARSSScraper,
    'qdnd': QDNDRSSScraper,
    # HTML Scrapers
    'vnexpress': VnExpressScraper,
    'vov': VOVScraper,
    'vietnamnet': VietnametScraper,
    'cafeland': CafelandScraper,
    'cafef': CafeFScraper,
    'nld': NLDScraper,
    'laodong': LaoDongScraper,
    'kinhtengaithuong': KinhTeNgoaiThuongScraper,
    'thoibaonganhang': ThoiBaoNganHangScraper,
    'taichinhdoanhnghiep': TaiChinhDoanhNghiepScraper,
    'baochinhphu': BaoChinhPhuScraper,
    'tinnhanhchungkhoan': TinNhanhChungKhoanScraper,
    'nguoiquansat': NguoiQuanSatScraper,
    'thoibaotaichinh': ThoiBaoTaiChinhScraper,
    'coin68': Coin68Scraper,
    'vietnamfinance': VietnamFinanceScraper,
    'xaydungchinhsach': XaydungChinhsachScraper,
    # Selenium Scrapers
    'vietstock': VietStockScraper,
}
