# 📋 REFACTOR PLAN - News Scraper Project

## 🎯 Mục tiêu
Tách file `scrapers/multi_source_scraper.py` (~2000+ lines) thành **mỗi trang báo 1 file** riêng để dễ đọc và maintain.

---

## 📊 Phân tích hiện trạng

### Vấn đề
- ❌ File quá lớn (~2000+ lines) - khó đọc, khó maintain
- ❌ 14 scraper classes trong 1 file
- ❌ Khó test từng scraper riêng lẻ
- ❌ Thêm source mới phải edit file khổng lồ

### Scrapers hiện tại
1. VnExpressScraper
2. VnEconomyScraper (RSS)
3. VOVScraper
4. VietnametScraper
5. CafelandScraper
6. CafeFScraper
7. DanTriRSSScraper (RSS)
8. ThanhNienRSSScraper (RSS)
9. TuoiTreRSSScraper (RSS)
10. VietStockScraper (Selenium)
11. NLDScraper
12. LaoDongScraper
13. ANTTRSSScraper (RSS)
14. (Có thể có thêm sau line 2000)

---

## 🏗️ Cấu trúc mới (Flat - Đơn giản nhất)

```
scrapers/
├── __init__.py                    # Exports + Registry
├── base.py                        # NewsScraperBase (giữ nguyên)
├── vnexpress.py
├── vneconomy.py
├── vov.py
├── vietnamnet.py
├── cafeland.py
├── cafef.py
├── dantri.py
├── thanhnien.py
├── tuoitre.py
├── vietstock.py
├── nld.py
├── laodong.py
└── antt.py
```

---

## 📝 Chi tiết các bước thực hiện

### **PHASE 1: Preparation** (Ưu tiên: Cao)

#### Step 1.1: Đọc toàn bộ file gốc
- [ ] Đọc hết file `multi_source_scraper.py` (cả phần sau line 2000)
- [ ] List tất cả scrapers có trong file
- [ ] Ghi chú các dependencies đặc biệt (selenium, feedparser, brotli, etc.)

#### Step 1.2: Tách NewsScraperBase
- [ ] Copy class `NewsScraperBase` từ `multi_source_scraper.py`
- [ ] Tạo file `scrapers/base.py`
- [ ] Paste `NewsScraperBase` vào (giữ nguyên 100%, không sửa gì)

---

### **PHASE 2: Tách từng Scraper** (Ưu tiên: Cao)

#### Step 2.1: Template cho mỗi scraper
```python
# scrapers/example.py
from scrapers.base import NewsScraperBase
from typing import List, Tuple, Optional

class ExampleScraper(NewsScraperBase):
    """Copy toàn bộ code từ file gốc, chỉ đổi import"""

    def __init__(self):
        super().__init__()
        self.source = "example.com"

    def fetch_news(self, ...):
        # Copy nguyên code từ file gốc
        pass

    def _fetch_article_detail(self, ...):
        # Copy nguyên code từ file gốc
        pass
```

#### Step 2.2: Tách từng scraper (Copy nguyên code, chỉ đổi import)

**Tất cả scrapers - làm tuần tự:**

- [ ] `scrapers/vnexpress.py` - Copy class `VnExpressScraper`
- [ ] `scrapers/vneconomy.py` - Copy class `VnEconomyScraper`
- [ ] `scrapers/vov.py` - Copy class `VOVScraper`
- [ ] `scrapers/vietnamnet.py` - Copy class `VietnametScraper`
- [ ] `scrapers/cafeland.py` - Copy class `CafelandScraper`
- [ ] `scrapers/cafef.py` - Copy class `CafeFScraper`
- [ ] `scrapers/dantri.py` - Copy class `DanTriRSSScraper`
- [ ] `scrapers/thanhnien.py` - Copy class `ThanhNienRSSScraper`
- [ ] `scrapers/tuoitre.py` - Copy class `TuoiTreRSSScraper`
- [ ] `scrapers/vietstock.py` - Copy class `VietStockScraper`
- [ ] `scrapers/nld.py` - Copy class `NLDScraper`
- [ ] `scrapers/laodong.py` - Copy class `LaoDongScraper`
- [ ] `scrapers/antt.py` - Copy class `ANTTRSSScraper`

**Lưu ý mỗi file:**
- Import: `from scrapers.base import NewsScraperBase`
- Import thêm: `from typing import List, Tuple, Optional`
- Import dependencies (feedparser, selenium, etc.) nếu class đó cần
- Copy 100% code của class, không sửa logic

---

### **PHASE 3: Registry & Integration** (Ưu tiên: Cao)

#### Step 3.1: Tạo scrapers/__init__.py
- [ ] Import tất cả scrapers
- [ ] Tạo Registry để dễ sử dụng

```python
# scrapers/__init__.py
from scrapers.base import NewsScraperBase

# Import all scrapers
from scrapers.vnexpress import VnExpressScraper
from scrapers.vneconomy import VnEconomyScraper
from scrapers.vov import VOVScraper
from scrapers.vietnamnet import VietnametScraper
from scrapers.cafeland import CafelandScraper
from scrapers.cafef import CafeFScraper
from scrapers.dantri import DanTriRSSScraper
from scrapers.thanhnien import ThanhNienRSSScraper
from scrapers.tuoitre import TuoiTreRSSScraper
from scrapers.vietstock import VietStockScraper
from scrapers.nld import NLDScraper
from scrapers.laodong import LaoDongScraper
from scrapers.antt import ANTTRSSScraper

# Registry (optional - để dễ sử dụng)
SCRAPERS = {
    'vnexpress': VnExpressScraper,
    'vneconomy': VnEconomyScraper,
    'vov': VOVScraper,
    'vietnamnet': VietnametScraper,
    'cafeland': CafelandScraper,
    'cafef': CafeFScraper,
    'dantri': DanTriRSSScraper,
    'thanhnien': ThanhNienRSSScraper,
    'tuoitre': TuoiTreRSSScraper,
    'vietstock': VietStockScraper,
    'nld': NLDScraper,
    'laodong': LaoDongScraper,
    'antt': ANTTRSSScraper,
}
```

---

### **PHASE 4: Update Main Scripts** (Ưu tiên: Cao)

#### Step 4.1: Tìm files sử dụng scrapers
- [ ] Search toàn project: `from scrapers.multi_source_scraper import`
- [ ] List tất cả files cần update

#### Step 4.2: Update imports
```python
# Cũ
from scrapers.multi_source_scraper import VnExpressScraper, VOVScraper

# Mới - Cách 1: Import trực tiếp
from scrapers.vnexpress import VnExpressScraper
from scrapers.vov import VOVScraper

# Mới - Cách 2: Import từ __init__ (khuyến nghị)
from scrapers import VnExpressScraper, VOVScraper

# Mới - Cách 3: Dùng Registry
from scrapers import SCRAPERS
scraper = SCRAPERS['vnexpress']()
```

---

### **PHASE 5: Testing** (Ưu tiên: Cao)

#### Step 5.1: Test từng scraper
- [ ] Test VnExpressScraper - chạy thử `fetch_news()`
- [ ] Test VnEconomyScraper
- [ ] Test VOVScraper
- [ ] Test các scrapers còn lại
- [ ] Verify output giống với version cũ

#### Step 5.2: Test integration
- [ ] Run main scripts
- [ ] Verify không có import errors
- [ ] Verify không có runtime errors

---

### **PHASE 6: Cleanup** (Ưu tiên: Thấp)

- [ ] Backup file cũ:
  ```bash
  mv scrapers/multi_source_scraper.py scrapers/multi_source_scraper.py.backup
  ```
- [ ] Hoặc xóa sau khi test kỹ
- [ ] Commit changes:
  ```bash
  git add scrapers/
  git commit -m "refactor: split multi_source_scraper into separate files"
  ```

---

## 🎯 Checklist tổng quan

### Phase 1: Preparation ⏳
- [ ] Đọc toàn bộ file source
- [ ] Tách NewsScraperBase ra `base.py`

### Phase 2: Split Scrapers ⏳
- [ ] Tách 13 scrapers ra file riêng
- [ ] Mỗi file import đúng dependencies
- [ ] Copy 100% code, không sửa logic

### Phase 3: Integration ⏳
- [ ] Tạo `scrapers/__init__.py`
- [ ] Setup Registry

### Phase 4: Update Imports ⏳
- [ ] Tìm files dùng old imports
- [ ] Update sang new imports

### Phase 5: Testing ⏳
- [ ] Test từng scraper
- [ ] Test main scripts
- [ ] Verify output

### Phase 6: Cleanup ⏳
- [ ] Backup file cũ
- [ ] Commit changes

---

## ⚠️ Lưu ý quan trọng

1. **KHÔNG sửa logic**: Copy nguyên code, chỉ đổi imports
2. **Backup trước**: Copy file gốc sang `.backup`
3. **Test ngay**: Test từng scraper sau khi tách
4. **Dependencies**: Check imports (feedparser, selenium, brotli)
5. **Giữ nguyên output**: Format Tuple không đổi

---

## 🚀 Bắt đầu từ đâu?

**Làm tuần tự:**
1. **Phase 1**: Đọc file → Tạo thư mục → Tách Base class (30 phút)
2. **Phase 2**: Tách từng scraper, 1 file/lần (3-4 giờ)
3. **Phase 3**: Setup __init__.py (30 phút)
4. **Phase 4**: Update imports trong main scripts (1 giờ)
5. **Phase 5**: Test tất cả (1-2 giờ)
6. **Phase 6**: Cleanup (15 phút)

**Tổng: ~6-8 giờ làm việc**

---

Bạn muốn mình bắt đầu implement không?
