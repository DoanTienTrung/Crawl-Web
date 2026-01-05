from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import feedparser
import re


class QDNDRSSScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "qdnd.vn"
        self.rss_url = "https://www.qdnd.vn/rss/cate/tin-tuc-moi-nhat.rss"

    def fetch_news(self, max_articles: int = 10) -> List[Tuple]:
        all_articles = []

        print(f"\n📡 Đang đọc RSS từ: {self.rss_url}")

        # 1. Fetch RSS với requests (vì feedparser trực tiếp bị chặn bởi redirect)
        try:
            import requests
            response = requests.get(self.rss_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            # Parse RSS content bằng feedparser
            feed = feedparser.parse(response.text)
        except Exception as e:
            print(f"⚠ Lỗi khi fetch RSS: {e}")
            return []

        if not feed.entries:
            print("⚠ Không thể lấy dữ liệu từ RSS.")
            return []

        # 2. Lấy danh sách các link bài viết
        article_links = []
        for entry in feed.entries:
            link = entry.link
            if link not in article_links:
                article_links.append(link)
            if len(article_links) >= max_articles:
                break

        print(f"✓ Tìm thấy {len(article_links)} bài viết mới từ RSS.")

        # 3. Duyệt từng bài để cào nội dung chi tiết
        for i, link in enumerate(article_links, 1):
            print(f"[{i}/{len(article_links)}] Đang cào: {link}", flush=True)
            self.sleep()
            data = self._fetch_article_detail(link)
            if data:
                all_articles.append(data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Title: Báo QDND dùng class post-title
        title_el = soup.select_one('h1.post-title')
        title = title_el.get_text(strip=True) if title_el else ""

        # 2. Category: Lấy từ breadcrumb (link đầu tiên)
        category = "MILITARY"
        # Tìm link đầu tiên trong breadcrumb với rel="v:url" và property="v:title"
        cate_el = soup.find('a', rel='v:url', property='v:title')
        if cate_el:
            category = cate_el.get_text(strip=True).upper()

        # 3. Published At: Lấy từ class post-date (Ví dụ: Chủ nhật, 04/01/2026)
        published_at = int(datetime.now().timestamp())
        date_el = soup.select_one('.post-date')
        if date_el:
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', date_el.get_text())
            if date_match:
                try:
                    dt = datetime.strptime(date_match.group(1), "%d/%m/%Y")
                    published_at = int(dt.timestamp())
                except: pass

        # 4. Content: Báo QDND dùng class post-content
        paragraphs = []
        # Lấy Sapo (Tóm tắt)
        sapo_el = soup.select_one('.post-summary')
        if sapo_el:
            paragraphs.append(sapo_el.get_text(strip=True))

        # Lấy nội dung chính
        content_area = soup.select_one('.post-content')
        if content_area:
            # Loại bỏ các div quảng cáo, video, ảnh liên quan nếu có
            for r in content_area.select('.related-post, .video-wrapper, .author-info'):
                r.decompose()

            for p in content_area.find_all('p'):
                txt = p.get_text(strip=True)
                if len(txt) > 30:
                    paragraphs.append(txt)

        content = "\n\n".join(paragraphs)

        if not title or len(content) < 100:
            return None

        return (published_at, title, link, content, self.source, "NA", "NA", False, category)
