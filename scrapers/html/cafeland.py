from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re


class CafelandScraper(NewsScraperBase):
    """
    Scraper cho Cafeland.vn - Bất động sản
    """

    def __init__(self):
        super().__init__()
        self.source = "cafeland.vn"
        self.headers['Referer'] = 'https://cafeland.vn/'

    def fetch_news(self, max_pages: int = 1, max_articles_per_page: int = 20) -> List[Tuple]:
        """
        Fetch tin tức từ Cafeland trang "Bất động sản mới nhất"

        Args:
            max_pages: Số trang tối đa cần crawl (mặc định 1)
            max_articles_per_page: Số bài tối đa mỗi trang (mặc định 20)
        """
        all_articles = []

        print(f"\n📰 Crawling Cafeland.vn  Bất động sản mới nhất - multi_source_scraper.py:753")

        for page in range(1, max_pages + 1):
            self.sleep()

            # Build URL
            if page == 1:
                url = "https://cafeland.vn/bat-dong-san-moi-nhat/"
            else:
                url = f"https://cafeland.vn/bat-dong-san-moi-nhat/page/{page}/"

            print(f"\n📄 Page {page}/{max_pages}: {url} - multi_source_scraper.py:764")

            html = self.fetch_html(url)
            if not html:
                print(f"⚠ Failed to fetch page {page}, skipping - multi_source_scraper.py:768")
                continue

            # Parse listing page
            soup = BeautifulSoup(html, 'html.parser')
            # Note: Articles are in <li class="loadBoxHomeMore">, not <div>
            articles = soup.select('li.loadBoxHomeMore')

            if not articles:
                print(f"⚠ No articles found on page {page} - multi_source_scraper.py:777")
                continue

            print(f"Found {len(articles)} articles on page {page} - multi_source_scraper.py:780")

            # Limit articles per page
            articles = articles[:max_articles_per_page]

            for article in articles:
                try:
                    # Extract title and link
                    title_el = article.select_one('h3 a')
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    link = title_el.get('href', '')

                    if not title or not link:
                        continue

                    # Make sure link is absolute
                    if not link.startswith('http'):
                        link = f"https://cafeland.vn{link}"

                    # Extract description
                    desc_els = article.select('p')
                    description = desc_els[1].get_text(strip=True) if len(desc_els) > 1 else ""

                    # Fetch article detail
                    self.sleep()
                    article_data = self._fetch_article_detail(link, title, description)
                    if article_data:
                        all_articles.append(article_data)

                except Exception as e:
                    print(f"✗ Error parsing article: {e} - multi_source_scraper.py:813")
                    continue

        print(f"\n✓ Total articles collected: {len(all_articles)} - multi_source_scraper.py:816")
        return all_articles

    def _fetch_article_detail(self, link: str, title: str, description: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        published_at = 0
        date_el = soup.select_one('div.info-date.right')

        if date_el:
            # Get text content, skipping audio element
            date_text = date_el.get_text(strip=True)
            # Remove any extra whitespace
            date_text = re.sub(r'\s+', ' ', date_text).strip()

            # Parse: "31/12/2025 9:05 PM"
            # Try to match the date pattern
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})\s*(AM|PM)', date_text)
            if date_match:
                day, month, year, hour, minute, period = date_match.groups()
                try:
                    hour = int(hour)
                    # Convert to 24-hour format
                    if period == 'PM' and hour != 12:
                        hour += 12
                    elif period == 'AM' and hour == 12:
                        hour = 0

                    dt = datetime(int(year), int(month), int(day), hour, int(minute))
                    published_at = int(dt.timestamp())
                except Exception as e:
                    print(f"⚠ Could not parse date '{date_text}': {e} - multi_source_scraper.py:854")

        # Extract content
        # Try content containers (IDs for news articles, class for project pages)
        content_els = soup.select('#sevenBoxNewContentInfo, #sevenBoxNewContentInfoNo, #sevenBoxNewContenDAtInfo, div.sevenPostContent')
        content = description

        if content_els:
            paragraphs = []
            # Only use the first matching container to avoid duplication
            el = content_els[0]

            # Get div.sevenPostDes (description)
            desc_div = el.select_one('div.sevenPostDes')
            if desc_div:
                paragraphs.append(desc_div)

            # Get all headings and paragraphs in document order
            for elem in el.select('h2, h3, h4, h5, h6, p'):
                # If it's a heading, add it directly
                if elem.name in ['h2', 'h3', 'h4', 'h5', 'h6']:
                    paragraphs.append(elem)

                # If it's a paragraph, apply filters
                elif elem.name == 'p':
                    # Skip if paragraph only contains <em> tag
                    if len(elem.find_all()) == 1 and elem.find('em'):
                        continue

                    # Skip paragraphs with javascript links or image title links
                    p_text = elem.get_text(strip=True)
                    js_link = elem.find('a', href=lambda x: x and x.startswith('javascript:'))
                    if js_link or 'Click vào' in p_text:
                        continue

                    # Skip navigation links (e.g., ">> Xem thêm các dự án...")
                    if p_text.startswith('>>') or 'Xem thêm' in p_text:
                        # Check if it's purely a navigation link (strong>a structure)
                        strong_tag = elem.find('strong')
                        if strong_tag and strong_tag.find('a'):
                            continue

                    # Add valid paragraphs (including those with inline links)
                    paragraphs.append(elem)

            content_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            if content_text:
                content = content_text

        category = "Bất động sản"  # Default

        breadcrumb_links = soup.select('a[itemprop="item"] span[itemprop="name"]')
        if len(breadcrumb_links) >= 2:
            # Lấy item thứ 2 (bỏ qua "Trang chủ")
            category_text = breadcrumb_links[1].get_text(strip=True)
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
