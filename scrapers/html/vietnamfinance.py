from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re


class VietnamFinanceScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "vietnamfinance.vn"
        self.base_url = "https://vietnamfinance.vn"

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        all_articles = []
        html = self.fetch_html(self.base_url)
        if not html: return []

        soup = BeautifulSoup(html, 'html.parser')
        article_links = []

        # 1. Lấy link từ khu vực articles (bao gồm cả Swiper và Danh sách bên dưới)
        container = soup.select_one('.section-secondary__left .articles')
        if container:
            # Tìm tất cả thẻ a có class title hoặc nằm trong h3.article__title
            # Cách bóc tách này khớp với cả 2 mẫu HTML bạn gửi
            links = container.find_all('a', href=True)
            for a in links:
                href = a['href']
                # Chỉ lấy link bài viết (thường có đuôi .html và chứa mã d+số)
                if '.html' in href and href != self.base_url:
                    full_url = href if href.startswith('http') else self.base_url + href
                    if full_url not in article_links:
                        article_links.append(full_url)

                if len(article_links) >= max_articles:
                    break

        print(f"✓ Tìm thấy {len(article_links)} bài viết từ trang chủ.")

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

        # 1. Title (Khớp với h1.detail-title)
        title_el = soup.select_one('h1.detail-title')
        title = title_el.get_text(strip=True) if title_el else ""

        # 2. Category (Khớp với li.breadcrumb-item a)
        category = "FINANCE"
        cate_el = soup.select_one('.breadcrumb-item a.breadcrumb-link')
        if cate_el:
            category = cate_el.get_text(strip=True).upper()

        # 3. Published At (Khớp với thẻ span chứa định dạng dd/mm/yyyy hh:mm)
        published_at = int(datetime.now().timestamp())
        # Tìm thẻ span có nội dung chứa ngày tháng
        date_el = soup.find('span', string=re.compile(r'\d{2}/\d{2}/\d{4}'))
        if date_el:
            date_str = re.search(r'\d{2}/\d{2}/\d{4}', date_el.get_text()).group()
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                published_at = int(dt.timestamp())
            except: pass

        # 4. Content (Khớp với #news_detail #explus-editor)
        paragraphs = []
        # Lấy Sapo trước (vì nó chứa tóm tắt quan trọng)
        sapo_el = soup.select_one('.detail-sapo')
        if sapo_el:
            paragraphs.append(sapo_el.get_text(strip=True))

        # Lấy các đoạn trong nội dung chính
        content_div = soup.select_one('#news_detail #explus-editor')
        if content_div:
            # Duyệt qua các thẻ p, bỏ qua các thẻ ads/script bên trong
            for p in content_div.find_all('p', recursive=False):
                txt = p.get_text(strip=True)
                if len(txt) > 20: # Bỏ qua các dòng quá ngắn
                    paragraphs.append(txt)

        content = "\n\n".join(paragraphs)

        if not title or len(content) < 100:
            return None

        return (published_at, title, link, content, self.source, "NA", "NA", False, category)
