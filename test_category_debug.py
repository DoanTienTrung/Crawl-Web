# -*- coding: utf-8 -*-
import sys
import io
import requests
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'https://cafef.vn/hose-chinh-thuc-co-quyen-chu-tich-va-tong-giam-doc-moi-tu-ngay-1-1-2026-18825122916005559.chn'
headers = {'User-Agent': 'Mozilla/5.0'}

print(f"Fetching: {url}\n")
resp = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(resp.text, 'html.parser')

print("=" * 60)
print("Test 1: li.acvmenu.active a[title]")
print("=" * 60)
active_menu = soup.select_one('li.acvmenu.active a[title]')
if active_menu:
    print(f"✓ Found!")
    print(f"  Title: {active_menu.get('title', '')}")
    print(f"  Text: {active_menu.get_text(strip=True)}")
else:
    print("✗ NOT FOUND")

print("\n" + "=" * 60)
print("Test 2: Find all li.acvmenu")
print("=" * 60)
all_menus = soup.select('li.acvmenu')
print(f"Total: {len(all_menus)}")
for i, menu in enumerate(all_menus[:5], 1):
    link = menu.select_one('a')
    classes = menu.get('class', [])
    if link:
        print(f"{i}. ID: {menu.get('id', '')} | Classes: {classes} | Title: {link.get('title', '')}")

print("\n" + "=" * 60)
print("Test 3: Find li.acvmenu.active (without a[title])")
print("=" * 60)
active_li = soup.select_one('li.acvmenu.active')
if active_li:
    print(f"✓ Found!")
    print(f"  ID: {active_li.get('id', '')}")
    print(f"  Classes: {active_li.get('class', [])}")
    link = active_li.select_one('a')
    if link:
        print(f"  Link title: {link.get('title', '')}")
else:
    print("✗ NOT FOUND")

print("\n" + "=" * 60)
print("Test 4: Check breadcrumb")
print("=" * 60)
breadcrumb = soup.select('.breadcrumb a, .bread-crumb a, ul.breadcrumb li a')
if breadcrumb:
    for i, bc in enumerate(breadcrumb, 1):
        print(f"{i}. {bc.get_text(strip=True)} - {bc.get('href', '')}")
else:
    print("✗ No breadcrumb found")

print("\n" + "=" * 60)
print("Test 5: Check meta keywords")
print("=" * 60)
meta_keywords = soup.find('meta', {'name': 'keywords'})
if meta_keywords:
    print(f"Keywords: {meta_keywords.get('content', '')}")

print("\n" + "=" * 60)
print("Test 6: Check article:section meta")
print("=" * 60)
article_section = soup.find('meta', {'property': 'article:section'})
if article_section:
    print(f"Section: {article_section.get('content', '')}")
else:
    print("✗ NOT FOUND")
