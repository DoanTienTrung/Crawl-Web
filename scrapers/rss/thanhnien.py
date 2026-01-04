from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import feedparser
import re


class ThanhNienRSSScraper(NewsScraperBase):
    """
    Scraper cho ThanhNien.vn sử dụng RSS Feed
    """

    def __init__(self):
        super().__init__()
        self.source = "thanhnien.vn"
        self.rss_url = "https://thanhnien.vn/rss/home.rss"

    def fetch_news(self) -> List[Tuple]:
        """
        Lấy tối đa 20 tin tức mới nhất từ RSS feed của Thanh Niên
        """
        all_articles = []
        print(f"\n📡 Đang đọc RSS từ: {self.rss_url}")

        feed = feedparser.parse(self.rss_url)

        if not feed.entries:
            print("⚠ Không tìm thấy bài viết nào trong RSS Thanh Niên.")
            return []

        entries_to_process = feed.entries[:20]
        print(f"Thanh Niên: Tìm thấy {len(feed.entries)} bài. Sẽ xử lý {len(entries_to_process)} bài.")

        for entry in entries_to_process:
            link = entry.link

            print(f"Fetching: {link[:60]}...")
            self.sleep()

            # RSS feed doesn't include category, extract from article page
            article_data = self._fetch_article_detail(link)
            if article_data:
                all_articles.append(article_data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo từ Thanh Niên"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        title_el = soup.select_one('h1.detail-title') or soup.select_one('.detail-title') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''

        if not title:
            return None

        # Format: dd/mm/yyyy HH:MM
        published_at = 0
        date_el = soup.select_one('.detail-time') or soup.select_one('.detail-time span')
        if date_el:
            date_text = date_el.get_text(strip=True)
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})', date_text)
            if date_match:
                day, month, year, hour, minute = date_match.groups()
                try:
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    published_at = int(dt.timestamp())
                except: pass

        content = ""
        content_el = soup.select_one('#abb-content') or soup.select_one('.detail-content') or soup.select_one('[itemprop="articleBody"]')
        if content_el:
            # Remove unwanted elements
            for unwanted in content_el.select('.morenews, .display-ads, .video-content-wrapper, .banner-ads'):
                unwanted.decompose()

            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        category = "TIN TỨC"

        # Priority 1: Meta tag article:section
        meta_cate = soup.find('meta', property='article:section')
        if meta_cate and meta_cate.get('content'):
            category = meta_cate.get('content').strip()
        else:
            # Priority 2: Extract from URL path
            try:
                path_parts = link.replace('https://thanhnien.vn/', '').split('/')
                if len(path_parts) > 1:
                    category = path_parts[0].replace('-', ' ')
            except: pass

        category = category.upper().strip()

        return (
            published_at,
            title,
            link,
            content,
            self.source,
            "NA",   # stock_related
            "NA",   # sentiment_score
            False,  # server_pushed
            category,
        )
