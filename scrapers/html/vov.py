from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime


class VOVScraper(NewsScraperBase):
    """
    Scraper cho VOV.vn - crawl từ trang "Tin mới cập nhật"
    """

    def __init__(self):
        super().__init__()
        self.source = "vov.vn"
        self.headers['Referer'] = 'https://vov.vn/'
        self.delay = 3  

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
