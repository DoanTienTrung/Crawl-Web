from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import feedparser
import re


class DanTriRSSScraper(NewsScraperBase):
    """
    Scraper cho DanTri.com.vn sử dụng RSS Feed
    """

    def __init__(self):
        super().__init__()
        self.source = "dantri.com.vn"
        self.rss_url = "https://dantri.com.vn/rss/tin-moi-nhat.rss"

    def fetch_news(self) -> List[Tuple]:
        """
        Lấy tối đa 20 tin tức mới nhất từ RSS feed của Dân trí
        """
        all_articles = []
        print(f"\n📡 Đang đọc RSS từ: {self.rss_url} - multi_source_scraper.py:1084")

        # 1. Sử dụng feedparser để đọc nội dung RSS
        feed = feedparser.parse(self.rss_url)

        if not feed.entries:
            print("⚠ Không tìm thấy bài viết nào trong RSS. - multi_source_scraper.py:1090")
            return []

        # 2. Giới hạn chỉ xử lý 20 bài viết đầu tiên
        entries_to_process = feed.entries[:20]
        print(f"Tìm thấy {len(feed.entries)} bài. Sẽ xử lý {len(entries_to_process)} bài mới nhất. - multi_source_scraper.py:1095")

        for entry in entries_to_process:
            link = entry.link

            # Lấy Category trực tiếp từ thẻ <category> của RSS để đảm bảo độ chính xác (ví dụ: Chính trị)
            rss_category = getattr(entry, 'category', 'TIN MỚI')

            print(f"Fetching: {link[:60]}... - multi_source_scraper.py:1103")
            self.sleep()

            # Truyền rss_category vào hàm detail để xử lý
            article_data = self._fetch_article_detail(link, rss_category)
            if article_data:
                all_articles.append(article_data)

        print(f"\n✓ Tổng số bài viết thu thập được: {len(all_articles)} - multi_source_scraper.py:1111")
        return all_articles

    def _fetch_article_detail(self, link: str, rss_category: str = None) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo từ Dân trí"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 1. Trích xuất Tiêu đề
        title_el = soup.select_one('h1.title-page') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''

        if not title:
            return None

        # 2. Trích xuất Ngày xuất bản
        published_at = 0
        date_el = soup.select_one('.author-time')
        if date_el:
            date_text = date_el.get_text(strip=True)
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s*-\s*(\d{1,2}):(\d{2})', date_text)
            if date_match:
                day, month, year, hour, minute = date_match.groups()
                try:
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    published_at = int(dt.timestamp())
                except:
                    pass

        # 3. Trích xuất Nội dung
        content = ""
        content_el = soup.select_one('.singular-content')
        if content_el:
            # Loại bỏ quảng cáo và video liên quan
            for unwanted in content_el.select('.gui-check-parent, .video-content-wrapper, .ad-container'):
                unwanted.decompose()

            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # 4. Trích xuất Chuyên mục (Ưu tiên từ RSS)
        if rss_category and rss_category != "TIN MỚI":
            category = rss_category
        else:
            # Dự phòng lấy từ Meta Tag nếu RSS thiếu
            meta_cate = soup.find('meta', property='article:section')
            category = meta_cate.get('content') if meta_cate else "TIN MỚI"

        category = category.upper().strip()

        return (
            published_at,
            title,
            link,
            content,
            self.source,
            "NA",   
            "NA",  
            False,  
            category,
        )
