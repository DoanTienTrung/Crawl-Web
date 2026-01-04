from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import copy


class ThoiBaoNganHangScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "thoibaonganhang.vn"
        self.headers.update({
            'Referer': 'https://thoibaonganhang.vn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        all_articles = []
        url = "https://thoibaonganhang.vn/"

        print(f"\n📡 Đang quét trang chủ Thời báo Ngân hàng: {url}")
        html = self.fetch_html(url)
        if not html: return []

        soup = BeautifulSoup(html, 'html.parser')
        article_urls = []
        seen_urls = set()

        # Quét tất cả link bài viết có đuôi .html và chứa số ID
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if ".html" in href and any(char.isdigit() for char in href):
                if not href.startswith('http'):
                    href = f"https://thoibaonganhang.vn{href}"

                if not any(x in href for x in ['/video-', '/anh-', '/chuyen-muc/', '/tags/']):
                    if href not in seen_urls:
                        seen_urls.add(href)
                        article_urls.append(href)

        article_urls = article_urls[:max_articles]
        print(f"✓ Tìm thấy {len(article_urls)} bài viết tiềm năng.")

        for i, article_url in enumerate(article_urls, 1):
            print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:60]}...")
            self.sleep() # Không truyền tham số để tránh lỗi NewsScraperBase
            article_data = self._fetch_article_detail(article_url)
            if article_data:
                all_articles.append(article_data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Tiêu đề
        title_el = soup.find('h1')
        if not title_el: return None
        title = title_el.get_text(strip=True)

        # 2. Ngày xuất bản (.format_date)
        published_at = int(datetime.now().timestamp())
        date_el = soup.select_one('.format_date')
        if date_el:
            try:
                dt = datetime.strptime(date_el.get_text(strip=True), '%d/%m/%Y')
                published_at = int(dt.timestamp())
            except: pass

        # 3. Chuyên mục (.bx-cat-link)
        category = "NGÂN HÀNG"
        cat_el = soup.select_one('.bx-cat-link')
        if cat_el:
            category = cat_el.get_text(strip=True).upper()

        # 4. Nội dung (Gộp Sapo + Body)
        content = ""
        container = soup.select_one('.article-detail-body')
        if container:
            content_box = copy.copy(container)

            # Lấy phần Sapo (Tóm tắt)
            sapo_el = content_box.select_one('.article-detail-desc')
            sapo_text = sapo_el.get_text(strip=True) if sapo_el else ""

            # Loại bỏ rác trước khi lấy Body
            for noise in content_box.select('.article-share-button, .article-extension, script, style, .article-detail-desc'):
                noise.decompose()

            # Lấy các đoạn văn bản chính
            paragraphs = content_box.find_all('p')
            if paragraphs:
                body_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            else:
                body_text = content_box.get_text(" ", strip=True)

            # Kết hợp Sapo và Body
            content = f"{sapo_text} {body_text}".strip()

        if not content or len(content) < 50:
            return None


        return (published_at, title, link, content, self.source, "NA", "NA", False, category)
