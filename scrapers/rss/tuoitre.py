from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import feedparser
import re


class TuoiTreRSSScraper(NewsScraperBase):
    """
    Scraper cho TuoiTre.vn sử dụng RSS Feed
    """

    def __init__(self):
        super().__init__()
        self.source = "tuoitre.vn"
        self.rss_url = "https://tuoitre.vn/rss/tin-moi-nhat.rss"

    def fetch_news(self) -> List[Tuple]:
        """Lấy 20 tin mới nhất từ Tuổi Trẻ"""
        all_articles = []
        print(f"\n📡 Đang đọc RSS từ: {self.rss_url}")

        feed = feedparser.parse(self.rss_url)
        if not feed.entries:
            return []

        entries_to_process = feed.entries[:20]
        for entry in entries_to_process:
            link = entry.link
            self.sleep()
            article_data = self._fetch_article_detail(link)
            if article_data:
                all_articles.append(article_data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        title_el = soup.select_one('.detail-title') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''
        if not title: return None

        # Format: dd/mm/yyyy HH:mm GMT+7
        published_at = 0
        date_el = soup.select_one('.detail-time') or soup.find('meta', property='article:published_time')
        if date_el:
            date_text = date_el.get_text(strip=True) if not date_el.get('content') else date_el.get('content')
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})', date_text)
            if date_match:
                day, month, year, hour, minute = date_match.groups()
                try:
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    published_at = int(dt.timestamp())
                except: pass

        content = ""
        content_el = soup.select_one('.fck') or soup.select_one('.detail-content')
        if content_el:
            # Remove video, related news, ads
            for unwanted in content_el.select('.vnn-title, .box-tin-lien-quan, .ad-container'):
                unwanted.decompose()
            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        category = "TIN MỚI"
        meta_cate = soup.find('meta', property='article:section')
        if meta_cate:
            category = meta_cate.get('content').upper().strip()

        return (
            published_at, title, link, content, self.source,
            "NA", "NA", False, category,
        )
