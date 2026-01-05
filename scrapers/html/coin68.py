from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime


class Coin68Scraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "coin68.com"
        self.base_url = "https://coin68.com"

    def fetch_news(self, max_articles: int = 10) -> List[Tuple]:
        all_articles = []
        url = self.base_url

        print(f"\n📡 Đang quét cấu trúc Hot News Coin68...")
        html = self.fetch_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')

        # 1. Tìm tất cả các khối tin dựa trên class 'css-19idom' bạn cung cấp
        items = soup.find_all('div', class_='css-19idom')

        article_urls = []
        for item in items:
            # 2. Tìm thẻ a chứa tiêu đề (thẻ a nằm trong div css-112x203 như mẫu của bạn)
            link_el = item.select_one('div.css-112x203 a')
            if link_el and link_el.get('href'):
                href = link_el.get('href')
                full_url = f"{self.base_url}{href}" if href.startswith('/') else href

                if full_url not in article_urls:
                    article_urls.append(full_url)

            if len(article_urls) >= max_articles:
                break

        print(f"✓ Tìm thấy {len(article_urls)} bài viết từ giao diện Hot News.")

        # 3. Lấy chi tiết từng bài
        for i, article_url in enumerate(article_urls, 1):
            print(f"[{i}/{len(article_urls)}] Đang cào: {article_url}", flush=True)
            self.sleep()
            data = self._fetch_article_detail(article_url)
            if data:
                all_articles.append(data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html_text = self.fetch_html(link)
        if not html_text: return None
        soup = BeautifulSoup(html_text, 'html.parser')

        # 1. Lấy Title - Dùng selector ổn định (h1 hoặc MuiTypography-h2)
        title = ""
        title_el = soup.find('h1')
        if title_el:
            title = title_el.get_text(strip=True)

        # 2. Lấy Category (Dựa trên breadcrumbs)
        category = "CRYPTO"
        # Tìm breadcrumb chứa link /article/ (đó là category)
        category_link = soup.select_one('.MuiBreadcrumbs-li a[href*="/article/"]')
        if category_link:
            span = category_link.find('span')
            if span:
                category = span.get_text(strip=True).upper()

        # 3. Lấy Published At - Tìm thẻ span chứa ngày
        published_at = int(datetime.now().timestamp())
        # Thử tìm span chứa pattern ngày DD/MM/YYYY
        for span in soup.find_all('span'):
            text = span.get_text(strip=True)
            if '/' in text and len(text) == 10:  # Format: DD/MM/YYYY
                try:
                    dt = datetime.strptime(text, "%d/%m/%Y")
                    published_at = int(dt.timestamp())
                    break
                except:
                    continue

        # 4. Lấy Content - Dùng div#content (không cần class cụ thể)
        paragraphs = []
        content_div = soup.find('div', id='content')

        if content_div:
            # Chỉ lấy text từ các thẻ p, bỏ qua các thẻ script/iframe/ads
            for p in content_div.find_all('p', recursive=True):
                # Loại bỏ các đoạn text chứa "Ảnh:", "Nguồn:", "Có thể bạn quan tâm"
                txt = p.get_text(strip=True)
                if len(txt) > 30 and not any(x in txt for x in ["Ảnh:", "Nguồn:", "tổng hợp"]):
                    paragraphs.append(txt)

        content = "\n\n".join(paragraphs)

        # Kiểm tra điều kiện cuối cùng để tránh lưu bài rỗng
        if not title or not content:
            return None

        return (published_at, title, link, content, self.source, "NA", "NA", False, category)
