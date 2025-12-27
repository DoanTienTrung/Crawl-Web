from selenium.webdriver.common.by import By
from datetime import datetime
import re
import sys
sys.path.append('..')
from scrapers.base_scraper import BaseScraper


class CafeFScraper(BaseScraper):
    """
    Scraper cho trang CafeF.vn - Trang tin tài chính, chứng khoán
    
    Trang "Đọc nhanh" có cấu trúc đặc biệt với timestamp rõ ràng.
    URL pattern: /doc-nhanh.chn (trang 1), /doc-nhanh/trang-2.chn (trang 2), ...
    """
    
    def __init__(self):
        super().__init__()
        self.source_name = "CafeF"
        self.base_url = "https://cafef.vn"
    
    def get_article_urls(self, category_url: str, max_pages: int = 1) -> list:
        """
        Lấy danh sách URLs bài báo từ trang category.
        Hỗ trợ pagination cho trang Đọc nhanh.
        """
        urls = []
        
        for page in range(1, max_pages + 1):
            # Xử lý pagination
            if page == 1:
                page_url = category_url
            else:
                # /doc-nhanh.chn -> /doc-nhanh/trang-2.chn
                if ".chn" in category_url:
                    base = category_url.replace(".chn", "")
                    page_url = f"{base}/trang-{page}.chn"
                else:
                    page_url = f"{category_url}/trang-{page}.chn"
            
            print(f"  Fetching page {page}: {page_url}")
            
            if not self.get_page(page_url):
                break
            
            try:
                # Tìm tất cả các links bài báo
                # CafeF thường dùng pattern: /ten-bai-viet-188251225205027358.chn
                article_links = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "a[href*='.chn']"
                )
                
                for link in article_links:
                    href = link.get_attribute("href")
                    if href and self._is_valid_article_url(href):
                        urls.append(href)
                
            except Exception as e:
                print(f"Error getting article URLs from page {page}: {e}")
                break
        
        # Loại bỏ duplicates và giữ thứ tự
        urls = list(dict.fromkeys(urls))
        return urls
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Kiểm tra xem URL có phải là bài báo hợp lệ không"""
        if not url:
            return False
        
        # Phải chứa ID số ở cuối (pattern: -188251225205027358.chn)
        if not re.search(r'-\d{15,}\.chn$', url):
            return False
        
        # Loại bỏ các trang category, static pages
        excluded_patterns = [
            '/doc-nhanh.chn',
            '/trang-',
            '/static/',
            '/du-lieu/',
            '/video/',
        ]
        
        for pattern in excluded_patterns:
            if pattern in url:
                return False
        
        return True
    
    def parse_article(self, url: str) -> dict:
        """Parse nội dung một bài báo CafeF"""
        
        if not self.get_page(url):
            return None
        
        article = {
            'url': url,
            'source': self.source_name,
            'title': '',
            'summary': '',
            'content': '',
            'author': '',
            'category': '',
            'published_at': None,
            'tags': ''
        }
        
        try:
            # Title - thường nằm trong h1
            try:
                title_el = self.driver.find_element(By.CSS_SELECTOR, "h1.title")
                article['title'] = title_el.text.strip()
            except:
                try:
                    title_el = self.driver.find_element(By.TAG_NAME, "h1")
                    article['title'] = title_el.text.strip()
                except:
                    pass
            
            # Summary/Sapo - mô tả ngắn đầu bài
            try:
                sapo_el = self.driver.find_element(By.CSS_SELECTOR, "h2.sapo, p.sapo, .sapo")
                article['summary'] = sapo_el.text.strip()
            except:
                pass
            
            # Content - nội dung chính
            try:
                # CafeF thường dùng class .detail-content hoặc .contentdetail
                content_selectors = [
                    ".detail-content",
                    ".contentdetail", 
                    ".detail_content",
                    "article .content",
                    ".maincontent"
                ]
                
                content_el = None
                for selector in content_selectors:
                    try:
                        content_el = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if content_el:
                    paragraphs = content_el.find_elements(By.TAG_NAME, "p")
                    content_parts = []
                    for p in paragraphs:
                        text = p.text.strip()
                        # Loại bỏ các đoạn không cần thiết
                        if text and not self._is_excluded_text(text):
                            content_parts.append(text)
                    article['content'] = "\n\n".join(content_parts)
            except Exception as e:
                print(f"  Error parsing content: {e}")
            
            # Author - tác giả
            try:
                author_selectors = [
                    ".author",
                    ".author-name", 
                    ".detail-author",
                    "p.source",
                    ".name-author"
                ]
                for selector in author_selectors:
                    try:
                        author_el = self.driver.find_element(By.CSS_SELECTOR, selector)
                        author_text = author_el.text.strip()
                        if author_text:
                            article['author'] = author_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Category - chuyên mục
            try:
                cat_selectors = [
                    ".breadcrumb a:nth-child(2)",
                    ".bread-crumb a",
                    "ul.breadcrumb li a"
                ]
                for selector in cat_selectors:
                    try:
                        cat_el = self.driver.find_element(By.CSS_SELECTOR, selector)
                        article['category'] = cat_el.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Published date
            try:
                date_selectors = [
                    ".dateandcat .date",
                    ".pdate",
                    ".date",
                    "time",
                    ".detail-time"
                ]
                for selector in date_selectors:
                    try:
                        date_el = self.driver.find_element(By.CSS_SELECTOR, selector)
                        date_text = date_el.text.strip()
                        if date_text:
                            article['published_at'] = self._parse_date(date_text)
                            break
                    except:
                        continue
                
                # Fallback: extract from datetime attribute
                if not article['published_at']:
                    try:
                        time_el = self.driver.find_element(By.TAG_NAME, "time")
                        datetime_attr = time_el.get_attribute("datetime")
                        if datetime_attr:
                            article['published_at'] = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    except:
                        pass
            except:
                pass
            
            # Tags
            try:
                tag_elements = self.driver.find_elements(By.CSS_SELECTOR, ".tags a, .tag-item a, .keywords a")
                tags = [tag.text.strip() for tag in tag_elements if tag.text.strip()]
                article['tags'] = ",".join(tags)
            except:
                pass
            
        except Exception as e:
            print(f"Error parsing article: {e}")
            return None
        
        # Validate - ít nhất phải có title
        if not article['title']:
            return None
        
        return article
    
    def _is_excluded_text(self, text: str) -> bool:
        """Kiểm tra text có nên bị loại bỏ không"""
        excluded_patterns = [
            "Link bài gốc",
            "Lấy link!",
            ">>",
            "Xem thêm:",
            "Đọc thêm:",
            "@",  # email
        ]
        
        for pattern in excluded_patterns:
            if pattern in text:
                return True
        
        # Loại bỏ text quá ngắn (thường là caption ảnh, v.v.)
        if len(text) < 10:
            return True
        
        return False
    
    def _parse_date(self, date_text: str) -> datetime:
        """
        Parse date từ các format của CafeF.
        VD: "25/12/2025 20:50", "25-12-2025 20:50", "2025-12-25T20:50:00"
        """
        try:
            # Format ISO
            if 'T' in date_text:
                return datetime.fromisoformat(date_text.replace('Z', '+00:00'))
            
            # Format: dd/mm/yyyy HH:MM hoặc dd-mm-yyyy HH:MM
            patterns = [
                (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})\s*(\d{1,2}):(\d{2})', 'dmy_hm'),
                (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dmy'),
            ]
            
            for pattern, fmt in patterns:
                match = re.search(pattern, date_text)
                if match:
                    groups = match.groups()
                    if fmt == 'dmy_hm':
                        day, month, year, hour, minute = groups
                        return datetime(int(year), int(month), int(day), int(hour), int(minute))
                    elif fmt == 'dmy':
                        day, month, year = groups
                        return datetime(int(year), int(month), int(day))
            
        except Exception as e:
            print(f"  Could not parse date '{date_text}': {e}")
        
        return None
    
    def scrape_doc_nhanh(self, max_pages: int = 1, max_articles: int = 20) -> list:
        """
        Scrape trang "Đọc nhanh" - tổng hợp tin mới nhất.
        
        Args:
            max_pages: Số trang cần crawl (mỗi trang ~20 bài)
            max_articles: Tổng số bài tối đa cần lấy
        """
        url = "https://cafef.vn/doc-nhanh.chn"
        return self.scrape_category(url, max_articles)


# Các category URLs phổ biến của CafeF
CAFEF_CATEGORIES = {
    'doc_nhanh': 'https://cafef.vn/doc-nhanh.chn',
    'chung_khoan': 'https://cafef.vn/thi-truong-chung-khoan.chn',
    'bat_dong_san': 'https://cafef.vn/bat-dong-san.chn',
    'doanh_nghiep': 'https://cafef.vn/doanh-nghiep.chn',
    'ngan_hang': 'https://cafef.vn/tai-chinh-ngan-hang.chn',
    'tai_chinh_quoc_te': 'https://cafef.vn/tai-chinh-quoc-te.chn',
    'vi_mo': 'https://cafef.vn/vi-mo-dau-tu.chn',
    'kinh_te_so': 'https://cafef.vn/kinh-te-so.chn',
    'thi_truong': 'https://cafef.vn/thi-truong.chn',
    'xa_hoi': 'https://cafef.vn/xa-hoi.chn',
}
