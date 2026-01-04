from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import feedparser
import re


class ANTTRSSScraper(NewsScraperBase):
    """
    Scraper cho ANTT.vn sử dụng RSS Feed
    """

    def __init__(self):
        super().__init__()
        self.source = "antt.vn"
        self.rss_url = "https://antt.vn/rss/trang-chu.rss"

    def fetch_news(self) -> List[Tuple]:
        """
        Lấy tối đa 20 tin tức mới nhất từ RSS feed của ANTT
        """
        all_articles = []
        print(f"\n📡 Đang đọc RSS từ: {self.rss_url}")

        feed = feedparser.parse(self.rss_url)

        if not feed.entries:
            print("⚠ Không tìm thấy bài viết nào trong RSS.")
            return []

        entries_to_process = feed.entries[:20]
        print(f"Tìm thấy {len(feed.entries)} bài. Sẽ xử lý {len(entries_to_process)} bài mới nhất.")

        for entry in entries_to_process:
            link = entry.link

            # RSS của ANTT thường không có thẻ <category> trực tiếp cho từng entry như Dân Trí
            # Ta sẽ mặc định là 'TIN MỚI' và để hàm detail lấy từ Meta Tag
            rss_category = getattr(entry, 'category', 'TIN MỚI')

            print(f"Fetching: {link[:60]}...")
            self.sleep() # Đảm bảo không crawl quá nhanh

            article_data = self._fetch_article_detail(link, rss_category)
            if article_data:
                all_articles.append(article_data)

        print(f"\n✓ Tổng số bài viết từ ANTT thu thập được: {len(all_articles)}")
        return all_articles

    def _fetch_article_detail(self, link: str, rss_category: str = None) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo từ ANTT"""
        # Fix: ANTT RSS trả về URLs dạng "-nXXXXXX.html" nhưng website dùng "-XXXXXX.htm"
        # Cần bỏ chữ 'n' trước số và đổi extension
        import re
        original_link = link
        if link.endswith('.html'):
            # Thay -nXXXXXX.html thành -XXXXXX.htm
            link = re.sub(r'-n(\d+)\.html$', r'-\1.htm', link)
        elif link.endswith('.htm'):
            # Nếu đã là .htm nhưng vẫn có 'n', thì bỏ 'n'
            link = re.sub(r'-n(\d+)\.htm$', r'-\1.htm', link)

        if link != original_link:
            print(f"  → URL fixed: ...{original_link[-50:]} → ...{link[-50:]}")

        # ANTT server trả về encoding sai (ISO-8859-1) nhưng content là UTF-8
        # Cần fetch với explicit UTF-8 encoding
        try:
            resp = self.session.get(link, headers=self.headers, timeout=30)
            resp.raise_for_status()
            # Force UTF-8 decoding
            html = resp.content.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"✗ Error fetching {link}: {e}")
            return None

        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 1. Trích xuất Tiêu đề (ANTT dùng div.title_detail)
        title_el = soup.select_one('.title_detail') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''

        if not title:
            print(f"  ⚠ No title found for {link[-60:]}")
            return None

        # 2. Trích xuất Ngày xuất bản
        # ANTT dùng format: "02/01/2026 11:02:40"
        published_at = 0
        date_el = soup.select_one('.time_home')
        if date_el:
            date_text = date_el.get_text(strip=True)
            # Format: dd/mm/yyyy hh:mm:ss
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})', date_text)
            if date_match:
                day, month, year, hour, minute, second = date_match.groups()
                try:
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                    published_at = int(dt.timestamp())
                except:
                    pass

        # 3. Trích xuất Nội dung
        content = ""
        # ANTT: content nằm trong các thẻ p trực tiếp trong content_main
        content_el = soup.select_one('.content_main')
        if content_el:
            # Loại bỏ các thành phần không cần thiết
            for unwanted in content_el.select('.related-box, .ad-container, script, style, .tag_detail, .article-footer'):
                unwanted.decompose()

            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # 4. Trích xuất Chuyên mục
        # ANTT: category nằm trong breadcrumb (item thứ 2)
        category = "TIN MỚI"

        # Tìm breadcrumb items
        breadcrumb_items = soup.select('a[itemprop="url"] span[itemprop="title"]')

        # Lấy item thứ 2 (index 1) - đó là category chính
        # Item 1: Trang chủ, Item 2: Category, Item 3: Sub-category
        if len(breadcrumb_items) >= 2:
            category = breadcrumb_items[1].get_text(strip=True)

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
