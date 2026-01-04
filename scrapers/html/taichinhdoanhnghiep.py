from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import copy


class TaiChinhDoanhNghiepScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "taichinhdoanhnghiep.net.vn"
        self.headers.update({
            'Referer': 'https://taichinhdoanhnghiep.net.vn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        all_articles = []
        # Quét trang chủ để lấy danh sách bài mới
        url = "https://taichinhdoanhnghiep.net.vn/"
        html = self.fetch_html(url)
        if not html: return []

        soup = BeautifulSoup(html, 'html.parser')
        article_urls = []
        seen_urls = set()

        # Trang này thường dùng link kết thúc bằng -dXXXXX.html
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if "-d" in href and ".html" in href:
                if not href.startswith('http'):
                    href = f"https://taichinhdoanhnghiep.net.vn{href}"
                if href not in seen_urls:
                    seen_urls.add(href)
                    article_urls.append(href)

        for article_url in article_urls[:max_articles]:
            self.sleep() # Sửa lỗi sleep() không tham số
            data = self._fetch_article_detail(article_url)
            if data: all_articles.append(data)
        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Tiêu đề (Ưu tiên lấy từ #getTitle, fallback sang h1)
        title_el = soup.select_one('#getTitle') or soup.find('h1')
        if not title_el:
            print(f"⚠️ Không tìm thấy title cho URL: {link}")
            return None
        title = title_el.get_text(strip=True)
        if not title:
            print(f"⚠️ Title rỗng cho URL: {link}")
            return None

        # 2. Chuyên mục (Theo mẫu: .c-j a)
        category = "TÀI CHÍNH"
        cat_el = soup.select_one('.c-j a')
        if cat_el:
            category = cat_el.get_text(strip=True).upper()

        # 3. Ngày xuất bản (Theo mẫu: .bx-time)
        published_at = int(datetime.now().timestamp())
        date_el = soup.select_one('.bx-time')
        if date_el:
            date_text = date_el.get_text(strip=True) # Dạng: 01/01/2026, 10:52
            try:
                # Cắt lấy phần ngày trước dấu phẩy
                clean_date = date_text.split(',')[0].strip()
                dt = datetime.strptime(clean_date, '%d/%m/%Y')
                published_at = int(dt.timestamp())
            except: pass

        # 4. Nội dung (Xử lý khối .chuyennoidung và #noidung)
        content = ""
        container = soup.select_one('#noidung')
        if container:
            # Sao chép để lọc rác
            content_box = copy.copy(container)

            # LOẠI BỎ RÁC: Audio player, khối social dưới bài, quảng cáo
            # Theo mẫu bạn gửi: .audio_box, .detail-share-2, .qc1, blockquote
            for noise in content_box.select('.audio_box, .detail-share-2, .qc1, blockquote, script, .audio_tool'):
                noise.decompose()

            # Lấy Sapo (Thường nằm trong thẻ h2 hoặc có id getIntro)
            sapo_el = content_box.select_one('#getIntro, h2')
            sapo_text = sapo_el.get_text(strip=True) if sapo_el else ""

            # Lấy các đoạn văn bản (p)
            paragraphs = content_box.find_all('p')
            body_parts = []
            for p in paragraphs:
                txt = p.get_text(strip=True)
                if txt: body_parts.append(txt)

            body_text = ' '.join(body_parts)
            content = f"{sapo_text} {body_text}".strip()

        if len(content) < 50: return None



        return (published_at, title, link, content, self.source, "NA", "NA", False, category)
