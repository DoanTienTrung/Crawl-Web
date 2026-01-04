from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re


class XaydungChinhsachScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "xaydungchinhsach.chinhphu.vn"
        self.base_url = "https://xaydungchinhsach.chinhphu.vn"

    def fetch_news(self, max_articles: int = 10) -> List[Tuple]:
        all_articles = []
        # Trang chủ của site này chính là danh sách tin nổi bật/mới nhất
        html = self.fetch_html(self.base_url)
        if not html: return []

        soup = BeautifulSoup(html, 'html.parser')
        article_links = []

        # Tìm tất cả các link bài viết (thường nằm trong các khối tin)
        # Site này sử dụng các thẻ a có thuộc tính title rất đầy đủ
        links = soup.select('a[title]')
        for a in links:
            href = a.get('href')
            # Lọc các link là bài viết:
            # - Phải có .htm
            # - Phải có mã ID số (ví dụ: 119260101192109677.htm)
            # - Loại bỏ category pages (không có số hoặc quá ngắn)
            if href and '.htm' in href and not href.startswith('javascript'):
                # Kiểm tra href có chứa chuỗi số dài (article ID)
                # Article URLs thường có format: /abc-xyz-119260101192109677.htm
                if re.search(r'\d{10,}', href):  # Có ít nhất 10 chữ số liên tiếp = article ID
                    full_url = href if href.startswith('http') else self.base_url + href
                    if full_url not in article_links:
                        article_links.append(full_url)

            if len(article_links) >= max_articles:
                break

        print(f"✓ Tìm thấy {len(article_links)} bài viết từ Xây dựng chính sách.")

        for i, link in enumerate(article_links, 1):
            print(f"[{i}/{len(article_links)}] Đang cào: {link}")
            self.sleep()
            data = self._fetch_article_detail(link)
            if data:
                all_articles.append(data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Title - Dùng data-role hoặc class chính xác
        title = ""
        title_el = soup.select_one('h1[data-role="title"]') or soup.select_one('h1.title') or soup.find('h1')
        if title_el:
            title = title_el.get_text(strip=True)

        # 2. Category - Từ breadcrumbs
        category = "POLICY"
        cat_el = soup.select_one('.list-cate a[data-role="cate-name"]') or soup.select_one('.list-cate a.item-cate')
        if cat_el:
            category = cat_el.get_text(strip=True).upper()

        # 3. Published At - Dùng data-role="publishdate"
        published_at = int(datetime.now().timestamp())
        date_el = soup.select_one('p[data-role="publishdate"]') or soup.select_one('p.days')
        if date_el:
            date_text = date_el.get_text(strip=True)
            # Format: "03/01/2026 08:56" hoặc "03/01/2026"
            match = re.search(r'(\d{2}/\d{2}/\d{4})', date_text)
            if match:
                try:
                    dt = datetime.strptime(match.group(1), "%d/%m/%Y")
                    published_at = int(dt.timestamp())
                except: pass

        # 4. Content - Lấy từ sapo + detail-content
        paragraphs = []

        # Lấy sapo (lead/summary)
        sapo_el = soup.select_one('h2[data-role="sapo"]') or soup.select_one('.detail-sapo')
        if sapo_el:
            sapo_text = sapo_el.get_text(strip=True)
            if len(sapo_text) > 20:
                paragraphs.append(sapo_text)

        # Lấy content chính
        content_area = soup.select_one('div[data-role="content"]') or soup.select_one('.detail-content.afcbc-body')
        if content_area:
            # Lấy các thẻ p, h2, h3, h4 (bỏ qua figure, script, style)
            for elem in content_area.find_all(['p', 'h2', 'h3', 'h4']):
                txt = elem.get_text(strip=True)
                # Bỏ qua các đoạn quá ngắn, chú thích ảnh, link download
                if len(txt) > 30 and not any(skip in txt.lower() for skip in ['nguồn:', 'tham khảo thêm', 'toàn văn:', '---']):
                    paragraphs.append(txt)

        content = "\n\n".join(paragraphs)

        if not title or not content: return None

        return (published_at, title, link, content, self.source, "NA", "NA", False, category)
