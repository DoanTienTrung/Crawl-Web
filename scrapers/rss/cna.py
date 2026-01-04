from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import feedparser


class CNARSSScraper(NewsScraperBase):
    """
    Scraper cho ChannelNewsAsia.com sử dụng RSS Feed
    """

    def __init__(self):
        super().__init__()
        self.source = "channelnewsasia.com"
        # Link RSS chính thức của CNA
        self.rss_url = "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml"

    def fetch_news(self) -> List[Tuple]:
        """
        Lấy tối đa 20 tin tức mới nhất từ RSS feed của CNA
        """
        all_articles = []
        print(f"\n📡 Đang đọc RSS từ: {self.rss_url}")

        # 1. Sử dụng feedparser để đọc nội dung RSS
        feed = feedparser.parse(self.rss_url)

        if not feed.entries:
            print("⚠ Không tìm thấy bài viết nào trong RSS.")
            return []

        # 2. Giới hạn 20 bài viết đầu tiên
        entries_to_process = feed.entries[:20]
        print(f"Tìm thấy {len(feed.entries)} bài. Sẽ xử lý {len(entries_to_process)} bài mới nhất.")

        for entry in entries_to_process:
            link = entry.link

            # Lấy Category (CNA thường để trong tags hoặc category field của RSS)
            rss_category = "WORLD" # Mặc định cho CNA
            if hasattr(entry, 'tags'):
                rss_category = entry.tags[0].term if entry.tags else "ASIA"

            # Lấy timestamp trực tiếp từ RSS (CNA hỗ trợ cực tốt phần này)
            published_at = 0
            if hasattr(entry, 'published_parsed'):
                published_at = int(datetime(*entry.published_parsed[:6]).timestamp())

            print(f"Fetching: {link[:60]}...")
            self.sleep()

            # Truyền các thông tin đã có vào hàm detail
            article_data = self._fetch_article_detail(link, rss_category, published_at)
            if article_data:
                all_articles.append(article_data)

        print(f"\n✓ Tổng số bài viết CNA thu thập được: {len(all_articles)}")
        return all_articles

    def _fetch_article_detail(self, link: str, rss_category: str = None, rss_published_at: int = 0) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo từ CNA"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 1. Trích xuất Tiêu đề (CNA thường dùng class h1.entry-title hoặc class liên quan đến content)
        title_el = soup.select_one('h1.page-title') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''

        if not title:
            return None

        # 2. Trích xuất Ngày xuất bản (Ưu tiên lấy từ RSS đã có ở bước trước)
        published_at = rss_published_at

        # 3. Trích xuất Nội dung
        content = ""
        # Selector cho nội dung bài viết của CNA (thường là div chứa text-long hoặc các thẻ p trong article)
        content_el = soup.select_one('.content-wrapper') or soup.select_one('.text-long')
        if content_el:
            # Loại bỏ các thành phần rác như "Also read", Video player, Ads
            for unwanted in content_el.select('.related-section, .video-embed, .ad-slot, .infographic'):
                unwanted.decompose()

            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # 4. Trích xuất Chuyên mục
        category = rss_category if rss_category else "WORLD"
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
