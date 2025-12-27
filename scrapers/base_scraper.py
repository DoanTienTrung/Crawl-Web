from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from abc import ABC, abstractmethod
import time
import sys
sys.path.append('..')
from config import config


class BaseScraper(ABC):
    """
    Base class cho tất cả scrapers.
    Mỗi trang báo sẽ extend class này và implement các phương thức abstract.
    """
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.source_name = "Unknown"  # Override trong subclass
    
    def setup_driver(self):
        """Khởi tạo Selenium WebDriver"""
        options = Options()
        
        if config.HEADLESS:
            options.add_argument("--headless=new")
        
        # Các options để tránh bị detect là bot
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Tắt các thông báo và logs không cần thiết
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--log-level=3")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        self.wait = WebDriverWait(self.driver, 10)
        
        print(f"✓ WebDriver initialized for {self.source_name}")
    
    def close_driver(self):
        """Đóng WebDriver"""
        if self.driver:
            self.driver.quit()
            print(f"✓ WebDriver closed for {self.source_name}")
    
    def get_page(self, url: str):
        """Load một trang web"""
        try:
            self.driver.get(url)
            time.sleep(config.REQUEST_DELAY)  # Delay để tránh bị block
            return True
        except Exception as e:
            print(f"✗ Error loading {url}: {e}")
            return False
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Đợi element xuất hiện"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception:
            return None
    
    def safe_get_text(self, element, selector: str, by: By = By.CSS_SELECTOR) -> str:
        """Lấy text từ element một cách an toàn"""
        try:
            el = element.find_element(by, selector)
            return el.text.strip()
        except Exception:
            return ""
    
    def safe_get_attribute(self, element, selector: str, attribute: str, by: By = By.CSS_SELECTOR) -> str:
        """Lấy attribute từ element một cách an toàn"""
        try:
            el = element.find_element(by, selector)
            return el.get_attribute(attribute)
        except Exception:
            return ""
    
    def scroll_to_bottom(self, pause_time: float = 1.0):
        """Scroll xuống cuối trang (cho infinite scroll)"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause_time)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    @abstractmethod
    def get_article_urls(self, category_url: str) -> list:
        """
        Lấy danh sách URLs của các bài báo từ trang category.
        Mỗi subclass phải implement method này.
        """
        pass
    
    @abstractmethod
    def parse_article(self, url: str) -> dict:
        """
        Parse một bài báo và trả về dict chứa thông tin.
        Mỗi subclass phải implement method này.
        
        Returns:
            dict với các keys: title, url, summary, content, author, 
                              category, source, published_at, tags
        """
        pass
    
    def scrape_category(self, category_url: str, max_articles: int = 10) -> list:
        """Scrape tất cả bài báo từ một category"""
        articles = []
        
        print(f"\n{'='*60}")
        print(f"Scraping category: {category_url}")
        print(f"{'='*60}")
        
        # Lấy danh sách URLs
        urls = self.get_article_urls(category_url)
        print(f"Found {len(urls)} article URLs")
        
        # Giới hạn số lượng
        urls = urls[:max_articles]
        
        # Parse từng bài
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Parsing: {url}")
            try:
                article = self.parse_article(url)
                if article:
                    articles.append(article)
                    print(f"  ✓ Title: {article['title'][:50]}...")
            except Exception as e:
                print(f"  ✗ Error: {e}")
            
            time.sleep(config.REQUEST_DELAY)
        
        return articles
    
    def run(self, category_urls: list, max_per_category: int = 10) -> list:
        """
        Main method để chạy scraper.
        
        Args:
            category_urls: List các URL category cần scrape
            max_per_category: Số bài tối đa mỗi category
        
        Returns:
            List tất cả articles đã scrape được
        """
        all_articles = []
        
        try:
            self.setup_driver()
            
            for cat_url in category_urls:
                articles = self.scrape_category(cat_url, max_per_category)
                all_articles.extend(articles)
            
            print(f"\n{'='*60}")
            print(f"TOTAL: Scraped {len(all_articles)} articles")
            print(f"{'='*60}")
            
        finally:
            self.close_driver()
        
        return all_articles
