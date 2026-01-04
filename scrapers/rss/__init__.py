"""
RSS-based News Scrapers
"""

from scrapers.rss.vneconomy import VnEconomyScraper
from scrapers.rss.dantri import DanTriRSSScraper
from scrapers.rss.thanhnien import ThanhNienRSSScraper
from scrapers.rss.tuoitre import TuoiTreRSSScraper
from scrapers.rss.antt import ANTTRSSScraper
from scrapers.rss.cna import CNARSSScraper
from scrapers.rss.qdnd import QDNDRSSScraper

__all__ = [
    'VnEconomyScraper',
    'DanTriRSSScraper',
    'ThanhNienRSSScraper',
    'TuoiTreRSSScraper',
    'ANTTRSSScraper',
    'CNARSSScraper',
    'QDNDRSSScraper',
]
