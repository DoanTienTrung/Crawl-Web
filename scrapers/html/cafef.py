from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re


class CafeFScraper(NewsScraperBase):
    """
    Scraper cho CafeF.vn
    """

    def __init__(self):
        super().__init__()
        self.source = "cafef.vn"
        self.headers['Referer'] = 'https://cafef.vn/'

    def fetch_news(self, max_pages: int = 1, max_articles_per_page: int = 20) -> List[Tuple]:
        """
        Fetch tin tức từ CafeF từ trang /doc-nhanh

        Args:
            max_pages: Số trang tối đa (mặc định 1)
            max_articles_per_page: Số bài tối đa mỗi trang (mặc định 20)
        """
        all_articles = []
        seen_urls = {}  # Track URLs và page number: {full_url: page_number}

        for page in range(1, max_pages + 1):
            # Build pagination URL
            if page == 1:
                url = "https://cafef.vn/doc-nhanh.chn"
            else:
                url = f"https://cafef.vn/doc-nhanh/trang-{page}.chn"

            print(f"\n📄 Page {page}/{max_pages}: {url} - multi_source_scraper.py:956")
            self.sleep()

            html = self.fetch_html(url)
            if not html:
                print(f"⚠ Failed to fetch page {page}, skipping - multi_source_scraper.py:961")
                continue

            soup = BeautifulSoup(html, 'html.parser')

            # Find all article links với pattern -188*.chn
            links = soup.find_all('a', href=re.compile(r'-\d{15,}\.chn$'))

            article_urls = []

            for link in links:
                href = link.get('href', '')
                if href:
                    full_url = href if href.startswith('http') else f"https://cafef.vn{href}"
                    # Exclude pagination pages
                    if '/trang-' in full_url:
                        continue
                    if full_url not in seen_urls:
                        seen_urls[full_url] = page
                        article_urls.append(full_url)

            if not article_urls:
                print(f"⚠ No new articles on page {page} - multi_source_scraper.py:983")
                continue

            print(f"Found {len(article_urls)} new article URLs on page {page} - multi_source_scraper.py:986")

            # Limit articles per page
            article_urls = article_urls[:max_articles_per_page]

            # Fetch article details
            for i, article_url in enumerate(article_urls, 1):
                print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:60]}... - multi_source_scraper.py:993", flush=True)
                self.sleep()

                article_data = self._fetch_article_detail(article_url)
                if article_data:
                    all_articles.append(article_data)

        print(f"\n✓ Total articles collected: {len(all_articles)} - multi_source_scraper.py:1000")
        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo CafeF"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract title
        title_el = soup.select_one('h1.title') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''

        if not title:
            return None

        # Extract date từ span.pdate[data-role="publishdate"]
        # Format: "29-12-2025 - 16:16 PM"
        published_at = 0

        date_el = soup.select_one('span.pdate[data-role="publishdate"]')
        if date_el:
            date_text = date_el.get_text(strip=True)
            # Parse: "29-12-2025 - 16:16 PM" -> datetime
            date_match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{4})\s*-\s*(\d{1,2}):(\d{2})', date_text)
            if date_match:
                day, month, year, hour, minute = date_match.groups()
                try:
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    published_at = int(dt.timestamp())
                except:
                    pass

        # Extract content
        content_selectors = ['.detail-content', '.contentdetail', '.detail_content', 'article .content']
        content = ""

        for selector in content_selectors:
            content_el = soup.select_one(selector)
            if content_el:
                paragraphs = content_el.select('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                if content:
                    break

        # Extract category từ a[data-role="cate-name"]
        category = "ĐỌC NHANH"  # Default

        category_el = soup.select_one('a[data-role="cate-name"]')
        if category_el:
            # Lấy text hoặc title nếu text rỗng, sau đó in hoa
            category = (category_el.get_text(strip=True) or category_el.get('title', 'ĐỌC NHANH')).strip().upper()


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
