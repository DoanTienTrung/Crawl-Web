from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime


class VietnametScraper(NewsScraperBase):
    """
    Scraper cho Vietnamnet.vn
    Tương tự hàm fetch_vietnamnet_news trong Rust
    """

    def __init__(self):
        super().__init__()
        self.source = "vietnamnet.vn"
        self.headers['Referer'] = 'https://vietnamnet.vn/'

    def fetch_news(self, max_pages: int = 1, target_date: str = None) -> List[Tuple]:
        """
        Fetch tin tức từ Vietnamnet (tin tức 24h by date)

        Args:
            max_pages: Số trang tối đa cần crawl (mặc định 1)
            target_date: Ngày cần crawl theo format 'dd/mm/yyyy'. Nếu None, dùng ngày hiện tại
        """
        all_articles = []

        # Get date for the bydate parameter
        if target_date:
            date_str = target_date
        else:
            today = datetime.now()
            date_str = today.strftime("%d/%m/%Y")

        print(f"\n📅 Crawling Vietnamnet for date: {date_str} - multi_source_scraper.py:560")

        # Start from page 0
        page = 0

        while True:
            # Build URL with date filter
            url = f"https://vietnamnet.vn/tin-tuc-24h-p{page}?bydate={date_str}-{date_str}&cate="

            print(f"\n  📄 Page {page}: {url} - multi_source_scraper.py:569")
            self.sleep()

            html = self.fetch_html(url)
            if not html:
                print(f"⚠ Failed to fetch page {page}, stopping - multi_source_scraper.py:574")
                break

            soup = BeautifulSoup(html, 'html.parser')

            # Select posts
            posts = soup.select('div.horizontalPost.version-news')

            if not posts:
                print(f"⚠ No articles found on page {page}, stopping - multi_source_scraper.py:583")
                break

            print(f"Found {len(posts)} articles on page {page} - multi_source_scraper.py:586")

            for post in posts:
                try:
                    # Extract title and link
                    title_el = post.select_one('h3.horizontalPost__main-title a')
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    href = title_el.get('href', '')
                    link = href if href.startswith('http') else f"https://vietnamnet.vn{href}"

                    if not title or not link:
                        continue

                    # Fetch article detail
                    self.sleep()
                    article_data = self._fetch_article_detail(link, title)
                    if article_data:
                        all_articles.append(article_data)

                except Exception as e:
                    print(f"✗ Error parsing article: {e} - multi_source_scraper.py:609")
                    continue

            # Check if we should continue to next page
            if max_pages is not None and page >= max_pages - 1:
                print(f"Reached max_pages limit ({max_pages}) - multi_source_scraper.py:614")
                break

            # Check if there's a next page by reading pagination numbers
            pagination = soup.select_one('div.pagination ul.pagination__list')
            if not pagination:
                print(f"No pagination found, stopping - multi_source_scraper.py:620")
                break

            # Find all numbered page links (excluding the pagination-next button)
            page_items = pagination.select('li.pagination__list-item:not(.pagination-next) a')
            page_numbers = []

            for item in page_items:
                page_text = item.get_text(strip=True)
                if page_text.isdigit():
                    page_numbers.append(int(page_text))

            if page_numbers:
                max_page_num = max(page_numbers)
                print(f"Pagination detected: pages 1{max_page_num} (current: page {page + 1}) - multi_source_scraper.py:634")

                # Current page is 0-indexed, but display is 1-indexed
                # If we're at the last page, stop
                if page + 1 >= max_page_num:
                    print(f"Reached the last page ({page + 1}/{max_page_num}) - multi_source_scraper.py:639")
                    break
            else:
                print(f"No page numbers found in pagination, stopping - multi_source_scraper.py:642")
                break

            # Move to next page
            page += 1

        print(f"\n  ✓ Total articles collected: {len(all_articles)} from {page + 1} page(s) - multi_source_scraper.py:648")
        return all_articles

    def _fetch_article_detail(self, link: str, title: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract date
        date_el = soup.select_one('div.bread-crumb-detail__time') or soup.select_one('span.time')
        published_at = 0

        if date_el:
            date_text = date_el.get_text(strip=True)

            # Clean date string
            # Format: "Thứ Sáu, 26/12/2025 - 22:10" → "26/12/2025 22:10"
            # Remove "Thứ X, " ở đầu
            if date_text.startswith('Thứ'):
                parts = date_text.split(',', 1)
                if len(parts) > 1:
                    date_text = parts[1].strip()

            # Remove dấu " - " giữa date và time
            date_text = date_text.replace(' - ', ' ')

            # Try various formats
            for fmt in ["%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M", "%d/%m/%Y"]:
                parsed_ts = self.parse_date_to_timestamp(date_text, fmt)
                if parsed_ts > 0:
                    published_at = parsed_ts
                    break

        # Extract content
        content_el = soup.select_one('div.maincontent') or soup.select_one('div.article-content')
        content = ""

        if content_el:
            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # Extract category từ breadcrumb
        category = "Tin tức"  # Default

        # Thử tìm từ breadcrumb - thường category là item thứ 2 (sau "Trang chủ")
        breadcrumb_links = soup.select('ul.breadcrumb li a, .breadcrumb a, .bread-crumb a')
        if len(breadcrumb_links) >= 2:
            # Item đầu tiên thường là "Trang chủ", item thứ 2 là category
            category_el = breadcrumb_links[1]
            category_text = category_el.get_text(strip=True)
            if category_text and category_text.lower() not in ['trang chủ', 'home', 'vietnamnet']:
                category = category_text
            # Nếu không có text, thử lấy từ title attribute
            elif not category_text:
                category = category_el.get('title', category).strip()

        # Fallback: Tìm link category gần khu vực date (nếu breadcrumb không có)
        if category == "Tin tức":
            # Tìm trong parent của bread-crumb-detail__time
            date_parent = soup.select_one('div.bread-crumb-detail__time')
            if date_parent and date_parent.parent:
                nearby_links = date_parent.parent.select('a[title]')
                for link_el in nearby_links:
                    href = link_el.get('href', '')
                    # Category links thường có href ngắn như "/thoi-su", "/kinh-doanh"
                    if href.startswith('/') and href.count('/') == 1 and len(href) < 30:
                        category = link_el.get_text(strip=True) or link_el.get('title', category)
                        break

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
