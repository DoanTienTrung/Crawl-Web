from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import copy
import re


class TinNhanhChungKhoanScraper(NewsScraperBase):
    """
    Scraper cho tinnhanhchungkhoan.vn
    Lấy 10 bài viết mới nhất từ trang chủ
    """
    def __init__(self):
        super().__init__()
        self.source = "tinnhanhchungkhoan.vn"
        self.headers.update({
            'Referer': 'https://www.tinnhanhchungkhoan.vn/',
        })

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        """Lấy bài viết mới nhất từ trang chủ"""
        all_articles = []
        url = "https://www.tinnhanhchungkhoan.vn/"

        print(f"\n📡 Đang quét Tin nhanh chứng khoán: {url}")
        html = self.fetch_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')

        # Tìm các link bài viết trên trang chủ
        article_urls = []
        seen_urls = set()

        # Tìm các link bài viết (thử nhiều selector phổ biến)
        links = soup.select('article a, .news-item a, .article-link, h2 a, h3 a, .cms-link a')

        for link in links:
            href = link.get('href', '')
            if not href:
                continue

            # Chuẩn hóa URL
            if not href.startswith('http'):
                if href.startswith('/'):
                    href = f"https://www.tinnhanhchungkhoan.vn{href}"
                else:
                    href = f"https://www.tinnhanhchungkhoan.vn/{href}"

            # Chỉ lấy các link bài viết từ domain tinnhanhchungkhoan.vn
            # và tránh các link menu, category, tag
            if 'tinnhanhchungkhoan.vn' in href and href not in seen_urls:
                # Bỏ qua các link không phải bài viết
                skip_patterns = ['/tag/', '/author/', '/category/', '#', 'javascript:']
                if any(pattern in href for pattern in skip_patterns):
                    continue

                seen_urls.add(href)
                article_urls.append(href)

                if len(article_urls) >= max_articles:
                    break

        print(f"Tìm thấy {len(article_urls)} bài viết")

        # Fetch chi tiết từng bài
        for i, article_url in enumerate(article_urls, 1):
            print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:70]}...", flush=True)
            self.sleep()
            article_data = self._fetch_article_detail(article_url)
            if article_data:
                all_articles.append(article_data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        """Lấy chi tiết một bài viết"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 1. Title - <h1 class="article__header cms-title">
        title_el = soup.select_one('h1.article__header.cms-title')
        if not title_el:
            # Fallback: thử selector khác
            title_el = soup.select_one('h1.cms-title')
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        # 2. Published_at - <time class="time" datetime="..." data-time="1767315611">
        published_at = int(datetime.now().timestamp())  # Default
        time_el = soup.select_one('time.time')
        if time_el:
            # Ưu tiên dùng data-time vì nó là Unix timestamp sẵn
            data_time = time_el.get('data-time', '')
            if data_time and data_time.isdigit():
                published_at = int(data_time)
            else:
                # Fallback: parse datetime attribute
                datetime_str = time_el.get('datetime', '')
                if datetime_str:
                    try:
                        # Format: "2026-01-02T08:00:11+0700"
                        # Loại bỏ timezone offset để parse
                        datetime_str_clean = re.sub(r'[+-]\d{4}$', '', datetime_str)
                        dt = datetime.fromisoformat(datetime_str_clean)
                        published_at = int(dt.timestamp())
                    except:
                        pass

        # 3. Category - <li class="main-cate"><a title="...">
        category = "Chứng khoán"  # Default
        cat_el = soup.select_one('li.main-cate a')
        if cat_el:
            category = cat_el.get_text(strip=True)

        # 4. Content - sapo + body
        content_parts = []

        # Sapo
        sapo_el = soup.select_one('div.article__sapo.cms-desc')
        if sapo_el:
            content_parts.append(sapo_el.get_text(strip=True))

        # Body
        body_el = soup.select_one('div.article__body.cms-body')
        if body_el:
            # Loại bỏ ads và script
            body_copy = copy.copy(body_el)
            for noise in body_copy.select('.ads_middle, script, style, .banner'):
                noise.decompose()

            # Lấy text từ các thẻ p, h2, h3
            paragraphs = body_copy.find_all(['p', 'h2', 'h3'])
            text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            content_parts.extend(text_parts)

        content = ' '.join(content_parts).strip()

        if len(content) < 50:  # Bài viết quá ngắn, bỏ qua
            return None

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
