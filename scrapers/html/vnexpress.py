from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup


class VnExpressScraper(NewsScraperBase):
    """
    Scraper cho VnExpress.net - crawl từ trang "Tin tức 24h"
    """

    def __init__(self):
        super().__init__()
        self.source = "vnexpress.net"
        self.headers['Referer'] = 'https://vnexpress.net/'

    def fetch_news(self, max_pages: int = 1) -> List[Tuple]:
        """
        Fetch tin tức từ VnExpress trang "Tin tức 24h"

        Args:
            max_pages: Số trang tối đa cần crawl (mặc định 1)
        """
        all_articles = []

        print(f"\n📰 Crawling VnExpress.net  Tin tức 24h - multi_source_scraper.py:90")

        for page in range(1, max_pages + 1):
            self.sleep()

            # Build URL
            if page == 1:
                url = "https://vnexpress.net/tin-tuc-24h"
            else:
                url = f"https://vnexpress.net/tin-tuc-24h-p{page}"

            print(f"\n📄 Page {page}/{max_pages}: {url} - multi_source_scraper.py:101")

            html = self.fetch_html(url)
            if not html:
                print(f"⚠ Failed to fetch page {page}, skipping - multi_source_scraper.py:105")
                continue

            # Parse listing page
            soup = BeautifulSoup(html, 'html.parser')
            articles = soup.select('article.item-news')

            if not articles:
                print(f"⚠ No articles found on page {page} - multi_source_scraper.py:113")
                continue

            print(f"Found {len(articles)} articles on page {page} - multi_source_scraper.py:116")

            for article in articles:
                try:
                    # Extract title and link
                    title_el = article.select_one('h3.title-news a')
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    link = title_el.get('href', '')

                    if not title or not link:
                        continue

                    # Extract description
                    desc_el = article.select_one('p.description a')
                    description = desc_el.get_text(strip=True) if desc_el else ""

                    # Fetch article detail
                    self.sleep()
                    article_data = self._fetch_article_detail(link, title, description)
                    if article_data:
                        all_articles.append(article_data)

                except Exception as e:
                    print(f"✗ Error parsing article: {e} - multi_source_scraper.py:142")
                    continue

        print(f"\n✓ Total articles collected: {len(all_articles)} - multi_source_scraper.py:145")
        return all_articles

    def _fetch_article_detail(self, link: str, title: str, description: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract date
        # Format: "Thứ hai, 29/12/2025, 15:50 (GMT+7)"
        date_el = soup.select_one('span.date')
        published_at = 0

        if date_el:
            date_text = date_el.get_text(strip=True)
            parts = date_text.split(',')
            if len(parts) >= 3:
                date_part = parts[1].strip()  # "29/12/2025"
                time_part = parts[2].strip().split(' ')[0]  # "15:50"
                datetime_str = f"{date_part} {time_part}"
                published_at = self.parse_date_to_timestamp(datetime_str, "%d/%m/%Y %H:%M")

        # Extract content
        content_els = soup.select('article.fck_detail p.Normal')
        content = ' '.join([p.get_text(strip=True) for p in content_els if p.get_text(strip=True)])

        if not content:
            content = description

        # Extract category từ breadcrumb
        # VD: <ul.breadcrumb><li><a href="/suc-khoe">Sức khỏe</a></li>...
        category = "Tin tức 24h"  # Default

        breadcrumb_links = soup.select('ul.breadcrumb li a, .breadcrumb a')
        if breadcrumb_links:
            # Lấy item đầu tiên làm category chính
            category_el = breadcrumb_links[0]
            category_text = category_el.get_text(strip=True)
            if category_text:
                category = category_text.upper()

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
