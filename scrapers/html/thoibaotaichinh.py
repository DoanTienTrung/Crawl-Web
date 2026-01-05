from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime


class ThoiBaoTaiChinhScraper(NewsScraperBase):
    """Scraper cho thoibaotaichinhvietnam.vn"""
    def __init__(self):
        super().__init__()
        self.source = "thoibaotaichinhvietnam.vn"
        self.headers["Referer"] = "https://thoibaotaichinhvietnam.vn/"

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
            print(f"[{i}/{len(article_urls)}] Fetching: {link}", flush=True)
            self.sleep()
            data = self._fetch_article_detail(link)
            if data:
                results.append(data)

        return results

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
            "NA",  
            "NA",
            False,
            category,
        )
