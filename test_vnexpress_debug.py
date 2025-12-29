# -*- coding: utf-8 -*-
import sys
import io
import requests
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Lấy một bài báo mẫu từ VnExpress
url = 'https://vnexpress.net/viet-nam-se-tang-cuong-hop-tac-voi-un-women-4838968.html'
headers = {'User-Agent': 'Mozilla/5.0'}

print(f"Fetching: {url}\n")
resp = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(resp.text, 'html.parser')

print("=" * 60)
print("Test 1: Extract published_at từ span.date")
print("=" * 60)
date_el = soup.select_one('span.date')
if date_el:
    print(f"✓ Found!")
    print(f"  Raw text: {date_el.get_text(strip=True)}")
else:
    print("✗ NOT FOUND")

print("\n" + "=" * 60)
print("Test 2: Extract category từ a.back-folder.minus")
print("=" * 60)
back_link = soup.select_one('a.back-folder.minus')
if back_link:
    print(f"✓ Found!")
    print(f"  Raw text: {back_link.get_text(strip=True)}")
    print(f"  href: {back_link.get('href', '')}")

    # Test extraction logic
    category_text = back_link.get_text(strip=True)
    if 'Trở lại' in category_text:
        category = category_text.replace('Trở lại', '').strip()
        print(f"  Extracted category: {category}")
else:
    print("✗ NOT FOUND")

print("\n" + "=" * 60)
print("Test 3: Check div.box-category")
print("=" * 60)
box_cat = soup.select_one('div.box-category')
if box_cat:
    print(f"✓ Found div.box-category")
    print(f"  Content: {box_cat.get_text(strip=True)[:100]}...")
    print(f"  → Không có category info, chỉ chứa ads")
else:
    print("✗ NOT FOUND")

print("\n" + "=" * 60)
print("Test 4: Alternative selectors")
print("=" * 60)

# Try breadcrumb
breadcrumb = soup.select('ul.breadcrumb li a, .breadcrumb a')
if breadcrumb:
    print("\n[Option 1] Breadcrumb:")
    for i, bc in enumerate(breadcrumb, 1):
        print(f"  {i}. {bc.get_text(strip=True)} - {bc.get('href', '')}")

# Try meta tags
print("\n[Option 2] Meta tags:")
article_section = soup.find('meta', {'property': 'article:section'})
if article_section:
    print(f"  article:section: {article_section.get('content', '')}")
else:
    print("  ✗ No article:section")

keywords = soup.find('meta', {'name': 'keywords'})
if keywords:
    print(f"  keywords: {keywords.get('content', '')[:60]}...")

print("\n" + "=" * 60)
print("Debug complete")
print("=" * 60)
