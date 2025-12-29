"""
News Scrapers - Convert từ Rust sang Python
Hỗ trợ các nguồn: CafeF, VnExpress, VnEconomy, VOV, Vietnamnet
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
from typing import List, Tuple, Optional
import gzip
import brotli
from io import BytesIO


class NewsScraperBase:
    """Base class cho tất cả news scrapers"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-IN,en-US;q=0.9,en;q=0.8,vi;q=0.7',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }
        self.delay = 2  # Delay giữa các request (giây)
    
    def fetch_html(self, url: str) -> Optional[str]:
        """Fetch và decode HTML từ URL"""
        try:
            resp = self.session.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            
            # Handle content encoding
            content_encoding = resp.headers.get('Content-Encoding', '')
            
            if 'br' in content_encoding:
                try:
                    return brotli.decompress(resp.content).decode('utf-8')
                except:
                    pass
            
            if 'gzip' in content_encoding:
                try:
                    return gzip.decompress(resp.content).decode('utf-8')
                except:
                    pass
            
            return resp.text
            
        except Exception as e:
            print(f"✗ Error fetching {url}: {e} - multi_source_scraper.py:54")
            return None
    
    def parse_date_to_timestamp(self, date_str: str, format_str: str) -> int:
        """Parse date string thành Unix timestamp"""
        try:
            dt = datetime.strptime(date_str.strip(), format_str)
            return int(dt.timestamp())
        except Exception as e:
            print(f"⚠ Could not parse date '{date_str}': {e} - multi_source_scraper.py:63")
            return 0
    
    def sleep(self):
        """Delay giữa các request"""
        time.sleep(self.delay)


class VnExpressScraper(NewsScraperBase):
    """
    Scraper cho VnExpress.net - crawl từ trang "Tin tức 24h"
    """

    def __init__(self):
        super().__init__()
        self.source = "vnexpress.net"
        self.headers['Referer'] = 'https://vnexpress.net/'

    def fetch_news(self, max_pages: int = 3) -> List[Tuple]:
        """
        Fetch tin tức từ VnExpress trang "Tin tức 24h"

        Args:
            max_pages: Số trang tối đa cần crawl (mặc định 3)
        """
        all_articles = []

        print(f"\n📰 Crawling VnExpress.net - Tin tức 24h")

        for page in range(1, max_pages + 1):
            self.sleep()

            # Build URL
            if page == 1:
                url = "https://vnexpress.net/tin-tuc-24h"
            else:
                url = f"https://vnexpress.net/tin-tuc-24h-p{page}"

            print(f"\n📄 Page {page}/{max_pages}: {url}")

            html = self.fetch_html(url)
            if not html:
                print(f"⚠ Failed to fetch page {page}, skipping")
                continue

            # Parse listing page
            soup = BeautifulSoup(html, 'html.parser')
            articles = soup.select('article.item-news')

            if not articles:
                print(f"⚠ No articles found on page {page}")
                continue

            print(f"Found {len(articles)} articles on page {page}")

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
                    print(f"✗ Error parsing article: {e}")
                    continue

        print(f"\n✓ Total articles collected: {len(all_articles)}")
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
                category = category_text

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


class VnEconomyScraper(NewsScraperBase):
    """
    Scraper cho VnEconomy.vn
    Tương tự hàm fetch_vneconomy_titles_and_links trong Rust
    """
    
    def __init__(self):
        super().__init__()
        self.source = "vneconomy.vn"
        self.headers['Referer'] = 'https://vneconomy.vn/'
        self.categories = [
            "tai-chinh",
            "thi-truong", 
            "nhip-cau-doanh-nghiep",
            "dia-oc",
            "kinh-te-the-gioi",
        ]
    
    def fetch_news(self, max_pages: int = 2) -> List[Tuple]:
        """Fetch tin tức từ VnEconomy"""
        all_articles = []
        
        for category in self.categories:
            print(f"\n📂 Category: {category} - multi_source_scraper.py:208")
            
            for page in range(1, max_pages + 1):
                self.sleep()
                
                url = f"https://vneconomy.vn/{category}.htm?page={page}"
                print(f"Fetching page {page}: {url} - multi_source_scraper.py:214")
                
                html = self.fetch_html(url)
                if not html:
                    continue
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Select articles
                items = soup.select('div.grid-new-column_item.mt-48 > div.featured-row_item.featured-column_item')
                
                for item in items:
                    try:
                        # Extract title
                        title_el = item.select_one('div.featured-row_item__title > h3')
                        title = title_el.get('title', '') if title_el else ''
                        
                        # Extract link
                        link_el = item.select_one('a.link-layer-imt')
                        href = link_el.get('href', '') if link_el else ''
                        link = f"https://vneconomy.vn{href}" if href else ''
                        
                        if not title or not link:
                            continue
                        
                        # Fetch article detail
                        self.sleep()
                        article_data = self._fetch_article_detail(link, title, category)
                        if article_data:
                            all_articles.append(article_data)
                            
                    except Exception as e:
                        print(f"✗ Error parsing article: {e} - multi_source_scraper.py:246")
                        continue
        
        return all_articles
    
    def _fetch_article_detail(self, link: str, title: str, category: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo"""
        html = self.fetch_html(link)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract date
        # Format: "24/12/2025, 10:30"
        date_el = soup.select_one('div.date-detail p.date')
        published_at = 0
        
        if date_el:
            date_text = date_el.get_text(strip=True)
            published_at = self.parse_date_to_timestamp(date_text, "%d/%m/%Y, %H:%M")
        
        # Extract content
        body_el = soup.select_one('div[data-field="body"]')
        content = ""
        if body_el:
            paragraphs = body_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
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


class VOVScraper(NewsScraperBase):
    """
    Scraper cho VOV.vn - crawl từ trang "Tin mới cập nhật"
    """

    def __init__(self):
        super().__init__()
        self.source = "vov.vn"
        self.headers['Referer'] = 'https://vov.vn/'
        self.delay = 3  # VOV cần delay lâu hơn

    def fetch_news(self, max_pages: int = 3) -> List[Tuple]:
        """
        Fetch tin tức từ VOV trang "Tin mới cập nhật"

        Args:
            max_pages: Số trang tối đa cần crawl (mặc định 3)
        """
        all_articles = []

        print(f"\n📰 Crawling VOV.vn - Tin mới cập nhật")

        # Pagination: page 0, page 1, page 2, ...
        for page in range(max_pages):
            if page == 0:
                url = "https://vov.vn/tin-moi-cap-nhat"
            else:
                url = f"https://vov.vn/tin-moi-cap-nhat?page={page}"

            print(f"\n  📄 Page {page + 1}/{max_pages}: {url}")
            self.sleep()

            html = self.fetch_html(url)
            if not html:
                print(f"  ⚠ Failed to fetch page {page}, stopping")
                break

            # Check for anti-bot redirect (VOV uses multiple levels of JavaScript redirects)
            max_redirects = 5
            redirect_count = 0
            import re as re_module
            from urllib.parse import unquote

            while ('Attention Required' in html or 'window.location.href' in html) and redirect_count < max_redirects:
                redirect_count += 1
                print(f"  ⚠ Anti-bot detected (level {redirect_count}), extracting redirect URL...")

                # Extract redirect URL from JavaScript
                match = re_module.search(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', html)
                if match:
                    redirect_url = match.group(1)
                    redirect_url = unquote(redirect_url)
                    print(f"  → Redirecting to: {redirect_url[:80]}...")

                    # Fetch the redirect URL
                    self.sleep()
                    html = self.fetch_html(redirect_url)
                    if not html:
                        print(f"  ⚠ Failed to fetch redirect URL, stopping")
                        break
                    print(f"  DEBUG: After redirect {redirect_count}, HTML length: {len(html)}")
                else:
                    print(f"  ⚠ Could not extract redirect URL, stopping")
                    break

            # If we still have anti-bot page after max redirects, stop
            if redirect_count >= max_redirects and 'Attention Required' in html:
                print(f"  ⚠ Max redirects ({max_redirects}) reached, still getting anti-bot page. Stopping.")
                break

            soup = BeautifulSoup(html, 'html.parser')

            # Select taxonomy-content divs
            content_divs = soup.select('div.taxonomy-content')

            # Debug: Show what we found
            print(f"  DEBUG: Found {len(content_divs)} div.taxonomy-content")

            if not content_divs:
                print(f"  ⚠ No articles found on page {page}, stopping")
                # Debug: Try alternative selector
                alt_divs = soup.select('.card')
                print(f"  DEBUG: Alternative .card selector found {len(alt_divs)} elements")
                break

            print(f"  Found {len(content_divs)} articles on page {page}")

            for div in content_divs:
                try:
                    # Extract title
                    title_el = div.select_one('h5.media-title') or div.select_one('h3.card-title')
                    title = title_el.get_text(strip=True) if title_el else ''

                    # Extract link
                    link_el = div.select_one('a.vovvn-title')
                    href = link_el.get('href', '') if link_el else ''
                    link = href if href.startswith('http') else f"https://vov.vn{href}"

                    # Extract description
                    desc_el = div.select_one('p.mt-2')
                    description = desc_el.get_text(strip=True) if desc_el else ''

                    if not title or not link:
                        continue

                    # Fetch article detail
                    self.sleep()
                    article_data = self._fetch_article_detail(link, title, description)
                    if article_data:
                        all_articles.append(article_data)

                except Exception as e:
                    print(f"  ✗ Error parsing article: {e}")
                    continue

            # Check pagination để xem có trang tiếp theo không
            pagination = soup.select_one('ul.pagination')
            if not pagination:
                print(f"  ⚠ No pagination found, stopping")
                break

        print(f"\n  ✓ Total articles collected: {len(all_articles)}")
        return all_articles
    
    def _fetch_article_detail(self, link: str, title: str, description: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo"""
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract date
        # Format mới: "Thứ Hai, 16:54, 29/12/2025" trong div.col-md-4.mb-2
        # Format cũ: "Thứ Ba, 22:35, 26/08/2025" trong .article-date .col-md-4
        published_at = int(datetime.now().timestamp())  # Default to now

        # Thử selector mới trước
        date_el = soup.select_one('div.col-md-4.mb-2') or soup.select_one('.article-date .col-md-4')

        if date_el:
            date_text = date_el.get_text(strip=True)
            # Format: "Thứ Hai, 16:54, 29/12/2025"
            parts = [p.strip() for p in date_text.split(',')]
            if len(parts) >= 3:
                time_part = parts[1]  # "16:54"
                date_part = parts[2]  # "29/12/2025"
                datetime_str = f"{date_part} {time_part}"
                parsed_ts = self.parse_date_to_timestamp(datetime_str, "%d/%m/%Y %H:%M")
                if parsed_ts > 0:
                    published_at = parsed_ts

        # Extract content
        content_el = soup.select_one('div.row.article-content div.col div.text-long')
        content = description

        if content_el:
            paragraphs = content_el.select('p')
            content_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            if content_text:
                content = content_text

        # Extract category từ breadcrumb
        category = "Tin tức"  # Default

        # Tìm từ breadcrumb: li.breadcrumb-item a
        breadcrumb_links = soup.select('li.breadcrumb-item a, .breadcrumb a')
        if breadcrumb_links:
            # Thường item đầu tiên là category chính
            # VD: <li class="breadcrumb-item"><a href="/chinh-tri">CHÍNH TRỊ</a></li>
            category_el = breadcrumb_links[0]
            category_text = category_el.get_text(strip=True)
            if category_text and category_text.lower() not in ['trang chủ', 'home', 'vov']:
                category = category_text

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


class VietnametScraper(NewsScraperBase):
    """
    Scraper cho Vietnamnet.vn
    Tương tự hàm fetch_vietnamnet_news trong Rust
    """
    
    def __init__(self):
        super().__init__()
        self.source = "vietnamnet.vn"
        self.headers['Referer'] = 'https://vietnamnet.vn/'
    
    def fetch_news(self, max_pages: int = None, target_date: str = None) -> List[Tuple]:
        """
        Fetch tin tức từ Vietnamnet (tin tức 24h by date)

        Args:
            max_pages: Số trang tối đa cần crawl. Nếu None, sẽ crawl tất cả các trang
            target_date: Ngày cần crawl theo format 'dd/mm/yyyy'. Nếu None, dùng ngày hiện tại
        """
        all_articles = []

        # Get date for the bydate parameter
        if target_date:
            date_str = target_date
        else:
            today = datetime.now()
            date_str = today.strftime("%d/%m/%Y")

        print(f"\n📅 Crawling Vietnamnet for date: {date_str} - multi_source_scraper.py:426")

        # Start from page 0
        page = 0

        while True:
            # Build URL with date filter
            url = f"https://vietnamnet.vn/tin-tuc-24h-p{page}?bydate={date_str}-{date_str}&cate="

            print(f"\n  📄 Page {page}: {url} - multi_source_scraper.py:435")
            self.sleep()

            html = self.fetch_html(url)
            if not html:
                print(f"⚠ Failed to fetch page {page}, stopping - multi_source_scraper.py:440")
                break

            soup = BeautifulSoup(html, 'html.parser')

            # Select posts
            posts = soup.select('div.horizontalPost.version-news')

            if not posts:
                print(f"⚠ No articles found on page {page}, stopping - multi_source_scraper.py:449")
                break

            print(f"Found {len(posts)} articles on page {page} - multi_source_scraper.py:452")

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
                    print(f"✗ Error parsing article: {e} - multi_source_scraper.py:475")
                    continue

            # Check if we should continue to next page
            if max_pages is not None and page >= max_pages - 1:
                print(f"Reached max_pages limit ({max_pages}) - multi_source_scraper.py:480")
                break

            # Check if there's a next page by reading pagination numbers
            pagination = soup.select_one('div.pagination ul.pagination__list')
            if not pagination:
                print(f"No pagination found, stopping - multi_source_scraper.py:486")
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
                print(f"Pagination detected: pages 1{max_page_num} (current: page {page + 1}) - multi_source_scraper.py:500")

                # Current page is 0-indexed, but display is 1-indexed
                # If we're at the last page, stop
                if page + 1 >= max_page_num:
                    print(f"Reached the last page ({page + 1}/{max_page_num}) - multi_source_scraper.py:505")
                    break
            else:
                print(f"No page numbers found in pagination, stopping - multi_source_scraper.py:508")
                break

            # Move to next page
            page += 1

        print(f"\n  ✓ Total articles collected: {len(all_articles)} from {page + 1} page(s) - multi_source_scraper.py:514")
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


class CafeFScraper(NewsScraperBase):
    """
    Scraper cho CafeF.vn
    """
    
    def __init__(self):
        super().__init__()
        self.source = "cafef.vn"
        self.headers['Referer'] = 'https://cafef.vn/'

    def fetch_news(self, max_pages: int = 4, max_articles_per_page: int = 20) -> List[Tuple]:
        """
        Fetch tin tức từ CafeF từ trang /doc-nhanh

        Args:
            max_pages: Số trang tối đa (mặc định 4)
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

            print(f"\n📄 Page {page}/{max_pages}: {url}")
            self.sleep()

            html = self.fetch_html(url)
            if not html:
                print(f"⚠ Failed to fetch page {page}, skipping")
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
                print(f"⚠ No new articles on page {page}")
                continue

            print(f"Found {len(article_urls)} new article URLs on page {page}")

            # Limit articles per page
            article_urls = article_urls[:max_articles_per_page]

            # Fetch article details
            for i, article_url in enumerate(article_urls, 1):
                print(f"  [{i}/{len(article_urls)}] Fetching: {article_url[:60]}...")
                self.sleep()

                article_data = self._fetch_article_detail(article_url)
                if article_data:
                    all_articles.append(article_data)

        print(f"\n✓ Total articles collected: {len(all_articles)}")
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
            category = category_el.get_text(strip=True)
            if not category:  # Nếu text rỗng, thử lấy từ title attribute
                category = category_el.get('title', 'ĐỌC NHANH').strip()

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
