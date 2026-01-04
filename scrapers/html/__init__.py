"""
HTML-based News Scrapers
"""

from scrapers.html.vnexpress import VnExpressScraper
from scrapers.html.vov import VOVScraper
from scrapers.html.vietnamnet import VietnametScraper
from scrapers.html.cafeland import CafelandScraper
from scrapers.html.cafef import CafeFScraper
from scrapers.html.nld import NLDScraper
from scrapers.html.laodong import LaoDongScraper
from scrapers.html.kinhtengaithuong import KinhTeNgoaiThuongScraper
from scrapers.html.thoibaonganhang import ThoiBaoNganHangScraper
from scrapers.html.taichinhdoanhnghiep import TaiChinhDoanhNghiepScraper
from scrapers.html.baochinhphu import BaoChinhPhuScraper
from scrapers.html.tinnhanhchungkhoan import TinNhanhChungKhoanScraper
from scrapers.html.nguoiquansat import NguoiQuanSatScraper
from scrapers.html.thoibaotaichinh import ThoiBaoTaiChinhScraper
from scrapers.html.coin68 import Coin68Scraper
from scrapers.html.vietnamfinance import VietnamFinanceScraper
from scrapers.html.xaydungchinhsach import XaydungChinhsachScraper

__all__ = [
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
]
