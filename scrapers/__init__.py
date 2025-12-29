"""
Scrapers package for news-scraper project.

All scraper implementations are in multi_source_scraper.py
"""

from .multi_source_scraper import (
    CafeFScraper,
    VnExpressScraper,
    VnEconomyScraper,
    VOVScraper,
    VietnametScraper,
)

__all__ = [
    'CafeFScraper',
    'VnExpressScraper',
    'VnEconomyScraper',
    'VOVScraper',
    'VietnametScraper',
]
