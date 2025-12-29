# -*- coding: utf-8 -*-
import sys
import io
import requests
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'Referer': 'https://vov.vn/'
}

print("=" * 60)
print("VOV Debug - Test pagination")
print("=" * 60)

for page in range(3):  # Test 3 pages
    if page == 0:
        url = "https://vov.vn/tin-moi-cap-nhat"
    else:
        url = f"https://vov.vn/tin-moi-cap-nhat?page={page}"

    print(f"\n{'='*60}")
    print(f"Page {page}: {url}")
    print(f"{'='*60}")

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")

        if resp.status_code != 200:
            print(f"⚠ Failed with status {resp.status_code}")
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Test current selector
        print("\n[Test 1] div.taxonomy-content:")
        content_divs = soup.select('div.taxonomy-content')
        print(f"  Found: {len(content_divs)} divs")

        # Test alternative selectors
        print("\n[Test 2] Alternative selectors:")

        selectors = [
            ('article', 'article'),
            ('.article-item', '.article-item'),
            ('.news-item', '.news-item'),
            ('div[class*="content"]', 'div with "content" in class'),
            ('div[class*="taxonomy"]', 'div with "taxonomy" in class'),
            ('.card', '.card'),
            ('h5.media-title', 'h5.media-title (title element)'),
            ('a.vovvn-title', 'a.vovvn-title (link element)'),
        ]

        for selector, desc in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"  ✓ {desc}: {len(elements)} found")
            else:
                print(f"  ✗ {desc}: 0 found")

        # Check pagination
        print("\n[Test 3] Pagination:")
        pagination = soup.select_one('ul.pagination')
        if pagination:
            page_links = pagination.select('a.page-link')
            print(f"  ✓ Found pagination with {len(page_links)} links")
            for link in page_links[:5]:  # Show first 5
                href = link.get('href', '')
                text = link.get_text(strip=True)
                print(f"    - {text}: {href}")
        else:
            print(f"  ✗ No pagination found")

        # Show first article if found
        if content_divs:
            print("\n[Test 4] First article structure:")
            first_div = content_divs[0]

            # Title
            title_el = first_div.select_one('h5.media-title') or first_div.select_one('h3.card-title')
            if title_el:
                print(f"  Title: {title_el.get_text(strip=True)[:50]}...")

            # Link
            link_el = first_div.select_one('a.vovvn-title')
            if link_el:
                print(f"  Link: {link_el.get('href', '')}")

            # Description
            desc_el = first_div.select_one('p.mt-2')
            if desc_el:
                print(f"  Desc: {desc_el.get_text(strip=True)[:50]}...")

    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("Debug complete")
print("=" * 60)
