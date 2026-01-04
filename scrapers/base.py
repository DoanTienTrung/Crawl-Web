
import requests
from datetime import datetime
import time
from typing import Optional
import gzip
import brotli


class NewsScraperBase:
    """Base class cho tất cả news scrapers"""

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-IN,en-US;q=0.9,en;q=0.8,vi;q=0.7',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }
        self.delay = 2  # Delay giữa các request (giây)

    def fetch_html(self, url: str) -> Optional[str]:
        """Fetch và decode HTML từ URL"""
        try:
            resp = self.session.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()

            # Handle content encoding
            content_encoding = resp.headers.get('Content-Encoding', '')

            if 'br' in content_encoding:
                try:
                    return brotli.decompress(resp.content).decode('utf-8')
                except:
                    pass

            if 'gzip' in content_encoding:
                try:
                    return gzip.decompress(resp.content).decode('utf-8')
                except:
                    pass

            return resp.text

        except Exception as e:
            print(f"✗ Error fetching {url}: {e} - multi_source_scraper.py:54")
            return None

    def parse_date_to_timestamp(self, date_str: str, format_str: str) -> int:
        """Parse date string thành Unix timestamp"""
        try:
            dt = datetime.strptime(date_str.strip(), format_str)
            return int(dt.timestamp())
        except Exception as e:
            print(f"⚠ Could not parse date '{date_str}': {e} - multi_source_scraper.py:63")
            return 0

    def sleep(self):
        """Delay giữa các request"""
        time.sleep(self.delay)
