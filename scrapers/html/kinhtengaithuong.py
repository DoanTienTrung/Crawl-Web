from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re


class KinhTeNgoaiThuongScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "kinhtengoaithuong.vn"
        # Thêm header để giả lập trình duyệt xem tin tức
        self.headers.update({
            'Referer': 'https://www.google.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        all_articles = []
        url = "https://kinhtengoaithuong.vn/"

        print(f"\n📡 Đang quét trang chủ: {url}")
        html = self.fetch_html(url)

        if not html:
            print("⚠ Không thể truy cập trang chủ kinhtengoaithuong.vn")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        potential_links = soup.select('h2 a, h3 a, .post-title a, .entry-title a')

        article_urls = []
        seen_urls = set()

        for a in potential_links:
            href = a.get('href', '')
            if not href: continue

            # Chuẩn hóa link tuyệt đối
            if href.startswith('/'):
                href = f"https://kinhtengoaithuong.vn{href}"

            # Lọc: Phải thuộc domain, không phải trang chủ, không phải link rác
            if "kinhtengoaithuong.vn" in href and href != "https://kinhtengoaithuong.vn/":
                # Loại bỏ các trang chức năng
                if not any(x in href for x in ['/category/', '/tag/', '/author/', '/contact/', '/gioi-thieu/', '/c/']):
                    if href not in seen_urls:
                        seen_urls.add(href)
                        article_urls.append(href)

        # 2. Nếu Selector trên không ra kết quả, dùng Regex để quét toàn bộ link
        if not article_urls:
            print("🔍 Thử quét link bằng phương thức Regex...")
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Link bài viết thường có độ sâu path > 3 (ví dụ domain.vn/ten-bai-viet/)
                if "kinhtengoaithuong.vn" in href and len(href.strip('/').split('/')) >= 3:
                     if href not in seen_urls and not any(x in href for x in ['/category/', '/tag/', '/c/']):
                        seen_urls.add(href)
                        article_urls.append(href)

        article_urls = article_urls[:max_articles]
        print(f"✓ Tìm thấy {len(article_urls)} bài viết từ trang chủ.")

        for i, article_url in enumerate(article_urls, 1):
            print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:50]}...", flush=True)
            self.sleep()
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
        title = title_el.get_text(strip=True) if title_el else ''
        if not title: return None

        # 2. Ngày xuất bản
        published_at = int(datetime.now().timestamp())
        # Tìm trong các thẻ meta hoặc class date phổ biến của trang
        date_el = soup.select_one('.detail-date, .post-date, .time')
        if date_el:
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_el.get_text())
            if date_match:
                d, m, y = date_match.groups()
                try: published_at = int(datetime(int(y), int(m), int(d)).timestamp())
                except: pass

        # 3. Nội dung (Sử dụng Selector: .article-content)
        content_el = soup.select_one('.article-content')
        content = ""
        if content_el:
            # Thu thập dữ liệu từ cả thẻ <p> và các dòng trong <table> (chú thích ảnh)
            # để đảm bảo không sót thông tin quan trọng
            parts = []

            # Lấy các đoạn văn bản
            for p in content_el.find_all(['p', 'td']):
                # Loại bỏ khoảng trắng thừa và các ký tự đặc biệt
                txt = p.get_text(strip=True)
                if txt and len(txt) > 5: # Chỉ lấy các đoạn có nghĩa
                    parts.append(txt)

            content = ' '.join(parts)

        # 4. Chuyên mục (Category)
        category = "TÀI CHÍNH" 
        bread_items = soup.select('a[itemprop="item"]')
        if len(bread_items) >= 2:
            # Lấy text từ thuộc tính title hoặc từ thẻ span bên trong
            category = bread_items[1].get('title') or bread_items[1].get_text(strip=True)

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
            category
        )
