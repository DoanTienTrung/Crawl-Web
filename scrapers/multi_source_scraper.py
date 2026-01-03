
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
from typing import List, Tuple, Optional
import gzip
import brotli
from io import BytesIO
import copy
import html


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


class VnEconomyScraper(NewsScraperBase):
    """
    Scraper cho VnEconomy.vn sử dụng RSS Feed
    """
    
    def __init__(self):
        super().__init__()
        self.source = "vneconomy.vn"
        self.rss_url = "https://vneconomy.vn/tin-moi.rss"

    def fetch_news(self, max_articles: int = 20) -> List[Tuple]:
        """Fetch tin tức từ VnEconomy qua RSS"""
        all_articles = []
        
        print(f"\n📰 Fetching VnEconomy RSS: {self.rss_url}")
        
        # Sử dụng feedparser để đọc RSS
        feed = feedparser.parse(self.rss_url)
        
        if not feed.entries:
            print("⚠ Không tìm thấy bài viết nào trong RSS feed.")
            return []

        # Giới hạn số lượng bài viết
        entries = feed.entries[:max_articles]
        print(f"✓ Tìm thấy {len(entries)} bài viết từ RSS.")

        for entry in entries:
            try:
                # 1. Tiêu đề
                title = entry.title

                # 2. Link
                link = entry.link

                # 3. Ngày xuất bản (Chuyển sang timestamp)
                # pubDate format: Fri, 02 Jan 2026 09:06:03 GMT
                published_at = int(datetime.now().timestamp())
                if hasattr(entry, 'published_parsed'):
                    published_at = int(datetime(*entry.published_parsed[:6]).timestamp())

                # 4. Nội dung (Ưu tiên content:encoded vì nó đầy đủ nhất)
                content = ""
                if hasattr(entry, 'content'):
                    # content thường là một list các dict
                    raw_content = entry.content[0].value
                    content = self._clean_rss_content(raw_content)
                elif hasattr(entry, 'description'):
                    content = self._clean_rss_content(entry.description)

                # 5. Chuyên mục
                category = "TIN MỚI"
                if hasattr(entry, 'category'):
                    category = entry.category.upper()

                # 6. Tác giả (Nếu có trong RSS)
                author = "NA"
                if hasattr(entry, 'author'):
                    author = entry.author

                article_data = (
                    published_at,
                    title,
                    link,
                    content,
                    self.source,
                    author,
                    "NA",
                    False,
                    category,
                )
                all_articles.append(article_data)
                
            except Exception as e:
                print(f"✗ Lỗi khi xử lý item RSS: {e}")
                continue

        print(f"✓ Đã xử lý xong {len(all_articles)} bài viết.")
        return all_articles

    def _clean_rss_content(self, raw_html: str) -> str:
        """Làm sạch HTML trong nội dung RSS"""
        if not raw_html:
            return ""
        
        # Decode các ký tự thực thể như &#237; -> í
        decoded_html = html.unescape(raw_html)
        
        # Sử dụng BeautifulSoup để loại bỏ toàn bộ tag HTML
        soup = BeautifulSoup(decoded_html, 'html.parser')
        
        # VnEconomy thường để tóm tắt trong thẻ <h2>, ta lấy cả <h2> và <p>
        text_parts = []
        for tag in soup.find_all(['h2', 'p']):
            txt = tag.get_text(strip=True)
            if txt:
                text_parts.append(txt)
                
        cleaned_text = " ".join(text_parts)
        
        # Nếu không tìm thấy h2/p thì lấy toàn bộ text
        if not cleaned_text:
            cleaned_text = soup.get_text(" ", strip=True)
            
        return cleaned_text

class VOVScraper(NewsScraperBase):
    """
    Scraper cho VOV.vn - crawl từ trang "Tin mới cập nhật"
    """

    def __init__(self):
        super().__init__()
        self.source = "vov.vn"
        self.headers['Referer'] = 'https://vov.vn/'
        self.delay = 3  # VOV cần delay lâu hơn

    def fetch_news(self, max_pages: int = 1) -> List[Tuple]:
        """
        Fetch tin tức từ VOV trang "Tin mới cập nhật"

        Args:
            max_pages: Số trang tối đa cần crawl (mặc định 1)
        """
        all_articles = []

        print(f"\n📰 Crawling VOV.vn  Tin mới cập nhật - multi_source_scraper.py:364")

        # Pagination: page 0, page 1, page 2, ...
        for page in range(max_pages):
            if page == 0:
                url = "https://vov.vn/tin-moi-cap-nhat"
            else:
                url = f"https://vov.vn/tin-moi-cap-nhat?page={page}"

            print(f"\n  📄 Page {page + 1}/{max_pages}: {url} - multi_source_scraper.py:373")
            self.sleep()

            html = self.fetch_html(url)
            if not html:
                print(f"⚠ Failed to fetch page {page}, stopping - multi_source_scraper.py:378")
                break

            # Check for anti-bot redirect (VOV uses multiple levels of JavaScript redirects)
            max_redirects = 5
            redirect_count = 0
            import re as re_module
            from urllib.parse import unquote

            while ('Attention Required' in html or 'window.location.href' in html) and redirect_count < max_redirects:
                redirect_count += 1
                print(f"⚠ Antibot detected (level {redirect_count}), extracting redirect URL... - multi_source_scraper.py:389")

                # Extract redirect URL from JavaScript
                match = re_module.search(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', html)
                if match:
                    redirect_url = match.group(1)
                    redirect_url = unquote(redirect_url)
                    print(f"→ Redirecting to: {redirect_url[:80]}... - multi_source_scraper.py:396")

                    # Fetch the redirect URL
                    self.sleep()
                    html = self.fetch_html(redirect_url)
                    if not html:
                        print(f"⚠ Failed to fetch redirect URL, stopping - multi_source_scraper.py:402")
                        break
                    print(f"DEBUG: After redirect {redirect_count}, HTML length: {len(html)} - multi_source_scraper.py:404")
                else:
                    print(f"⚠ Could not extract redirect URL, stopping - multi_source_scraper.py:406")
                    break

            # If we still have anti-bot page after max redirects, stop
            if redirect_count >= max_redirects and 'Attention Required' in html:
                print(f"⚠ Max redirects ({max_redirects}) reached, still getting antibot page. Stopping. - multi_source_scraper.py:411")
                break

            soup = BeautifulSoup(html, 'html.parser')

            # Select taxonomy-content divs
            content_divs = soup.select('div.taxonomy-content')

            # Debug: Show what we found
            print(f"DEBUG: Found {len(content_divs)} div.taxonomycontent - multi_source_scraper.py:420")

            if not content_divs:
                print(f"⚠ No articles found on page {page}, stopping - multi_source_scraper.py:423")
                # Debug: Try alternative selector
                alt_divs = soup.select('.card')
                print(f"DEBUG: Alternative .card selector found {len(alt_divs)} elements - multi_source_scraper.py:426")
                break

            print(f"Found {len(content_divs)} articles on page {page} - multi_source_scraper.py:429")

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
                    print(f"✗ Error parsing article: {e} - multi_source_scraper.py:456")
                    continue

            # Check pagination để xem có trang tiếp theo không
            pagination = soup.select_one('ul.pagination')
            if not pagination:
                print(f"⚠ No pagination found, stopping - multi_source_scraper.py:462")
                break

        print(f"\n  ✓ Total articles collected: {len(all_articles)} - multi_source_scraper.py:465")
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

        # Extract category
        category = "Tin tức"  # Giá trị mặc định

        # Ưu tiên 1: Lấy từ navbar chuyên mục 
        # Cấu trúc: <a class="navbar-brand special-header-title" ...>
        nav_category = soup.select_one('a.special-header-title')
        
        # Ưu tiên 2: Lấy từ breadcrumb 
        # Cấu trúc: li.breadcrumb-item-first a
        breadcrumb_category = soup.select_one('li.breadcrumb-item-first a, .breadcrumb-item a')

        if nav_category:
            category = nav_category.get_text(strip=True)
        elif breadcrumb_category:
            category = breadcrumb_category.get_text(strip=True)

        # Chuẩn hóa: Nếu lấy trúng chữ "Trang chủ" thì đặt lại mặc định
        if category.lower() in ['trang chủ', 'home', 'vov.vn', 'vov']:
            category = "Tin tức"
            
        # Chuyển thành chữ hoa để đồng bộ dữ liệu
        category = category.upper()

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

        # Extract date từ div.info-date.right
        # Format: "31/12/2025 9:05 PM"
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

        # Extract category từ breadcrumb
        # <a itemprop="item"><span itemprop="name">Thị Trường</span></a>
        # Breadcrumb có dạng: [Trang chủ, Thị Trường, Thị Trường Bất Động Sản]
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
                print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:60]}... - multi_source_scraper.py:993")
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


class DanTriRSSScraper(NewsScraperBase):
    """
    Scraper cho DanTri.com.vn sử dụng RSS Feed
    """

    def __init__(self):
        super().__init__()
        self.source = "dantri.com.vn"
        self.rss_url = "https://dantri.com.vn/rss/tin-moi-nhat.rss"

    def fetch_news(self) -> List[Tuple]:
        """
        Lấy tối đa 20 tin tức mới nhất từ RSS feed của Dân trí
        """
        all_articles = []
        print(f"\n📡 Đang đọc RSS từ: {self.rss_url} - multi_source_scraper.py:1084")
        
        # 1. Sử dụng feedparser để đọc nội dung RSS
        feed = feedparser.parse(self.rss_url)
        
        if not feed.entries:
            print("⚠ Không tìm thấy bài viết nào trong RSS. - multi_source_scraper.py:1090")
            return []

        # 2. Giới hạn chỉ xử lý 20 bài viết đầu tiên
        entries_to_process = feed.entries[:20]
        print(f"Tìm thấy {len(feed.entries)} bài. Sẽ xử lý {len(entries_to_process)} bài mới nhất. - multi_source_scraper.py:1095")

        for entry in entries_to_process:
            link = entry.link
            
            # Lấy Category trực tiếp từ thẻ <category> của RSS để đảm bảo độ chính xác (ví dụ: Chính trị)
            rss_category = getattr(entry, 'category', 'TIN MỚI')
            
            print(f"Fetching: {link[:60]}... - multi_source_scraper.py:1103")
            self.sleep()
            
            # Truyền rss_category vào hàm detail để xử lý
            article_data = self._fetch_article_detail(link, rss_category)
            if article_data:
                all_articles.append(article_data)

        print(f"\n✓ Tổng số bài viết thu thập được: {len(all_articles)} - multi_source_scraper.py:1111")
        return all_articles

    def _fetch_article_detail(self, link: str, rss_category: str = None) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo từ Dân trí"""
        html = self.fetch_html(link)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Trích xuất Tiêu đề
        title_el = soup.select_one('h1.title-page') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''
        
        if not title:
            return None
        
        # 2. Trích xuất Ngày xuất bản
        published_at = 0
        date_el = soup.select_one('.author-time')
        if date_el:
            date_text = date_el.get_text(strip=True)
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s*-\s*(\d{1,2}):(\d{2})', date_text)
            if date_match:
                day, month, year, hour, minute = date_match.groups()
                try:
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    published_at = int(dt.timestamp())
                except:
                    pass
        
        # 3. Trích xuất Nội dung
        content = ""
        content_el = soup.select_one('.singular-content')
        if content_el:
            # Loại bỏ quảng cáo và video liên quan
            for unwanted in content_el.select('.gui-check-parent, .video-content-wrapper, .ad-container'):
                unwanted.decompose()
                
            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # 4. Trích xuất Chuyên mục (Ưu tiên từ RSS)
        if rss_category and rss_category != "TIN MỚI":
            category = rss_category
        else:
            # Dự phòng lấy từ Meta Tag nếu RSS thiếu
            meta_cate = soup.find('meta', property='article:section')
            category = meta_cate.get('content') if meta_cate else "TIN MỚI"

        category = category.upper().strip()

        return (
            published_at,
            title,
            link,
            content,
            self.source,
            "NA",   # stock_related
            "NA",   # sentiment_score
            False,  # server_pushed
            category,
        )


class ThanhNienRSSScraper(NewsScraperBase):
    """
    Scraper cho ThanhNien.vn sử dụng RSS Feed
    """

    def __init__(self):
        super().__init__()
        self.source = "thanhnien.vn"
        # Sử dụng RSS Tin mới nhất
        self.rss_url = "https://thanhnien.vn/rss/home.rss"

    def fetch_news(self) -> List[Tuple]:
        """
        Lấy tối đa 20 tin tức mới nhất từ RSS feed của Thanh Niên
        """
        all_articles = []
        print(f"\n📡 Đang đọc RSS từ: {self.rss_url} - multi_source_scraper.py:1193")
        
        feed = feedparser.parse(self.rss_url)
        
        if not feed.entries:
            print("⚠ Không tìm thấy bài viết nào trong RSS Thanh Niên. - multi_source_scraper.py:1198")
            return []

        # Giới hạn 20 bài đầu tiên
        entries_to_process = feed.entries[:20]
        print(f"Thanh Niên: Tìm thấy {len(feed.entries)} bài. Sẽ xử lý {len(entries_to_process)} bài. - multi_source_scraper.py:1203")

        for entry in entries_to_process:
            link = entry.link
            
            print(f"Fetching: {link[:60]}... - multi_source_scraper.py:1208")
            self.sleep()
            
            # Vì RSS Thanh Niên không có thẻ <category>, ta sẽ bóc tách nó trong hàm detail
            article_data = self._fetch_article_detail(link)
            if article_data:
                all_articles.append(article_data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo từ Thanh Niên"""
        html = self.fetch_html(link)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Trích xuất Tiêu đề
        # Thanh Niên dùng class .detail-title hoặc h1
        title_el = soup.select_one('h1.detail-title') or soup.select_one('.detail-title') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''
        
        if not title:
            return None
        
        # 2. Trích xuất Ngày xuất bản
        published_at = 0
        # Thanh Niên: <div class="detail-time"><span>01/01/2026 17:24</span></div>
        date_el = soup.select_one('.detail-time') or soup.select_one('.detail-time span')
        if date_el:
            date_text = date_el.get_text(strip=True)
            # Regex lấy định dạng dd/mm/yyyy HH:MM
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})', date_text)
            if date_match:
                day, month, year, hour, minute = date_match.groups()
                try:
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    published_at = int(dt.timestamp())
                except: pass

        # 3. Trích xuất Nội dung
        content = ""
        # Thanh Niên thường dùng div#abb-content hoặc [itemprop="articleBody"]
        content_el = soup.select_one('#abb-content') or soup.select_one('.detail-content') or soup.select_one('[itemprop="articleBody"]')
        if content_el:
            # Loại bỏ các thành phần thừa
            for unwanted in content_el.select('.morenews, .display-ads, .video-content-wrapper, .banner-ads'):
                unwanted.decompose()
            
            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # 4. Trích xuất Chuyên mục (Giải pháp cho việc thiếu thẻ trong RSS)
        category = "TIN TỨC"
        
        # Ưu tiên 1: Lấy từ Meta Tag article:section (Chuẩn SEO của Thanh Niên)
        meta_cate = soup.find('meta', property='article:section')
        if meta_cate and meta_cate.get('content'):
            category = meta_cate.get('content').strip()
        else:
            # Ưu tiên 2: Tách từ URL (Ví dụ thanhnien.vn/thoi-su/abc.htm -> THOI SU)
            try:
                path_parts = link.replace('https://thanhnien.vn/', '').split('/')
                if len(path_parts) > 1:
                    category = path_parts[0].replace('-', ' ')
            except: pass

        category = category.upper().strip()

        return (
            published_at,
            title,
            link,
            content,
            self.source,
            "NA",   # stock_related
            "NA",   # sentiment_score
            False,  # server_pushed
            category,
        )


class TuoiTreRSSScraper(NewsScraperBase):
    """
    Scraper cho TuoiTre.vn sử dụng RSS Feed
    """

    def __init__(self):
        super().__init__()
        self.source = "tuoitre.vn"
        self.rss_url = "https://tuoitre.vn/rss/tin-moi-nhat.rss"

    def fetch_news(self) -> List[Tuple]:
        """Lấy 20 tin mới nhất từ Tuổi Trẻ"""
        all_articles = []
        print(f"\n📡 Đang đọc RSS từ: {self.rss_url} - multi_source_scraper.py:1304")

        feed = feedparser.parse(self.rss_url)
        if not feed.entries:
            return []

        entries_to_process = feed.entries[:20]
        for entry in entries_to_process:
            link = entry.link
            self.sleep()
            article_data = self._fetch_article_detail(link)
            if article_data:
                all_articles.append(article_data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 1. Tiêu đề
        title_el = soup.select_one('.detail-title') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''
        if not title: return None

        # 2. Ngày xuất bản (Xử lý format: 01/01/2026 18:00 GMT+7)
        published_at = 0
        date_el = soup.select_one('.detail-time') or soup.find('meta', property='article:published_time')
        if date_el:
            # Lấy text nếu là tag, lấy content nếu là meta
            date_text = date_el.get_text(strip=True) if not date_el.get('content') else date_el.get('content')
            # Regex tìm: dd/mm/yyyy HH:mm
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})', date_text)
            if date_match:
                day, month, year, hour, minute = date_match.groups()
                try:
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    published_at = int(dt.timestamp())
                except: pass

        # 3. Nội dung
        content = ""
        # Tuổi trẻ dùng class .fck hoặc div[itemprop="articleBody"]
        content_el = soup.select_one('.fck') or soup.select_one('.detail-content')
        if content_el:
            # Loại bỏ video, tin liên quan, quảng cáo
            for unwanted in content_el.select('.vnn-title, .box-tin-lien-quan, .ad-container'):
                unwanted.decompose()
            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # 4. Chuyên mục (Bóc từ Meta article:section)
        category = "TIN MỚI"
        meta_cate = soup.find('meta', property='article:section')
        if meta_cate:
            category = meta_cate.get('content').upper().strip()

        return (
            published_at, title, link, content, self.source,
            "NA", "NA", False, category,
        )


class VietStockScraper(NewsScraperBase):
    """
    Scraper cho VietStock.vn - crawl từ trang "Mới cập nhật"

    Sử dụng Selenium để xử lý trang load bằng JavaScript.
    """

    def __init__(self):
        super().__init__()
        self.source = "vietstock.vn"
        self.headers['Referer'] = 'https://vietstock.vn/'

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        """
        Fetch tin tức từ VietStock trang "Mới cập nhật" bằng Selenium

        Args:
            max_articles: Số bài tối đa cần crawl (mặc định 15)
        """
        all_articles = []
        url = "https://vietstock.vn/chu-de/1-2/moi-cap-nhat.htm"

        print(f"\n📰 Crawling VietStock.vn  Mới cập nhật (with Selenium)")
        print(f"\n📄 Fetching: {url}")

        # Import Selenium
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        # Setup Chrome options (headless mode)
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Chạy không hiển thị browser
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')

        # Chỉ định đường dẫn Chrome binary (Windows)
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
            # Khởi tạo Chrome driver với webdriver-manager
            print("→ Starting Chrome browser...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Mở trang
            driver.get(url)

            # Đợi JavaScript load xong - đợi có link bài viết xuất hiện
            print("→ Waiting for page to load...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='.htm']"))
            )

            # Đợi thêm một chút để đảm bảo tất cả content đã load
            import time
            time.sleep(2)

            # Lấy HTML đã render
            html = driver.page_source
            print(f"✓ Got rendered HTML: {len(html)} chars")

        except Exception as e:
            print(f"⚠ Selenium error: {e}")
            return all_articles
        finally:
            # Đóng browser
            if driver:
                driver.quit()
                print("→ Browser closed")

        # Parse HTML với BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find all article links - VietStock articles have title attribute
        # URL pattern: /YYYY/MM/article-slug-###-XXXXXXX.htm
        article_links = []

        # Find links with title attribute (actual articles)
        titled_links = soup.find_all('a', title=True, href=lambda x: x and '.htm' in x)

        for link in titled_links:
            href = link.get('href', '')
            title = link.get('title', '')

            # Skip non-articles
            if not href or href.startswith('javascript:') or href.startswith('#'):
                continue

            # Skip topic pages
            if '/chu-de/' in href:
                continue

            # Make absolute URL
            if not href.startswith('http'):
                if href.startswith('//'):
                    href = 'https:' + href
                else:
                    href = f"https://vietstock.vn{href}"

            # Article URLs have pattern: /YYYY/MM/slug.htm
            # Must have title (real article) and proper URL depth
            if (len(title) > 10 and
                href.count('/') >= 5 and  # /YYYY/MM/article.htm = 5 slashes minimum
                href not in article_links and
                '/20' in href):  # Has year in path like /2026/

                article_links.append(href)

        if not article_links:
            print(f"⚠ No articles found")
            return all_articles

        # Limit to requested number
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
        """Fetch chi tiết một bài báo VietStock"""
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

        # Extract date - VietStock has multiple sources
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
                # Format: "01-01-2026 21:11:44+07:00" or "01/01/2026 21:11:44"
                # Try parsing with dateutil
                try:
                    from dateutil import parser
                    dt = parser.parse(date_text)
                    published_at = int(dt.timestamp())
                except Exception as e:
                    # Fallback to regex
                    date_match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})', date_text)
                    if date_match:
                        day, month, year, hour, minute, second = date_match.groups()
                        try:
                            dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                            published_at = int(dt.timestamp())
                        except Exception as e:
                            print(f"⚠ Could not parse date '{date_text}': {e}")

        # Extract content
        content_el = soup.select_one('.detail-content') or soup.select_one('.article-content') or soup.select_one('[itemprop="articleBody"]')
        content = ""

        if content_el:
            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # Extract category from breadcrumb
        # <a href="/kinh-te.htm" itemprop="item" title="Kinh tế" class="bcrumbs-item"><span itemprop="name">Kinh tế</span></a>
        category = "MỚI CẬP NHẬT"  # Default (đã in hoa)

        # Try to get from breadcrumb
        breadcrumb_links = soup.select('a.bcrumbs-item[itemprop="item"]')
        if len(breadcrumb_links) >= 2:
            # Skip first (usually "Trang chủ"), take second as category
            category_el = breadcrumb_links[1]
            category_span = category_el.select_one('span[itemprop="name"]')
            if category_span:
                category_text = category_span.get_text(strip=True)
                if category_text:
                    category = category_text.upper()  # In hoa category

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
        category = "TIN 24H"  # Default (đã in hoa)

        category_el = soup.select_one('a.category-name_ac[data-role="cate-name"]')
        if category_el:
            category_text = category_el.get_text(strip=True)
            if category_text:
                category = category_text.upper()  # In hoa category

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
                    # Skip: /tin-moi, /thong-tin-doanh-nghiep, category pages
                    if (href not in article_links and
                        '/tin-moi' not in href and
                        '/thong-tin-doanh-nghiep' not in href and
                        not href.endswith('laodong.vn/') and
                        href.count('/') >= 4):  # Article URLs have at least domain/category/slug
                        article_links.append(href)

        if not article_links:
            print(f"⚠ No valid article links found")
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
        # <a class="main-cat-lnk" href="https://laodong.vn/the-thao"> Thể thao </a>
        category = "TIN MỚI"  # Default (đã in hoa)

        category_el = soup.select_one('a.main-cat-lnk')
        if category_el:
            category_text = category_el.get_text(strip=True)
            if category_text:
                category = category_text.upper()  # In hoa category

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


class ANTTRSSScraper(NewsScraperBase):
    """
    Scraper cho ANTT.vn sử dụng RSS Feed
    """

    def __init__(self):
        super().__init__()
        self.source = "antt.vn"
        self.rss_url = "https://antt.vn/rss/trang-chu.rss"

    def fetch_news(self) -> List[Tuple]:
        """
        Lấy tối đa 20 tin tức mới nhất từ RSS feed của ANTT
        """
        all_articles = []
        print(f"\n📡 Đang đọc RSS từ: {self.rss_url}")
        
        feed = feedparser.parse(self.rss_url)
        
        if not feed.entries:
            print("⚠ Không tìm thấy bài viết nào trong RSS.")
            return []

        entries_to_process = feed.entries[:20]
        print(f"Tìm thấy {len(feed.entries)} bài. Sẽ xử lý {len(entries_to_process)} bài mới nhất.")

        for entry in entries_to_process:
            link = entry.link
            
            # RSS của ANTT thường không có thẻ <category> trực tiếp cho từng entry như Dân Trí
            # Ta sẽ mặc định là 'TIN MỚI' và để hàm detail lấy từ Meta Tag
            rss_category = getattr(entry, 'category', 'TIN MỚI')
            
            print(f"Fetching: {link[:60]}...")
            self.sleep() # Đảm bảo không crawl quá nhanh
            
            article_data = self._fetch_article_detail(link, rss_category)
            if article_data:
                all_articles.append(article_data)

        print(f"\n✓ Tổng số bài viết từ ANTT thu thập được: {len(all_articles)}")
        return all_articles

    def _fetch_article_detail(self, link: str, rss_category: str = None) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo từ ANTT"""
        # Fix: ANTT RSS trả về URLs dạng "-nXXXXXX.html" nhưng website dùng "-XXXXXX.htm"
        # Cần bỏ chữ 'n' trước số và đổi extension
        import re
        original_link = link
        if link.endswith('.html'):
            # Thay -nXXXXXX.html thành -XXXXXX.htm
            link = re.sub(r'-n(\d+)\.html$', r'-\1.htm', link)
        elif link.endswith('.htm'):
            # Nếu đã là .htm nhưng vẫn có 'n', thì bỏ 'n'
            link = re.sub(r'-n(\d+)\.htm$', r'-\1.htm', link)

        if link != original_link:
            print(f"  → URL fixed: ...{original_link[-50:]} → ...{link[-50:]}")

        # ANTT server trả về encoding sai (ISO-8859-1) nhưng content là UTF-8
        # Cần fetch với explicit UTF-8 encoding
        try:
            resp = self.session.get(link, headers=self.headers, timeout=30)
            resp.raise_for_status()
            # Force UTF-8 decoding
            html = resp.content.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"✗ Error fetching {link}: {e}")
            return None

        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 1. Trích xuất Tiêu đề (ANTT dùng div.title_detail)
        title_el = soup.select_one('.title_detail') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''

        if not title:
            print(f"  ⚠ No title found for {link[-60:]}")
            return None
        
        # 2. Trích xuất Ngày xuất bản
        # ANTT dùng format: "02/01/2026 11:02:40"
        published_at = 0
        date_el = soup.select_one('.time_home')
        if date_el:
            date_text = date_el.get_text(strip=True)
            # Format: dd/mm/yyyy hh:mm:ss
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})', date_text)
            if date_match:
                day, month, year, hour, minute, second = date_match.groups()
                try:
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                    published_at = int(dt.timestamp())
                except:
                    pass
        
        # 3. Trích xuất Nội dung
        content = ""
        # ANTT: content nằm trong các thẻ p trực tiếp trong content_main
        content_el = soup.select_one('.content_main')
        if content_el:
            # Loại bỏ các thành phần không cần thiết
            for unwanted in content_el.select('.related-box, .ad-container, script, style, .tag_detail, .article-footer'):
                unwanted.decompose()

            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # 4. Trích xuất Chuyên mục
        # ANTT: category nằm trong breadcrumb (item thứ 2)
        category = "TIN MỚI"

        # Tìm breadcrumb items
        breadcrumb_items = soup.select('a[itemprop="url"] span[itemprop="title"]')

        # Lấy item thứ 2 (index 1) - đó là category chính
        # Item 1: Trang chủ, Item 2: Category, Item 3: Sub-category
        if len(breadcrumb_items) >= 2:
            category = breadcrumb_items[1].get_text(strip=True)

        category = category.upper().strip()

        return (
            published_at,
            title,
            link,
            content,
            self.source,
            "NA",   # stock_related
            "NA",   # sentiment_score
            False,  # server_pushed
            category,
        )

# class AgroMonitorScraper(NewsScraperBase):
#     """
#     Scraper cho Agromonitor.vn - crawl từ trang "Trang chủ"
 # #     Sử dụng Selenium để xử lý trang load bằng JavaScript và tự động đăng nhập.
#     """
 # #     def __init__(self):
#         super().__init__()
#         self.source = "agromonitor.vn"
#         self.headers['Referer'] = 'https://agromonitor.vn/'
#         self.driver = None  # Selenium driver instance
#         self.logged_in = False  # Track login status
 #     # def _get_driver(self):
        # """Tạo và configure Selenium Chrome driver"""
        # from selenium import webdriver
        # from selenium.webdriver.chrome.options import Options
        # from selenium.webdriver.chrome.service import Service
        # from webdriver_manager.chrome import ChromeDriverManager
        # import os
 #         # chrome_options = Options()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.add_argument('--disable-gpu')
        # chrome_options.add_argument('--window-size=1920,1080')
        # chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
 #         # Chỉ định đường dẫn Chrome binary
        # chrome_paths = [
            # r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            # r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        # ]
        # for chrome_path in chrome_paths:
            # if os.path.exists(chrome_path):
                # chrome_options.binary_location = chrome_path
                # break
 #         # service = Service(ChromeDriverManager().install())
        # return webdriver.Chrome(service=service, options=chrome_options)
 #     # def _login(self):
        # """Tự động đăng nhập vào AgroMonitor"""
        # from selenium.webdriver.common.by import By
        # from selenium.webdriver.support.ui import WebDriverWait
        # from selenium.webdriver.support import expected_conditions as EC
        # from dotenv import load_dotenv
        # import os
        # import time
 #         # Load credentials từ .env
        # load_dotenv()
        # email = os.getenv('AGROMONITOR_EMAIL')
        # password = os.getenv('AGROMONITOR_PASSWORD')
 #         # if not email or not password or email == 'your_email@example.com':
            # print("⚠ Warning: AgroMonitor credentials not configured in .env file")
            # print("  Please update AGROMONITOR_EMAIL and AGROMONITOR_PASSWORD in .env")
            # return False
 #         # try:
            # print("→ Logging in to AgroMonitor...")
 #             # Mở trang login
            # self.driver.get("https://agromonitor.vn/login")
            # time.sleep(3)  # Đợi trang load
 #             # Đóng popup/modal nếu có (nút "Đóng" hoặc "X")
            # try:
                # close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.ant-modal-close, button.btn-danger")
                # for btn in close_buttons:
                    # if btn.is_displayed():
                        # print("  → Closing popup/modal...")
                        # btn.click()
                        # time.sleep(1)
                        # break
            # except:
                # pass  # Không có popup, tiếp tục
 #             # Tìm và điền username
            # username_input = self.driver.find_element(By.NAME, "username")
            # username_input.clear()
            # username_input.send_keys(email)
 #             # Tìm và điền password
            # password_input = self.driver.find_element(By.NAME, "password")
            # password_input.clear()
            # password_input.send_keys(password)
 #             # Tìm nút đăng nhập
            # login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
 #             # Scroll đến nút login
            # self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            # time.sleep(1)
 #             # Click bằng JavaScript (tránh bị intercepted)
            # print("  → Clicking login button...")
            # self.driver.execute_script("arguments[0].click();", login_button)
 #             # Đợi login hoàn tất
            # time.sleep(5)
 #             # Kiểm tra xem đã login thành công chưa
            # current_url = self.driver.current_url
 #             # Debug: Save HTML after login attempt
            # with open('debug_after_login.html', 'w', encoding='utf-8') as f:
                # f.write(self.driver.page_source)
            # print(f"  → Saved HTML after login to debug_after_login.html")
            # print(f"  → Current URL: {current_url}")
 #             # Tìm error message nếu có
            # try:
                # error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".ant-message-error, .error, .alert-danger")
                # for err in error_elements:
                    # if err.is_displayed():
                        # print(f"  ✗ Error message: {err.text}")
            # except:
                # pass
 #             # if "login" not in current_url:
                # print("✓ Login successful!")
                # self.logged_in = True
                # return True
            # else:
                # print("✗ Login failed - still on login page")
                # return False
 #         # except Exception as e:
            # print(f"✗ Login error: {e}")
            # import traceback
            # traceback.print_exc()
            # return False
 #     # def fetch_news(self, max_pages: int = 1, max_articles_per_page: int = 20) -> List[Tuple]:
        # all_articles = []
        # seen_urls = {}
        # import time
 #         # url = "https://agromonitor.vn/category/16/trang-chu"
        # print(f"\n📄 Fetching Agromonitor (with auto-login): {url}")
 #         # try:
            # Khởi tạo driver
            # print("→ Starting Chrome browser...")
            # self.driver = self._get_driver()
 #             # Đăng nhập
            # if not self._login():
                # print("⚠ Failed to login, aborting scrape")
                # return all_articles
 #             # Mở trang category
            # print(f"→ Opening category page...")
            # self.driver.get(url)
            # time.sleep(5)  # Đợi trang load
 #             # Lấy HTML đã render
            # html = self.driver.page_source
            # print(f"✓ Got rendered HTML: {len(html)} chars")
 #             # Parse HTML với BeautifulSoup
            # soup = BeautifulSoup(html, 'html.parser')
 #             # Tìm các link bài viết (Agromonitor sử dụng pattern /post/ID/slug)
            # links = soup.select('a[href*="/post/"]')
 #             # article_urls = []
            # for link in links:
                # href = link.get('href', '')
                # if href:
                    # Chuyển link tương đối thành tuyệt đối
                    # full_url = href if href.startswith('http') else f"https://agromonitor.vn{href}"
 #                     # if full_url not in seen_urls:
                        # seen_urls[full_url] = True
                        # article_urls.append(full_url)
 #             # Giới hạn số lượng bài
            # article_urls = article_urls[:max_articles_per_page]
            # print(f"Found {len(article_urls)} potential article URLs")
 #             # Fetch chi tiết từng bài viết (sử dụng same driver instance)
            # for i, article_url in enumerate(article_urls, 1):
                # print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:65]}...")
                # article_data = self._fetch_article_detail(article_url)
                # if article_data:
                    # all_articles.append(article_data)
                # time.sleep(2)  # Delay giữa các request
 #         # except Exception as e:
            # print(f"⚠ Error during scraping: {e}")
            # import traceback
            # traceback.print_exc()
        # finally:
            # Cleanup: Đóng browser
            # if self.driver:
                # self.driver.quit()
                # print("→ Browser closed")
                # self.driver = None
                # self.logged_in = False
 #         # return all_articles
 #     # def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        # """Fetch chi tiết bài viết sử dụng driver instance đã đăng nhập"""
        # import time
 #         # if not self.driver or not self.logged_in:
            # print(f"  ✗ Driver not initialized or not logged in")
            # return None
 #         # try:
            # Mở trang detail
            # self.driver.get(link)
            # time.sleep(3)  # Đợi trang load
 #             # Lấy HTML đã render
            # html = self.driver.page_source
 #         # except Exception as e:
            # print(f"  ✗ Error fetching detail: {e}")
            # return None
 #         # if not html:
            # return None
 #         # soup = BeautifulSoup(html, 'html.parser')
 #         # 1. Extract Title: Thường nằm trong h1 hoặc class title-detail
        # title_el = soup.select_one('h1') or soup.select_one('.title-detail')
        # title = title_el.get_text(strip=True) if title_el else ''
 #         # if not title:
            # print(f"  ✗ No title found for: {link[:60]}...")
            # return None
 #         # 2. Extract Date: Agromonitor thường ghi "02:37 31/12/2025"
        # published_at = 0
        # date_el = soup.select_one('.date') or soup.select_one('.time')
        # if date_el:
            # date_text = date_el.get_text(strip=True)
            # Regex tìm: HH:mm DD/MM/YYYY hoặc DD/MM/YYYY
            # date_match = re.search(r'(\d{1,2}):(\d{2})\s+(\d{1,2})/(\d{1,2})/(\d{4})', date_text)
            # if date_match:
                # hour, minute, day, month, year = date_match.groups()
                # try:
                    # dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    # published_at = int(dt.timestamp())
                # except:
                    # pass
 #         # 3. Extract Content: Thường nằm trong các thẻ div có class content hoặc detail-content
        # content = ""
        # content_el = soup.select_one('.content-detail') or soup.select_one('.post-content')
        # if content_el:
            # Loại bỏ các phần không cần thiết như quảng cáo, tag nếu có
            # paragraphs = content_el.find_all(['p', 'div'], recursive=False)
            # content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
 #         # 4. Extract Category
        # category = "NÔNG SẢN" # Mặc định
        # Thử lấy từ breadcrumb nếu có
        # breadcrumb = soup.select_one('.breadcrumb')
        # if breadcrumb:
            # category = breadcrumb.get_text(" > ", strip=True)
 #         # return (
            # published_at,
            # title,
            # link,
            # content,
            # self.source,
            # "NA",
            # "NA",
            # False,
            # category,
        # )

class CNARSSScraper(NewsScraperBase):
    """
    Scraper cho ChannelNewsAsia.com sử dụng RSS Feed
    """

    def __init__(self):
        super().__init__()
        self.source = "channelnewsasia.com"
        # Link RSS chính thức của CNA
        self.rss_url = "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml"

    def fetch_news(self) -> List[Tuple]:
        """
        Lấy tối đa 20 tin tức mới nhất từ RSS feed của CNA
        """
        all_articles = []
        print(f"\n📡 Đang đọc RSS từ: {self.rss_url}")
        
        # 1. Sử dụng feedparser để đọc nội dung RSS
        feed = feedparser.parse(self.rss_url)
        
        if not feed.entries:
            print("⚠ Không tìm thấy bài viết nào trong RSS.")
            return []

        # 2. Giới hạn 20 bài viết đầu tiên
        entries_to_process = feed.entries[:20]
        print(f"Tìm thấy {len(feed.entries)} bài. Sẽ xử lý {len(entries_to_process)} bài mới nhất.")

        for entry in entries_to_process:
            link = entry.link
            
            # Lấy Category (CNA thường để trong tags hoặc category field của RSS)
            rss_category = "WORLD" # Mặc định cho CNA
            if hasattr(entry, 'tags'):
                rss_category = entry.tags[0].term if entry.tags else "ASIA"
            
            # Lấy timestamp trực tiếp từ RSS (CNA hỗ trợ cực tốt phần này)
            published_at = 0
            if hasattr(entry, 'published_parsed'):
                published_at = int(datetime(*entry.published_parsed[:6]).timestamp())
            
            print(f"Fetching: {link[:60]}...")
            self.sleep()
            
            # Truyền các thông tin đã có vào hàm detail
            article_data = self._fetch_article_detail(link, rss_category, published_at)
            if article_data:
                all_articles.append(article_data)

        print(f"\n✓ Tổng số bài viết CNA thu thập được: {len(all_articles)}")
        return all_articles

    def _fetch_article_detail(self, link: str, rss_category: str = None, rss_published_at: int = 0) -> Optional[Tuple]:
        """Fetch chi tiết một bài báo từ CNA"""
        html = self.fetch_html(link)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Trích xuất Tiêu đề (CNA thường dùng class h1.entry-title hoặc class liên quan đến content)
        title_el = soup.select_one('h1.page-title') or soup.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else ''
        
        if not title:
            return None
        
        # 2. Trích xuất Ngày xuất bản (Ưu tiên lấy từ RSS đã có ở bước trước)
        published_at = rss_published_at
        
        # 3. Trích xuất Nội dung
        content = ""
        # Selector cho nội dung bài viết của CNA (thường là div chứa text-long hoặc các thẻ p trong article)
        content_el = soup.select_one('.content-wrapper') or soup.select_one('.text-long')
        if content_el:
            # Loại bỏ các thành phần rác như "Also read", Video player, Ads
            for unwanted in content_el.select('.related-section, .video-embed, .ad-slot, .infographic'):
                unwanted.decompose()
                
            paragraphs = content_el.select('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # 4. Trích xuất Chuyên mục
        category = rss_category if rss_category else "WORLD"
        category = category.upper().strip()

        return (
            published_at,
            title,
            link,
            content,
            self.source,
            "NA",   # stock_related
            "NA",   # sentiment_score
            False,  # server_pushed
            category,
        )




class KinhTeNgoaiThuongScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "kinhtengoaithuong.vn"
        # Thêm header để giả lập trình duyệt xem tin tức
        self.headers.update({
            'Referer': 'https://www.google.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        all_articles = []
        url = "https://kinhtengoaithuong.vn/" 

        print(f"\n📡 Đang quét trang chủ: {url}")
        html = self.fetch_html(url)
        
        if not html:
            print("⚠ Không thể truy cập trang chủ kinhtengoaithuong.vn")
            return []

        soup = BeautifulSoup(html, 'html.parser')

        # 1. Tìm tất cả các link bài viết
        # Đặc điểm: Các bài viết trên trang này thường nằm trong các thẻ h2, h3 
        # hoặc div có class chứa 'post', 'item', 'title'
        potential_links = soup.select('h2 a, h3 a, .post-title a, .entry-title a')
        
        article_urls = []
        seen_urls = set()

        for a in potential_links:
            href = a.get('href', '')
            if not href: continue

            # Chuẩn hóa link tuyệt đối
            if href.startswith('/'):
                href = f"https://kinhtengoaithuong.vn{href}"
            
            # Lọc: Phải thuộc domain, không phải trang chủ, không phải link rác
            if "kinhtengoaithuong.vn" in href and href != "https://kinhtengoaithuong.vn/":
                # Loại bỏ các trang chức năng
                if not any(x in href for x in ['/category/', '/tag/', '/author/', '/contact/', '/gioi-thieu/']):
                    if href not in seen_urls:
                        seen_urls.add(href)
                        article_urls.append(href)

        # 2. Nếu Selector trên không ra kết quả, dùng Regex để quét toàn bộ link
        if not article_urls:
            print("🔍 Thử quét link bằng phương thức Regex...")
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Link bài viết thường có độ sâu path > 3 (ví dụ domain.vn/ten-bai-viet/)
                if "kinhtengoaithuong.vn" in href and len(href.strip('/').split('/')) >= 3:
                     if href not in seen_urls and not any(x in href for x in ['/category/', '/tag/']):
                        seen_urls.add(href)
                        article_urls.append(href)

        article_urls = article_urls[:max_articles]
        print(f"✓ Tìm thấy {len(article_urls)} bài viết từ trang chủ.")

        for i, article_url in enumerate(article_urls, 1):
            print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:50]}...")
            self.sleep()
            article_data = self._fetch_article_detail(article_url)
            if article_data:
                all_articles.append(article_data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Tiêu đề
        title_el = soup.find('h1')
        title = title_el.get_text(strip=True) if title_el else ''
        if not title: return None

        # 2. Ngày xuất bản
        published_at = int(datetime.now().timestamp())
        # Tìm trong các thẻ meta hoặc class date phổ biến của trang
        date_el = soup.select_one('.detail-date, .post-date, .time')
        if date_el:
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_el.get_text())
            if date_match:
                d, m, y = date_match.groups()
                try: published_at = int(datetime(int(y), int(m), int(d)).timestamp())
                except: pass

        # 3. Nội dung (Sử dụng Selector: .article-content)
        content_el = soup.select_one('.article-content')
        content = ""
        if content_el:
            # Thu thập dữ liệu từ cả thẻ <p> và các dòng trong <table> (chú thích ảnh)
            # để đảm bảo không sót thông tin quan trọng
            parts = []
            
            # Lấy các đoạn văn bản
            for p in content_el.find_all(['p', 'td']):
                # Loại bỏ khoảng trắng thừa và các ký tự đặc biệt
                txt = p.get_text(strip=True)
                if txt and len(txt) > 5: # Chỉ lấy các đoạn có nghĩa
                    parts.append(txt)
            
            content = ' '.join(parts)

        # 4. Chuyên mục (Category)
        category = "TÀI CHÍNH" # Default dựa trên link mẫu
        # Theo element bạn đưa: <a itemprop="item" ... title="Tài chính">
        # Chúng ta tìm danh sách Breadcrumb và lấy phần tử thứ 2 (sau Trang chủ)
        bread_items = soup.select('a[itemprop="item"]')
        if len(bread_items) >= 2:
            # Lấy text từ thuộc tính title hoặc từ thẻ span bên trong
            category = bread_items[1].get('title') or bread_items[1].get_text(strip=True)
        
        category = category.upper().strip()

        return (
            published_at, 
            title, 
            link, 
            content, 
            self.source, 
            "NA", "NA", False, 
            category
        )


class ThoiBaoNganHangScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "thoibaonganhang.vn"
        self.headers.update({
            'Referer': 'https://thoibaonganhang.vn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        all_articles = []
        url = "https://thoibaonganhang.vn/"

        print(f"\n📡 Đang quét trang chủ Thời báo Ngân hàng: {url}")
        html = self.fetch_html(url)
        if not html: return []

        soup = BeautifulSoup(html, 'html.parser')
        article_urls = []
        seen_urls = set()
        
        # Quét tất cả link bài viết có đuôi .html và chứa số ID
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if ".html" in href and any(char.isdigit() for char in href):
                if not href.startswith('http'):
                    href = f"https://thoibaonganhang.vn{href}"
                
                if not any(x in href for x in ['/video-', '/anh-', '/chuyen-muc/', '/tags/']):
                    if href not in seen_urls:
                        seen_urls.add(href)
                        article_urls.append(href)

        article_urls = article_urls[:max_articles]
        print(f"✓ Tìm thấy {len(article_urls)} bài viết tiềm năng.")

        for i, article_url in enumerate(article_urls, 1):
            print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:60]}...")
            self.sleep() # Không truyền tham số để tránh lỗi NewsScraperBase
            article_data = self._fetch_article_detail(article_url)
            if article_data:
                all_articles.append(article_data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Tiêu đề
        title_el = soup.find('h1')
        if not title_el: return None
        title = title_el.get_text(strip=True)

        # 2. Ngày xuất bản (.format_date)
        published_at = int(datetime.now().timestamp())
        date_el = soup.select_one('.format_date')
        if date_el:
            try:
                dt = datetime.strptime(date_el.get_text(strip=True), '%d/%m/%Y')
                published_at = int(dt.timestamp())
            except: pass

        # 3. Chuyên mục (.bx-cat-link)
        category = "NGÂN HÀNG"
        cat_el = soup.select_one('.bx-cat-link')
        if cat_el:
            category = cat_el.get_text(strip=True).upper()

        # 4. Nội dung (Gộp Sapo + Body)
        content = ""
        container = soup.select_one('.article-detail-body')
        if container:
            content_box = copy.copy(container)
            
            # Lấy phần Sapo (Tóm tắt)
            sapo_el = content_box.select_one('.article-detail-desc')
            sapo_text = sapo_el.get_text(strip=True) if sapo_el else ""
            
            # Loại bỏ rác trước khi lấy Body
            for noise in content_box.select('.article-share-button, .article-extension, script, style, .article-detail-desc'):
                noise.decompose()
            
            # Lấy các đoạn văn bản chính
            paragraphs = content_box.find_all('p')
            if paragraphs:
                body_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            else:
                body_text = content_box.get_text(" ", strip=True)
            
            # Kết hợp Sapo và Body
            content = f"{sapo_text} {body_text}".strip()

        if not content or len(content) < 50:
            return None

    
        return (published_at, title, link, content, self.source, "NA", "NA", False, category)



class TaiChinhDoanhNghiepScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "taichinhdoanhnghiep.net.vn"
        self.headers.update({
            'Referer': 'https://taichinhdoanhnghiep.net.vn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        all_articles = []
        # Quét trang chủ để lấy danh sách bài mới
        url = "https://taichinhdoanhnghiep.net.vn/"
        html = self.fetch_html(url)
        if not html: return []

        soup = BeautifulSoup(html, 'html.parser')
        article_urls = []
        seen_urls = set()
        
        # Trang này thường dùng link kết thúc bằng -dXXXXX.html
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if "-d" in href and ".html" in href:
                if not href.startswith('http'):
                    href = f"https://taichinhdoanhnghiep.net.vn{href}"
                if href not in seen_urls:
                    seen_urls.add(href)
                    article_urls.append(href)

        for article_url in article_urls[:max_articles]:
            self.sleep() # Sửa lỗi sleep() không tham số
            data = self._fetch_article_detail(article_url)
            if data: all_articles.append(data)
        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Tiêu đề (Ưu tiên lấy từ #getTitle, fallback sang h1)
        title_el = soup.select_one('#getTitle') or soup.find('h1')
        if not title_el:
            print(f"⚠️ Không tìm thấy title cho URL: {link}")
            return None
        title = title_el.get_text(strip=True)
        if not title:
            print(f"⚠️ Title rỗng cho URL: {link}")
            return None

        # 2. Chuyên mục (Theo mẫu: .c-j a)
        category = "TÀI CHÍNH"
        cat_el = soup.select_one('.c-j a')
        if cat_el:
            category = cat_el.get_text(strip=True).upper()

        # 3. Ngày xuất bản (Theo mẫu: .bx-time)
        published_at = int(datetime.now().timestamp())
        date_el = soup.select_one('.bx-time')
        if date_el:
            date_text = date_el.get_text(strip=True) # Dạng: 01/01/2026, 10:52
            try:
                # Cắt lấy phần ngày trước dấu phẩy
                clean_date = date_text.split(',')[0].strip()
                dt = datetime.strptime(clean_date, '%d/%m/%Y')
                published_at = int(dt.timestamp())
            except: pass

        # 4. Nội dung (Xử lý khối .chuyennoidung và #noidung)
        content = ""
        container = soup.select_one('#noidung')
        if container:
            # Sao chép để lọc rác
            content_box = copy.copy(container)
            
            # LOẠI BỎ RÁC: Audio player, khối social dưới bài, quảng cáo
            # Theo mẫu bạn gửi: .audio_box, .detail-share-2, .qc1, blockquote
            for noise in content_box.select('.audio_box, .detail-share-2, .qc1, blockquote, script, .audio_tool'):
                noise.decompose()
            
            # Lấy Sapo (Thường nằm trong thẻ h2 hoặc có id getIntro)
            sapo_el = content_box.select_one('#getIntro, h2')
            sapo_text = sapo_el.get_text(strip=True) if sapo_el else ""
            
            # Lấy các đoạn văn bản (p)
            paragraphs = content_box.find_all('p')
            body_parts = []
            for p in paragraphs:
                txt = p.get_text(strip=True)
                if txt: body_parts.append(txt)
            
            body_text = ' '.join(body_parts)
            content = f"{sapo_text} {body_text}".strip()

        if len(content) < 50: return None

        

        return (published_at, title, link, content, self.source, "NA", "NA", False, category)


class BaoChinhPhuScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "baochinhphu.vn"
        self.headers.update({
            'Referer': 'https://baochinhphu.vn/',
        })

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        all_articles = []
        url = "https://baochinhphu.vn/tin-moi.htm"
        
        print(f"\n📡 Đang quét Báo Chính phủ: {url}")
        html = self.fetch_html(url)
        if not html: return []

        soup = BeautifulSoup(html, 'html.parser')
        article_urls = []
        seen_urls = set()
        
        # Báo Chính phủ thường bọc link trong khối có class 'story' hoặc 'box-category'
        links = soup.select('a[data-role="title"], .story__title a, .box-category-link-title')
        for link in links:
            href = link.get('href', '')
            if href and href.endswith('.htm'):
                if not href.startswith('http'):
                    href = f"https://baochinhphu.vn{href}"
                
                if href not in seen_urls:
                    seen_urls.add(href)
                    article_urls.append(href)
            
            if len(article_urls) >= max_articles:
                break

        for i, article_url in enumerate(article_urls, 1):
            print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:60]}...")
            self.sleep()
            article_data = self._fetch_article_detail(article_url)
            if article_data:
                all_articles.append(article_data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Tiêu đề (data-role="title")
        title_el = soup.select_one('[data-role="title"]')
        if not title_el: return None
        title = title_el.get_text(strip=True)

        # 2. Ngày xuất bản (Xử lý chuỗi 02/01/2026 ... 15:21)
        published_at = int(datetime.now().timestamp())
        date_container = soup.select_one('[data-role="publishdate"]')
        if date_container:
            # Loại bỏ các tag con (như icon SVG) để lấy text thuần
            raw_date = date_container.get_text(" ", strip=True)
            # Dùng regex lấy định dạng dd/mm/yyyy
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', raw_date)
            if date_match:
                try:
                    dt = datetime.strptime(date_match.group(1), '%d/%m/%Y')
                    published_at = int(dt.timestamp())
                except: pass

        # 3. Chuyên mục (data-role="cate-name")
        category = "CHÍNH TRỊ"
        cat_el = soup.select_one('[data-role="cate-name"]')
        if cat_el:
            category = cat_el.get_text(strip=True).upper()

        # 4. Nội dung (data-role="content")
        content = ""
        body_container = soup.select_one('[data-role="content"]')
        if body_container:
            content_box = copy.copy(body_container)
            
            # LOẠI BỎ RÁC:
            # - RelatedNewsBox (Tin liên quan giữa bài)
            # - button-dowload-img (Nút tải ảnh)
            # - script, style
            for noise in content_box.select('.VCSortableInPreviewMode[type="RelatedNewsBox"], .button-dowload-img, script, style'):
                noise.decompose()
            
            # Lấy toàn bộ text từ các thẻ p
            paragraphs = content_box.find_all(['p', 'h2', 'h3'])
            text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            content = ' '.join(text_parts).strip()

        if len(content) < 50: return None


        return (published_at, title, link, content, self.source, "NA", "NA", False, category)


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

    def fetch_news(self, max_articles: int = 10) -> List[Tuple]:
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
            print(f"[{i}/{len(article_urls)}] Fetching: {article_url[:70]}...")
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


class NguoiQuanSatScraper(NewsScraperBase):
    """
    Scraper cho nguoiquansat.vn – chuẩn longform (đã fix lỗi 0 articles)
    """

    def __init__(self):
        super().__init__()
        self.source = "nguoiquansat.vn"
        self.headers["Referer"] = "https://nguoiquansat.vn/"

    # =====================================================
    # 1. FETCH LIST PAGE
    # =====================================================
    def fetch_news(self, max_articles: int = 10) -> List[Tuple]:
        url = "https://nguoiquansat.vn/tin-moi-nhat"
        print(f"\n📡 Crawling: {url}")

        html = self.fetch_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")

        article_urls = []
        seen = set()

        # ---- FIX CHÍNH: LỌC LINK ĐÚNG ----
        for a in soup.select("a[href]"):
            href = a.get("href", "").strip()

            if not href.endswith(".html"):
                continue

            # loại link rác
            if any(x in href for x in ["/video", "/media", "/tag", "/author"]):
                continue

            full_url = (
                href if href.startswith("http")
                else f"https://nguoiquansat.vn{href}"
            )

            if full_url not in seen:
                seen.add(full_url)
                article_urls.append(full_url)

            if len(article_urls) >= max_articles:
                break

        print(f"✓ Found {len(article_urls)} article URLs")

        results = []
        for i, link in enumerate(article_urls, 1):
            print(f"[{i}/{len(article_urls)}] Fetching: {link}")
            self.sleep()
            data = self._fetch_article_detail(link)
            if data:
                results.append(data)

        return results

    # =====================================================
    # 2. FETCH ARTICLE DETAIL
    # =====================================================
    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # -------- TITLE --------
        title_el = soup.select_one("h1.sc-longform-header-title")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        # -------- PUBLISHED AT --------
        published_at = int(datetime.now().timestamp())
        date_el = soup.select_one("span.sc-longform-header-date")
        if date_el:
            date_str = date_el.get_text(strip=True).replace(" - ", " ")
            ts = self.parse_date_to_timestamp(date_str, "%d/%m/%Y %H:%M")
            if ts > 0:
                published_at = ts
        # -------- CATEGORY --------
        category_el = soup.select_one("li.breadcrumb-item.active a")
        category = category_el.get_text(strip=True).upper() if category_el else "TIN TỨC"


        # -------- CONTENT --------
        article = soup.select_one("article.entry")
        if not article:
            return None

        paragraphs = []

        # sapo
        sapo_el = article.select_one("p.sc-longform-header-sapo")
        if sapo_el:
            paragraphs.append(sapo_el.get_text(strip=True))

        for p in article.find_all("p", recursive=True):
            if p.find_parent(
                ["div", "figure"],
                class_=["c-box", "oneads", "ads_viewport"]
            ):
                continue

            txt = p.get_text(strip=True)
            if txt and txt not in paragraphs:
                paragraphs.append(txt)

        content = "\n\n".join(paragraphs)
        if not content:
            return None

        return (
            published_at,
            title,
            link,
            content,
            self.source,
            "NA",     # author
            "NA",
            False,
            category,
        )

class ThoiBaoTaiChinhScraper(NewsScraperBase):
    """Scraper cho thoibaotaichinhvietnam.vn"""
    def __init__(self):
        super().__init__()
        self.source = "thoibaotaichinhvietnam.vn"
        self.headers["Referer"] = "https://thoibaotaichinhvietnam.vn/"

    # =====================================================
    # 1. FETCH LIST PAGE
    # =====================================================
    def fetch_news(self, max_articles: int = 10) -> List[Tuple]:
        url = "https://thoibaotaichinhvietnam.vn/"
        print(f"\n📡 Crawling: {url}")

        html = self.fetch_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        article_urls = []
        seen = set()

        # ---- Lấy link bài mới nhất (.html) ----
        for a in soup.select("a[href$='.html']"):
            href = a.get("href", "").strip()
            if not href:
                continue

            # loại link rác nếu cần
            if any(x in href for x in ["/video", "/media", "/tag", "/author"]):
                continue

            # Build full URL an toàn (fix lỗi domain)
            full_url = href if href.startswith("http") else f"https://thoibaotaichinhvietnam.vn/{href.lstrip('/')}"

            if full_url not in seen:
                seen.add(full_url)
                article_urls.append(full_url)

            if len(article_urls) >= max_articles:
                break

        print(f"✓ Found {len(article_urls)} article URLs")

        # Crawl chi tiết từng bài
        results = []
        for i, link in enumerate(article_urls, 1):
            print(f"[{i}/{len(article_urls)}] Fetching: {link}")
            self.sleep()
            data = self._fetch_article_detail(link)
            if data:
                results.append(data)

        return results

    # =====================================================
    # 2. FETCH ARTICLE DETAIL
    # =====================================================
    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # -------- TITLE --------
        title_el = soup.select_one("h1.post-title")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        # -------- PUBLISHED AT --------
        published_at = int(datetime.now().timestamp())
        date_el = soup.select_one("span.format_date")
        time_el = soup.select_one("span.format_time")
        if date_el and time_el:
            datetime_str = f"{date_el.get_text(strip=True)} {time_el.get_text(strip=True)}"
            try:
                dt = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M")
                published_at = int(dt.timestamp())
            except Exception as e:
                print(f"⚠ Could not parse date '{datetime_str}': {e}")

        # -------- CATEGORY --------
        cate_el = soup.select_one("a.article-catname")
        category = cate_el.get_text(strip=True).upper() if cate_el else "TIN TỨC"

        # -------- CONTENT --------
        paragraphs = []
        desc_el = soup.select_one("div.post-desc")
        if desc_el:
            paragraphs.append(desc_el.get_text(strip=True))

        content_el = soup.select_one("div.post-content.__MASTERCMS_CONTENT")
        if content_el:
            for p in content_el.find_all("p", recursive=True):
                txt = p.get_text(strip=True)
                if txt and txt not in paragraphs:
                    paragraphs.append(txt)

        content = "\n\n".join(paragraphs)
        if not content:
            return None

        return (
            published_at,
            title,
            link,
            content,
            self.source,
            "NA",  # author
            "NA",
            False,
            category,
        )


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
            print(f"[{i}/{len(article_urls)}] Đang cào: {article_url}")
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


class VietnamFinanceScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "vietnamfinance.vn"
        self.base_url = "https://vietnamfinance.vn"

    def fetch_news(self, max_articles: int = 15) -> List[Tuple]:
        all_articles = []
        html = self.fetch_html(self.base_url)
        if not html: return []

        soup = BeautifulSoup(html, 'html.parser')
        article_links = []

        # 1. Lấy link từ khu vực articles (bao gồm cả Swiper và Danh sách bên dưới)
        container = soup.select_one('.section-secondary__left .articles')
        if container:
            # Tìm tất cả thẻ a có class title hoặc nằm trong h3.article__title
            # Cách bóc tách này khớp với cả 2 mẫu HTML bạn gửi
            links = container.find_all('a', href=True)
            for a in links:
                href = a['href']
                # Chỉ lấy link bài viết (thường có đuôi .html và chứa mã d+số)
                if '.html' in href and href != self.base_url:
                    full_url = href if href.startswith('http') else self.base_url + href
                    if full_url not in article_links:
                        article_links.append(full_url)
                
                if len(article_links) >= max_articles:
                    break

        print(f"✓ Tìm thấy {len(article_links)} bài viết từ trang chủ.")

        for i, link in enumerate(article_links, 1):
            print(f"[{i}/{len(article_links)}] Đang cào: {link}")
            self.sleep()
            data = self._fetch_article_detail(link)
            if data:
                all_articles.append(data)
        
        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Title (Khớp với h1.detail-title)
        title_el = soup.select_one('h1.detail-title')
        title = title_el.get_text(strip=True) if title_el else ""

        # 2. Category (Khớp với li.breadcrumb-item a)
        category = "FINANCE"
        cate_el = soup.select_one('.breadcrumb-item a.breadcrumb-link')
        if cate_el:
            category = cate_el.get_text(strip=True).upper()

        # 3. Published At (Khớp với thẻ span chứa định dạng dd/mm/yyyy hh:mm)
        published_at = int(datetime.now().timestamp())
        # Tìm thẻ span có nội dung chứa ngày tháng
        date_el = soup.find('span', string=re.compile(r'\d{2}/\d{2}/\d{4}'))
        if date_el:
            date_str = re.search(r'\d{2}/\d{2}/\d{4}', date_el.get_text()).group()
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                published_at = int(dt.timestamp())
            except: pass

        # 4. Content (Khớp với #news_detail #explus-editor)
        paragraphs = []
        # Lấy Sapo trước (vì nó chứa tóm tắt quan trọng)
        sapo_el = soup.select_one('.detail-sapo')
        if sapo_el:
            paragraphs.append(sapo_el.get_text(strip=True))

        # Lấy các đoạn trong nội dung chính
        content_div = soup.select_one('#news_detail #explus-editor')
        if content_div:
            # Duyệt qua các thẻ p, bỏ qua các thẻ ads/script bên trong
            for p in content_div.find_all('p', recursive=False):
                txt = p.get_text(strip=True)
                if len(txt) > 20: # Bỏ qua các dòng quá ngắn
                    paragraphs.append(txt)
        
        content = "\n\n".join(paragraphs)

        if not title or len(content) < 100:
            return None

        return (published_at, title, link, content, self.source, "NA", "NA", False, category)


class XaydungChinhsachScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "xaydungchinhsach.chinhphu.vn"
        self.base_url = "https://xaydungchinhsach.chinhphu.vn"

    def fetch_news(self, max_articles: int = 10) -> List[Tuple]:
        all_articles = []
        # Trang chủ của site này chính là danh sách tin nổi bật/mới nhất
        html = self.fetch_html(self.base_url)
        if not html: return []

        soup = BeautifulSoup(html, 'html.parser')
        article_links = []

        # Tìm tất cả các link bài viết (thường nằm trong các khối tin)
        # Site này sử dụng các thẻ a có thuộc tính title rất đầy đủ
        links = soup.select('a[title]')
        for a in links:
            href = a.get('href')
            # Lọc các link là bài viết:
            # - Phải có .htm
            # - Phải có mã ID số (ví dụ: 119260101192109677.htm)
            # - Loại bỏ category pages (không có số hoặc quá ngắn)
            if href and '.htm' in href and not href.startswith('javascript'):
                # Kiểm tra href có chứa chuỗi số dài (article ID)
                # Article URLs thường có format: /abc-xyz-119260101192109677.htm
                if re.search(r'\d{10,}', href):  # Có ít nhất 10 chữ số liên tiếp = article ID
                    full_url = href if href.startswith('http') else self.base_url + href
                    if full_url not in article_links:
                        article_links.append(full_url)

            if len(article_links) >= max_articles:
                break

        print(f"✓ Tìm thấy {len(article_links)} bài viết từ Xây dựng chính sách.")

        for i, link in enumerate(article_links, 1):
            print(f"[{i}/{len(article_links)}] Đang cào: {link}")
            self.sleep()
            data = self._fetch_article_detail(link)
            if data:
                all_articles.append(data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Title - Dùng data-role hoặc class chính xác
        title = ""
        title_el = soup.select_one('h1[data-role="title"]') or soup.select_one('h1.title') or soup.find('h1')
        if title_el:
            title = title_el.get_text(strip=True)

        # 2. Category - Từ breadcrumbs
        category = "POLICY"
        cat_el = soup.select_one('.list-cate a[data-role="cate-name"]') or soup.select_one('.list-cate a.item-cate')
        if cat_el:
            category = cat_el.get_text(strip=True).upper()

        # 3. Published At - Dùng data-role="publishdate"
        published_at = int(datetime.now().timestamp())
        date_el = soup.select_one('p[data-role="publishdate"]') or soup.select_one('p.days')
        if date_el:
            date_text = date_el.get_text(strip=True)
            # Format: "03/01/2026 08:56" hoặc "03/01/2026"
            match = re.search(r'(\d{2}/\d{2}/\d{4})', date_text)
            if match:
                try:
                    dt = datetime.strptime(match.group(1), "%d/%m/%Y")
                    published_at = int(dt.timestamp())
                except: pass

        # 4. Content - Lấy từ sapo + detail-content
        paragraphs = []

        # Lấy sapo (lead/summary)
        sapo_el = soup.select_one('h2[data-role="sapo"]') or soup.select_one('.detail-sapo')
        if sapo_el:
            sapo_text = sapo_el.get_text(strip=True)
            if len(sapo_text) > 20:
                paragraphs.append(sapo_text)

        # Lấy content chính
        content_area = soup.select_one('div[data-role="content"]') or soup.select_one('.detail-content.afcbc-body')
        if content_area:
            # Lấy các thẻ p, h2, h3, h4 (bỏ qua figure, script, style)
            for elem in content_area.find_all(['p', 'h2', 'h3', 'h4']):
                txt = elem.get_text(strip=True)
                # Bỏ qua các đoạn quá ngắn, chú thích ảnh, link download
                if len(txt) > 30 and not any(skip in txt.lower() for skip in ['nguồn:', 'tham khảo thêm', 'toàn văn:', '---']):
                    paragraphs.append(txt)

        content = "\n\n".join(paragraphs)

        if not title or not content: return None

        return (published_at, title, link, content, self.source, "NA", "NA", False, category)

class QDNDRSSScraper(NewsScraperBase):
    def __init__(self):
        super().__init__()
        self.source = "qdnd.vn"
        self.rss_url = "https://www.qdnd.vn/rss/cate/tin-tuc-moi-nhat.rss"

    def fetch_news(self, max_articles: int = 10) -> List[Tuple]:
        all_articles = []

        print(f"\n📡 Đang đọc RSS từ: {self.rss_url}")

        # 1. Fetch RSS với requests (vì feedparser trực tiếp bị chặn bởi redirect)
        try:
            import requests
            response = requests.get(self.rss_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            # Parse RSS content bằng feedparser
            feed = feedparser.parse(response.text)
        except Exception as e:
            print(f"⚠ Lỗi khi fetch RSS: {e}")
            return []

        if not feed.entries:
            print("⚠ Không thể lấy dữ liệu từ RSS.")
            return []

        # 2. Lấy danh sách các link bài viết
        article_links = []
        for entry in feed.entries:
            link = entry.link
            if link not in article_links:
                article_links.append(link)
            if len(article_links) >= max_articles:
                break

        print(f"✓ Tìm thấy {len(article_links)} bài viết mới từ RSS.")

        # 3. Duyệt từng bài để cào nội dung chi tiết
        for i, link in enumerate(article_links, 1):
            print(f"[{i}/{len(article_links)}] Đang cào: {link}")
            self.sleep()
            data = self._fetch_article_detail(link)
            if data:
                all_articles.append(data)

        return all_articles

    def _fetch_article_detail(self, link: str) -> Optional[Tuple]:
        html = self.fetch_html(link)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Title: Báo QDND dùng class post-title
        title_el = soup.select_one('h1.post-title')
        title = title_el.get_text(strip=True) if title_el else ""

        # 2. Category: Lấy từ breadcrumb (link đầu tiên)
        category = "MILITARY"
        # Tìm link đầu tiên trong breadcrumb với rel="v:url" và property="v:title"
        cate_el = soup.find('a', rel='v:url', property='v:title')
        if cate_el:
            category = cate_el.get_text(strip=True).upper()

        # 3. Published At: Lấy từ class post-date (Ví dụ: Chủ nhật, 04/01/2026)
        published_at = int(datetime.now().timestamp())
        date_el = soup.select_one('.post-date')
        if date_el:
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', date_el.get_text())
            if date_match:
                try:
                    dt = datetime.strptime(date_match.group(1), "%d/%m/%Y")
                    published_at = int(dt.timestamp())
                except: pass

        # 4. Content: Báo QDND dùng class post-content
        paragraphs = []
        # Lấy Sapo (Tóm tắt)
        sapo_el = soup.select_one('.post-summary')
        if sapo_el:
            paragraphs.append(sapo_el.get_text(strip=True))

        # Lấy nội dung chính
        content_area = soup.select_one('.post-content')
        if content_area:
            # Loại bỏ các div quảng cáo, video, ảnh liên quan nếu có
            for r in content_area.select('.related-post, .video-wrapper, .author-info'):
                r.decompose()
            
            for p in content_area.find_all('p'):
                txt = p.get_text(strip=True)
                if len(txt) > 30:
                    paragraphs.append(txt)
        
        content = "\n\n".join(paragraphs)

        if not title or len(content) < 100:
            return None

        return (published_at, title, link, content, self.source, "NA", "NA", False, category)
