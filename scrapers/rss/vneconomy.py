from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
import feedparser
from datetime import datetime
import html
from bs4 import BeautifulSoup


class VnEconomyScraper(NewsScraperBase):
    """Scraper cho VnEconomy.vn sử dụng RSS Feed"""

    def __init__(self):
        super().__init__()
        self.source = "vneconomy.vn"
        self.rss_url = "https://vneconomy.vn/tin-moi.rss"

    def fetch_news(self, max_articles: int = 20) -> List[Tuple]:
        """Fetch tin tức từ VnEconomy qua RSS"""
        all_articles = []

        print(f"\n📰 Fetching VnEconomy RSS: {self.rss_url}")

        feed = feedparser.parse(self.rss_url)

        if not feed.entries:
            print("⚠ Không tìm thấy bài viết nào trong RSS feed.")
            return []

        entries = feed.entries[:max_articles]
        print(f"✓ Tìm thấy {len(entries)} bài viết từ RSS.")

        for entry in entries:
            try:
                title = entry.title
                link = entry.link

                # pubDate format: Fri, 02 Jan 2026 09:06:03 GMT
                published_at = int(datetime.now().timestamp())
                if hasattr(entry, 'published_parsed'):
                    published_at = int(datetime(*entry.published_parsed[:6]).timestamp())

                # Ưu tiên content:encoded vì nó đầy đủ nhất
                content = ""
                if hasattr(entry, 'content'):
                    raw_content = entry.content[0].value
                    content = self._clean_rss_content(raw_content)
                elif hasattr(entry, 'description'):
                    content = self._clean_rss_content(entry.description)

                category = "TIN MỚI"
                if hasattr(entry, 'category'):
                    category = entry.category.upper()

                author = "NA"
                if hasattr(entry, 'author'):
                    author = entry.author

                article_data = (
                    published_at,
                    title,
                    link,
                    content,
                    self.source,
                    author,
                    "NA",
                    False,
                    category,
                )
                all_articles.append(article_data)

            except Exception as e:
                print(f"✗ Lỗi khi xử lý item RSS: {e}")
                continue

        print(f"✓ Đã xử lý xong {len(all_articles)} bài viết.")
        return all_articles

    def _clean_rss_content(self, raw_html: str) -> str:
        """Làm sạch HTML trong nội dung RSS"""
        if not raw_html:
            return ""

        # Decode HTML entities: &#237; -> í
        decoded_html = html.unescape(raw_html)

        soup = BeautifulSoup(decoded_html, 'html.parser')

        # VnEconomy thường để tóm tắt trong thẻ <h2>, lấy cả <h2> và <p>
        text_parts = []
        for tag in soup.find_all(['h2', 'p']):
            txt = tag.get_text(strip=True)
            if txt:
                text_parts.append(txt)

        cleaned_text = " ".join(text_parts)

        # Fallback: nếu không tìm thấy h2/p thì lấy toàn bộ text
        if not cleaned_text:
            cleaned_text = soup.get_text(" ", strip=True)

        return cleaned_text
