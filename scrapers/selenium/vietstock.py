from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re


class VietStockScraper(NewsScraperBase):
    """Scraper cho VietStock.vn - crawl từ trang Mới cập nhật sử dụng Selenium"""

    def __init__(self):
        super().__init__()
        self.source = "vietstock.vn"
        self.headers['Referer'] = 'https://vietstock.vn/'

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        """
        Fetch tin tức từ VietStock trang Mới cập nhật bằng Selenium

        Args:
            max_articles: Số bài tối đa cần crawl (mặc định 15)
        """
        all_articles = []
        url = "https://vietstock.vn/chu-de/1-2/moi-cap-nhat.htm"

        print(f"\n📰 Crawling VietStock.vn  Mới cập nhật (with Selenium)")
        print(f"\n📄 Fetching: {url}")

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')

        import os
        chrome_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        ]
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                chrome_options.binary_location = chrome_path
                break

        driver = None
        try:
            print("→ Starting Chrome browser...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.get(url)

            print("→ Waiting for page to load...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='.htm']"))
            )

            import time
            time.sleep(2)

            html = driver.page_source
            print(f"✓ Got rendered HTML: {len(html)} chars")

        except Exception as e:
            print(f"⚠ Selenium error: {e}")
            return all_articles
        finally:
            if driver:
                driver.quit()
                print("→ Browser closed")

        soup = BeautifulSoup(html, 'html.parser')

        # Find all article links
        # URL pattern: /YYYY/MM/article-slug-###-XXXXXXX.htm
        article_links = []

        titled_links = soup.find_all('a', title=True, href=lambda x: x and '.htm' in x)

        for link in titled_links:
            href = link.get('href', '')
            title = link.get('title', '')

            if not href or href.startswith('javascript:') or href.startswith('#'):
                continue

            if '/chu-de/' in href:
                continue

            if not href.startswith('http'):
                if href.startswith('//'):
                    href = 'https:' + href
                else:
                    href = f"https://vietstock.vn{href}"

            # Article filter: must have title, proper URL depth, and year in path
            if (len(title) > 10 and
                href.count('/') >= 5 and
                href not in article_links and
                '/20' in href):

                article_links.append(href)

        if not article_links:
            print(f"⚠ No articles found")
            return all_articles

        article_links = article_links[:max_articles]
        print(f"Found {len(article_links)} article URLs")

        for i, article_url in enumerate(article_links, 1):
            print(f"[{i}/{len(article_links)}] Fetching: {article_url[:60]}...", flush=True)
            self.sleep()

            article_data = self._fetch_article_detail(article_url)
            if article_data:
                all_articles.append(article_data)

        print(f"\n✓ Total articles collected: {len(all_articles)}")
        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo VietStock"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        title_el = soup.select_one('h1') or soup.select_one('.article-title')
        title = title_el.get_text(strip=True) if title_el else ''

        if not title:
            print(f"✗ No title found for: {link[:60]}...")
            return None

        # Extract date
        # Priority 1: Meta tag article:published_time (ISO format)
        # Priority 2: span.datenew
        published_at = 0

        # Try meta tag first (ISO format: 2026-01-01T21:11:44+07:00)
        meta_date = soup.find('meta', property='article:published_time')
        if meta_date and meta_date.get('content'):
            try:
                from dateutil import parser
                dt = parser.parse(meta_date.get('content'))
                published_at = int(dt.timestamp())
            except Exception as e:
                print(f"⚠ Could not parse meta date: {e}")

        # Fallback to span.datenew (format: 01-01-2026 21:11:44+07:00)
        if published_at == 0:
            date_el = soup.select_one('span.datenew')
            if date_el:
                date_text = date_el.get_text(strip=True)
                try:
                    from dateutil import parser
                    dt = parser.parse(date_text)
                    published_at = int(dt.timestamp())
                except Exception:
                    # Fallback to regex
                    date_match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})', date_text)
                    if date_match:
                        day, month, year, hour, minute, second = date_match.groups()
                        try:
                            dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                            published_at = int(dt.timestamp())
                        except Exception as e:
                            print(f"⚠ Could not parse date '{date_text}': {e}")

        content_el = soup.select_one('.detail-content') or soup.select_one('.article-content') or soup.select_one('[itemprop="articleBody"]')
        content = ""

        if content_el:
            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # Extract category from breadcrumb: <a href="/kinh-te.htm" itemprop="item" title="Kinh tế" class="bcrumbs-item"><span itemprop="name">Kinh tế</span></a>
        category = "MỚI CẬP NHẬT"

        breadcrumb_links = soup.select('a.bcrumbs-item[itemprop="item"]')
        if len(breadcrumb_links) >= 2:
            # Skip first (usually Trang chủ), take second as category
            category_el = breadcrumb_links[1]
            category_span = category_el.select_one('span[itemprop="name"]')
            if category_span:
                category_text = category_span.get_text(strip=True)
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
