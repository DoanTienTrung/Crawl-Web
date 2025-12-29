# -*- coding: utf-8 -*-
import sys
import io
import requests
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Lấy một bài báo mẫu từ Vietnamnet
url = 'https://vietnamnet.vn/bo-truong-quoc-phong-lam-viec-voi-ban-chap-hanh-dang-bo-quan-dung-2798089.html'
headers = {'User-Agent': 'Mozilla/5.0'}

print(f"Fetching: {url}\n")
resp = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(resp.text, 'html.parser')

print("=" * 60)
print("Test 1: Extract published_at từ div.bread-crumb-detail__time")
print("=" * 60)
date_el = soup.select_one('div.bread-crumb-detail__time')
if date_el:
    print(f"✓ Found!")
    print(f"  Raw text: {date_el.get_text(strip=True)}")

    # Test parsing logic
    date_text = date_el.get_text(strip=True)
    if date_text.startswith('Thứ'):
        parts = date_text.split(',', 1)
        if len(parts) > 1:
            date_text = parts[1].strip()
    date_text = date_text.replace(' - ', ' ')
    print(f"  Cleaned: {date_text}")
else:
    print("✗ NOT FOUND")

# Fallback
if not date_el:
    print("\nTrying span.time...")
    date_el = soup.select_one('span.time')
    if date_el:
        print(f"✓ Found in span.time: {date_el.get_text(strip=True)}")

print("\n" + "=" * 60)
print("Test 2: Extract category")
print("=" * 60)

# Current implementation: hardcoded "kinh-doanh"
print("Current implementation: category = 'kinh-doanh' (HARDCODED)")

print("\nTrying to find category from HTML...")

# Method 1: Breadcrumb
print("\n[Method 1] Breadcrumb:")
breadcrumb = soup.select('ul.breadcrumb li a, .breadcrumb a, .bread-crumb a')
if breadcrumb:
    for i, bc in enumerate(breadcrumb, 1):
        print(f"  {i}. {bc.get_text(strip=True)} - href: {bc.get('href', '')} - title: {bc.get('title', '')}")
else:
    print("  ✗ No breadcrumb found")

# Method 2: Link có title attribute gần published date
print("\n[Method 2] Links near bread-crumb-detail__time:")
parent = soup.select_one('div.bread-crumb-detail__time')
if parent and parent.parent:
    links = parent.parent.select('a[title]')
    for link in links:
        print(f"  - {link.get_text(strip=True)} | title: {link.get('title', '')} | href: {link.get('href', '')}")

# Method 3: Any <a> with title in the breadcrumb area
print("\n[Method 3] All <a> tags with category-like hrefs:")
category_links = soup.select('a[href^="/"][title]')
for link in category_links[:5]:  # Chỉ show 5 cái đầu
    href = link.get('href', '')
    title = link.get('title', '')
    text = link.get_text(strip=True)
    # Chỉ show nếu là category (không phải bài báo cụ thể)
    if href.count('/') <= 2 and not any(x in href for x in ['tin-tuc', 'p0', 'p1']):
        print(f"  - Text: {text} | Title: {title} | Href: {href}")

print("\n" + "=" * 60)
print("Test 3: Tìm chính xác category theo pattern user cung cấp")
print("=" * 60)
print("Pattern: <a href='/thoi-su' title='Thời sự'>Thời sự</a>")

# Selector chính xác hơn
selectors = [
    'a[href="/thoi-su"]',
    'a[title="Thời sự"]',
    '.breadcrumb a',
    'ul.breadcrumb li:nth-child(2) a',  # Usually category is 2nd item in breadcrumb
]

for selector in selectors:
    print(f"\nTrying: {selector}")
    el = soup.select_one(selector)
    if el:
        print(f"  ✓ Found: {el.get_text(strip=True)} | href: {el.get('href', '')} | title: {el.get('title', '')}")
    else:
        print(f"  ✗ Not found")
