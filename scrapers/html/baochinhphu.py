from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import copy
import re


class BaoChinhPhuScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "baochinhphu.vn"
        self.headers.update({
            'Referer': 'https://baochinhphu.vn/',
        })

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        all_articles = []
        url = "https://baochinhphu.vn/tin-moi.htm"

        print(f"\n📡 Đang quét Báo Chính phủ: {url}")
        html = self.fetch_html(url)
        if not html: return []

        soup = BeautifulSoup(html, 'html.parser')
        article_urls = []
        seen_urls = set()

        # Báo Chính phủ thường bọc link trong khối có class 'story' hoặc 'box-category'
        links = soup.select('a[data-role="title"], .story__title a, .box-stream-link-title, .box-category-link-title')
        for link in links:
            href = link.get('href', '')
            if href and href.endswith('.htm'):
                if not href.startswith('http'):
                    href = f"https://baochinhphu.vn{href}"

                if href not in seen_urls:
                    seen_urls.add(href)
                    article_urls.append(href)

            if len(article_urls) >= max_articles:
                break

        for i, article_url in enumerate(article_urls, 1):
            print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:60]}...", flush=True)
            self.sleep()
            article_data = self._fetch_article_detail(article_url)
            if article_data:
                all_articles.append(article_data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Tiêu đề (data-role="title")
        title_el = soup.select_one('[data-role="title"]')
        if not title_el: return None
        title = title_el.get_text(strip=True)

        # 2. Ngày xuất bản (Xử lý chuỗi 02/01/2026 ... 15:21)
        published_at = int(datetime.now().timestamp())
        date_container = soup.select_one('[data-role="publishdate"]')
        if date_container:
            # Loại bỏ các tag con (như icon SVG) để lấy text thuần
            raw_date = date_container.get_text(" ", strip=True)
            # Dùng regex lấy định dạng dd/mm/yyyy
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', raw_date)
            if date_match:
                try:
                    dt = datetime.strptime(date_match.group(1), '%d/%m/%Y')
                    published_at = int(dt.timestamp())
                except: pass

        # 3. Chuyên mục (data-role="cate-name")
        category = "CHÍNH TRỊ"
        cat_el = soup.select_one('[data-role="cate-name"]')
        if cat_el:
            category = cat_el.get_text(strip=True).upper()

        # 4. Nội dung (data-role="content")
        content = ""
        body_container = soup.select_one('[data-role="content"]')
        if body_container:
            content_box = copy.copy(body_container)
            
            for noise in content_box.select('.VCSortableInPreviewMode[type="RelatedNewsBox"], .button-dowload-img, script, style'):
                noise.decompose()

            # Lấy toàn bộ text từ các thẻ p
            paragraphs = content_box.find_all(['p', 'h2', 'h3'])
            text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            content = ' '.join(text_parts).strip()

        if len(content) < 50: return None


        return (
            published_at,
            title,
            link, 
            content, 
            self.source, 
            "NA", 
            "NA", 
            False, 
            category
            )
