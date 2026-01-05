from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re


class LaoDongScraper(NewsScraperBase):
    """
    Scraper cho LaoDong.vn - crawl từ trang "Tin mới"
    """

    def __init__(self):
        super().__init__()
        self.source = "laodong.vn"
        self.headers['Referer'] = 'https://laodong.vn/'

    def fetch_news(self, max_articles: int = 20) -> List[Tuple]:
        """
        Fetch tin tức từ LaoDong trang "Tin mới"

        Args:
            max_articles: Số bài tối đa cần crawl (mặc định 20)
        """
        all_articles = []
        url = "https://laodong.vn/tin-moi"

        print(f"\n📰 Crawling LaoDong.vn  Tin mới - multi_source_scraper.py")
        print(f"\n📄 Fetching: {url}")

        self.sleep()
        html = self.fetch_html(url)
        if not html:
            print(f"⚠ Failed to fetch page, stopping")
            return all_articles

        # Handle anti-bot cookie redirect (similar to VOV)
        if len(html) < 500 and 'document.cookie' in html and 'window.location.reload' in html:
            print(f"⚠ Antibot detected, extracting cookie and retrying...")

            # Extract cookie from JavaScript
            import re as re_module
            cookie_match = re_module.search(r'document\.cookie\s*=\s*"([^"]+)"', html)
            if cookie_match:
                cookie_str = cookie_match.group(1)
                print(f"→ Setting cookie: {cookie_str[:50]}...")

                # Parse cookie name and value
                cookie_parts = cookie_str.split('=', 1)
                if len(cookie_parts) == 2:
                    cookie_name = cookie_parts[0]
                    cookie_value = cookie_parts[1].split(';')[0]  # Get value before options

                    # Set cookie in session
                    self.session.cookies.set(cookie_name, cookie_value, domain='laodong.vn', path='/')

                    # Retry request with cookie
                    self.sleep()
                    html = self.fetch_html(url)
                    if not html:
                        print(f"⚠ Failed to fetch page after cookie, stopping")
                        return all_articles
                    print(f"✓ Got HTML with cookie: {len(html)} chars")
            else:
                print(f"⚠ Could not extract cookie, stopping")
                return all_articles

        # Parse listing page
        soup = BeautifulSoup(html, 'html.parser')

        # Find all article tags - LaoDong uses <article> tags for news items
        articles = soup.find_all('article')

        if not articles:
            print(f"⚠ No article tags found")
            return all_articles

        print(f"Found {len(articles)} article tags on page")

        # Extract links from articles
        article_links = []
        for article in articles:
            # Find the main link in the article (usually first link or link in title)
            link_el = article.find('a')
            if link_el:
                href = link_el.get('href', '')
                if href:
                    # Make sure link is absolute
                    if not href.startswith('http'):
                        href = f"https://laodong.vn{href}"

                    # Filter out non-article links
                    # Valid article URLs: /xa-hoi/..., /the-thao/..., /suc-khoe/...
                    if (href not in article_links and
                        '/tin-moi' not in href and
                        '/thong-tin-doanh-nghiep' not in href and
                        not href.endswith('laodong.vn/') and
                        href.count('/') >= 4): 
                        article_links.append(href)

        if not article_links:
            print(f"⚠ No valid article links found")
            return all_articles

        # Limit to requested number of articles
        article_links = article_links[:max_articles]
        print(f"Found {len(article_links)} article URLs")

        # Fetch article details
        for i, article_url in enumerate(article_links, 1):
            print(f"[{i}/{len(article_links)}] Fetching: {article_url[:60]}...", flush=True)
            self.sleep()

            article_data = self._fetch_article_detail(article_url)
            if article_data:
                all_articles.append(article_data)

        print(f"\n✓ Total articles collected: {len(all_articles)}")
        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo LaoDong"""
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

        # Extract date from span.time
        # Format: "Thứ năm, 01/01/2026 21:59 (GMT+7)"
        published_at = 0
        date_el = soup.select_one('span.time')

        if date_el:
            date_text = date_el.get_text(strip=True)
            # Remove day of week and GMT info
            # "Thứ năm, 01/01/2026 21:59 (GMT+7)" -> "01/01/2026 21:59"
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

        # Extract category from a.main-cat-lnk
        category = "TIN MỚI" 

        category_el = soup.select_one('a.main-cat-lnk')
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
