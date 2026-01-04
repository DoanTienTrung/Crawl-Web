from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re


class NLDScraper(NewsScraperBase):
    """
    Scraper cho NLD.com.vn (Người Lao Động) - crawl từ trang "Tin 24h"
    """

    def __init__(self):
        super().__init__()
        self.source = "nld.com.vn"
        self.headers['Referer'] = 'https://nld.com.vn/'

    def fetch_news(self, max_articles: int = 20) -> List[Tuple]:
        """
        Fetch tin tức từ NLD trang "Tin 24h"

        Args:
            max_articles: Số bài tối đa cần crawl (mặc định 20)
        """
        all_articles = []
        url = "https://nld.com.vn/tin-24h.htm"

        print(f"\n📰 Crawling NLD.com.vn  Tin 24h")
        print(f"\n📄 Fetching: {url}")

        self.sleep()
        html = self.fetch_html(url)
        if not html:
            print(f"⚠ Failed to fetch page, stopping")
            return all_articles

        # Parse listing page
        soup = BeautifulSoup(html, 'html.parser')

        # Find all article links on the page
        article_links = []

        # Try multiple selectors to find articles
        for selector in ['article a', '.article-item a', '.news-item a', 'h3 a', 'h2 a', '.box-category-item a']:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get('href', '')
                    if href and not href.startswith('javascript:') and not href.startswith('#'):
                        # Make sure link is absolute
                        if not href.startswith('http'):
                            href = f"https://nld.com.vn{href}"
                        # Filter to only include article URLs (not category pages, etc.)
                        if '/tin-24h' not in href and '.htm' in href and href not in article_links:
                            article_links.append(href)

                if article_links:
                    break

        if not article_links:
            print(f"⚠ No articles found")
            return all_articles

        # Limit to requested number of articles
        article_links = article_links[:max_articles]
        print(f"Found {len(article_links)} article URLs")

        # Fetch article details
        for i, article_url in enumerate(article_links, 1):
            print(f"[{i}/{len(article_links)}] Fetching: {article_url[:60]}...")
            self.sleep()

            article_data = self._fetch_article_detail(article_url)
            if article_data:
                all_articles.append(article_data)

        print(f"\n✓ Total articles collected: {len(all_articles)}")
        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo NLD"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract title
        title_el = soup.select_one('h1') or soup.select_one('.article-title')
        title = title_el.get_text(strip=True) if title_el else ''

        if not title:
            print(f"✗ No title found for: {link[:60]}...")
            return None

        # Extract date from time[data-role="publishdate"]
        # Format: <time data-role="publishdate" datetime="2026-01-01T21:35:00+07:00">01/01/2026 21:35 GMT+7</time>
        published_at = 0
        date_el = soup.select_one('time[data-role="publishdate"]')

        if date_el:
            # Try to use datetime attribute first (ISO format)
            datetime_attr = date_el.get('datetime', '')
            if datetime_attr:
                try:
                    # Parse ISO format: 2026-01-01T21:35:00+07:00
                    from dateutil import parser
                    dt = parser.parse(datetime_attr)
                    published_at = int(dt.timestamp())
                except:
                    # Fallback to text parsing
                    date_text = date_el.get_text(strip=True)
                    # Format: "01/01/2026 21:35 GMT+7"
                    date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})', date_text)
                    if date_match:
                        day, month, year, hour, minute = date_match.groups()
                        try:
                            dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                            published_at = int(dt.timestamp())
                        except Exception as e:
                            print(f"⚠ Could not parse date '{date_text}': {e}")
            else:
                # No datetime attribute, parse text
                date_text = date_el.get_text(strip=True)
                date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})', date_text)
                if date_match:
                    day, month, year, hour, minute = date_match.groups()
                    try:
                        dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                        published_at = int(dt.timestamp())
                    except Exception as e:
                        print(f"⚠ Could not parse date '{date_text}': {e}")

        # Extract content
        content_el = soup.select_one('.detail-content') or soup.select_one('.article-content') or soup.select_one('[itemprop="articleBody"]')
        content = ""

        if content_el:
            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # Extract category from a.category-name_ac[data-role="cate-name"]
        # <a href="/the-thao.htm" title="Thể thao" class="category-name_ac" data-role="cate-name">Thể thao</a>
        category = "TIN 24H"  

        category_el = soup.select_one('a.category-name_ac[data-role="cate-name"]')
        if category_el:
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
