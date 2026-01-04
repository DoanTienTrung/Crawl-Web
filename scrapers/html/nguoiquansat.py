from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
from datetime import datetime


class NguoiQuanSatScraper(NewsScraperBase):
    """
    Scraper cho nguoiquansat.vn – chuẩn longform (đã fix lỗi 0 articles)
    """

    def __init__(self):
        super().__init__()
        self.source = "nguoiquansat.vn"
        self.headers["Referer"] = "https://nguoiquansat.vn/"

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
            "NA",    
            "NA",
            False,
            category,
        )
