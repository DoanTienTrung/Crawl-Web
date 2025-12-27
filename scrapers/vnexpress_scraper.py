from selenium.webdriver.common.by import By
from datetime import datetime
import re
import sys
sys.path.append('..')
from scrapers.base_scraper import BaseScraper


class VnExpressScraper(BaseScraper):
    """
    Scraper cho trang VnExpress.net
    
    Cấu trúc HTML của VnExpress (có thể thay đổi theo thời gian):
    - Article list: .item-news hoặc .article-item
    - Title: .title-news
    - Summary: .description
    - Content: .fck_detail
    - Author: .author_mail hoặc .fck_detail p strong cuối cùng
    - Published date: .date
    """
    
    def __init__(self):
        super().__init__()
        self.source_name = "VnExpress"
        self.base_url = "https://vnexpress.net"
    
    def get_article_urls(self, category_url: str) -> list:
        """Lấy danh sách URLs bài báo từ trang category"""
        urls = []
        
        if not self.get_page(category_url):
            return urls
        
        try:
            # Scroll để load thêm bài (nếu có lazy loading)
            self.driver.execute_script("window.scrollTo(0, 2000);")
            
            # Tìm tất cả các article items
            # VnExpress thường dùng class .item-news hoặc .title-news a
            article_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".item-news .title-news a, article.item-news h3 a, .item-news-common .title-news a"
            )
            
            for element in article_elements:
                href = element.get_attribute("href")
                if href and href.startswith("http") and "/video/" not in href:
                    # Loại bỏ video, chỉ lấy bài viết text
                    urls.append(href)
            
            # Loại bỏ duplicates và giữ thứ tự
            urls = list(dict.fromkeys(urls))
            
        except Exception as e:
            print(f"Error getting article URLs: {e}")
        
        return urls
    
    def parse_article(self, url: str) -> dict:
        """Parse nội dung một bài báo VnExpress"""
        
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
            # Title
            title_el = self.wait_for_element(By.CSS_SELECTOR, "h1.title-detail")
            if title_el:
                article['title'] = title_el.text.strip()
            
            # Summary/Description
            try:
                desc_el = self.driver.find_element(By.CSS_SELECTOR, "p.description")
                article['summary'] = desc_el.text.strip()
            except:
                pass
            
            # Content - lấy tất cả paragraphs trong .fck_detail
            try:
                content_el = self.driver.find_element(By.CSS_SELECTOR, "article.fck_detail")
                paragraphs = content_el.find_elements(By.TAG_NAME, "p")
                content_parts = []
                for p in paragraphs:
                    text = p.text.strip()
                    if text and not text.startswith(">>"):  # Loại bỏ related links
                        content_parts.append(text)
                article['content'] = "\n\n".join(content_parts)
            except:
                pass
            
            # Author - thường nằm ở cuối bài hoặc trong .author
            try:
                author_el = self.driver.find_element(By.CSS_SELECTOR, "p.author_mail strong, p.Normal[style*='right'] strong")
                article['author'] = author_el.text.strip()
            except:
                # Thử cách khác - lấy tên tác giả từ cuối bài
                try:
                    author_el = self.driver.find_element(By.CSS_SELECTOR, ".fck_detail p:last-child strong")
                    article['author'] = author_el.text.strip()
                except:
                    pass
            
            # Category - lấy từ breadcrumb
            try:
                category_el = self.driver.find_element(By.CSS_SELECTOR, "ul.breadcrumb li:nth-child(2) a")
                article['category'] = category_el.text.strip()
            except:
                pass
            
            # Published date
            try:
                date_el = self.driver.find_element(By.CSS_SELECTOR, "span.date")
                date_text = date_el.text.strip()
                article['published_at'] = self._parse_date(date_text)
            except:
                pass
            
            # Tags
            try:
                tag_elements = self.driver.find_elements(By.CSS_SELECTOR, ".tags a, .tag a")
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
    
    def _parse_date(self, date_text: str) -> datetime:
        """
        Parse date từ format của VnExpress.
        VD: "Thứ hai, 25/12/2024, 10:30 (GMT+7)"
        """
        try:
            # Regex để extract ngày tháng năm giờ phút
            match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4}),?\s*(\d{1,2}):(\d{2})', date_text)
            if match:
                day, month, year, hour, minute = match.groups()
                return datetime(int(year), int(month), int(day), int(hour), int(minute))
        except:
            pass
        return None


# Các category URLs phổ biến của VnExpress
VNEXPRESS_CATEGORIES = {
    'thoi_su': 'https://vnexpress.net/thoi-su',
    'the_gioi': 'https://vnexpress.net/the-gioi',
    'kinh_doanh': 'https://vnexpress.net/kinh-doanh',
    'giai_tri': 'https://vnexpress.net/giai-tri',
    'the_thao': 'https://vnexpress.net/the-thao',
    'phap_luat': 'https://vnexpress.net/phap-luat',
    'giao_duc': 'https://vnexpress.net/giao-duc',
    'suc_khoe': 'https://vnexpress.net/suc-khoe',
    'doi_song': 'https://vnexpress.net/doi-song',
    'khoa_hoc': 'https://vnexpress.net/khoa-hoc',
    'so_hoa': 'https://vnexpress.net/so-hoa',
    'xe': 'https://vnexpress.net/oto-xe-may',
}
