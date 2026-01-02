# Multi-Source News Scraper

Tool crawl tin tức từ nhiều nguồn báo Việt Nam và lưu vào PostgreSQL.

## Supported Sources

| Source | URL | Status |
|--------|-----|--------|
| CafeF | cafef.vn | ✅ |
| VnExpress | vnexpress.net | ✅ |
| VnEconomy | vneconomy.vn | ✅ |
| VOV | vov.vn | ✅ |
| Vietnamnet | vietnamnet.vn | ✅ |

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS public.news (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    published_at bigint,
    title text NOT NULL,
    link text,
    content text,
    source text,
    stock_related text,
    sentiment_score text,
    server_pushed boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    category text,
    CONSTRAINT news_pkey PRIMARY KEY (id),
    CONSTRAINT news_title_key UNIQUE (title)
);
```

## Cài đặt

### 1. Clone và setup

```bash
cd news-scraper
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Tạo database PostgreSQL

```sql
CREATE DATABASE news_db;
```

### 3. Cấu hình .env

```bash
copy .env.example .env
```

Sửa file `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=news_db
DB_USER=postgres
DB_PASSWORD=your_password
```

## Sử dụng

### Scrape tất cả sources

```bash
python main.py
```

### Scrape từng source riêng

```bash
python main.py cafef        # Chỉ CafeF
python main.py vnexpress    # Chỉ VnExpress
python main.py vneconomy    # Chỉ VnEconomy status: processing
python main.py vov          # Chỉ VOV       status: processing
python main.py vietnamnet   # Chỉ Vietnamnet
```

### Export CSV only (không cần database)

```bash
python main.py csv
```

### Test mode

```bash
python main.py test
```

## Output

### Database
- Table: `news`
- Primary key: `id` (UUID)
- Unique constraint: `title`

### CSV Files
- Location: `exports/`
- Format: `{source}_{timestamp}.csv`

### CSV Columns

| Column | Type | Description |
|--------|------|-------------|
| published_at | bigint | Unix timestamp |
| title | text | Tiêu đề bài báo |
| link | text | URL bài báo |
| content | text | Nội dung |
| source | text | Nguồn (cafef.vn, vnexpress.net, ...) |
| stock_related | text | Mã chứng khoán liên quan |
| sentiment_score | text | Điểm sentiment |
| server_pushed | boolean | Đã push lên server chưa |
| category | text | Chuyên mục |

## Cấu trúc Project

```
news-scraper/
├── main.py                 # Entry point
├── config.py               # Configuration
├── requirements.txt
├── .env.example
├── README.md
│
├── database/
│   ├── __init__.py
│   └── models.py           # SQLAlchemy models (News table)
│
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py     # Base class (Selenium-based)
│   ├── cafef_scraper.py    # CafeF scraper (Selenium)
│   ├── vnexpress_scraper.py
│   └── multi_source_scraper.py  # ⭐ All scrapers (requests-based)
│
├── utils/
│   ├── __init__.py
│   └── exporters.py        # CSV & JSON exporters
│
└── exports/                # Output files
```

## So sánh với code Rust gốc

| Feature | Rust | Python |
|---------|------|--------|
| HTTP Client | reqwest | requests |
| HTML Parsing | scraper | BeautifulSoup |
| Database | sqlx (async) | SQLAlchemy |
| Compression | flate2, brotli | gzip, brotli |
| Browser automation | thirtyfour | selenium (optional) |

## 🤖 Scheduler - Tự động lập lịch scraping

### Cách sử dụng Scheduler

Scheduler giúp tự động chạy các scraper functions theo lịch đã định sẵn.

#### 1. Cài đặt thêm APScheduler

```bash
pip install -r requirements.txt
```

#### 2. Cấu hình lịch chạy

Chỉnh sửa file `scheduler_config.json`:

```json
{
  "jobs": [
    {
      "id": "scrape_all_news_hourly",
      "name": "Scrape tất cả nguồn tin mỗi giờ",
      "function": "scrape_all",
      "enabled": true,
      "schedule": {
        "type": "interval",
        "hours": 1
      },
      "description": "Chạy scrape_all() mỗi 1 giờ"
    }
  ],
  "timezone": "Asia/Ho_Chi_Minh",
  "log_file": "logs/news_scheduler.log",
  "log_level": "INFO"
}
```

#### 3. Chạy Scheduler

```bash
python scheduler.py
```

Output:
```
[2026-01-02 10:00:00] INFO - 🚀 Scheduler started successfully!
[2026-01-02 10:00:00] INFO - ⏰ Timezone: Asia/Ho_Chi_Minh
[2026-01-02 10:00:00] INFO - 📋 Total active jobs: 1
[2026-01-02 10:00:00] INFO -   🕐 Scrape tất cả nguồn tin mỗi giờ
[2026-01-02 10:00:00] INFO -      Next run: 2026-01-02 11:00:00
```

#### 4. Dừng Scheduler

Nhấn `Ctrl+C` để dừng gracefully.

### Các loại Schedule

#### Interval Schedule (chạy mỗi X thời gian)

```json
{
  "type": "interval",
  "minutes": 30    // Mỗi 30 phút
}

{
  "type": "interval",
  "hours": 2      // Mỗi 2 giờ
}
```

#### Cron Schedule (chạy theo lịch cụ thể)

```json
{
  "type": "cron",
  "hour": "8",
  "minute": "0",
  "day_of_week": "mon-fri"    // 8:00 sáng, thứ 2-6
}

{
  "type": "cron",
  "minute": "*/15"    // Mỗi 15 phút
}
```

### Các Scraper Functions có sẵn

- `scrape_all` - Scrape tất cả nguồn
- `scrape_cafef` - CafeF
- `scrape_vnexpress` - VnExpress
- `scrape_vneconomy` - VnEconomy
- `scrape_vov` - VOV
- `scrape_vietnamnet` - Vietnamnet
- `scrape_dantri` - Dân trí
- `scrape_thanhnien` - Thanh Niên
- `scrape_tuoitre` - Tuổi Trẻ
- `scrape_laodong` - Lao Động
- `scrape_nld` - Người Lao Động
- `scrape_vietstock` - VietStock
- `scrape_antt` - An ninh Thủ đô
- `scrape_cna` - Channel NewsAsia
- `scrape_qdnd` - Quân đội Nhân dân
- `scrape_kinhte` - Kinh tế Ngoại thương
- `scrape_thoibaonganhang` - Thời báo Ngân hàng
- `scrape_taichinhdoanhnghiep` - Tài chính Doanh nghiệp
- `scrape_baochinhphu` - Báo Chính phủ

### Logs

Xem logs tại: `logs/news_scheduler.log`

```bash
tail -f logs/news_scheduler.log    # Xem logs real-time
```

### Bật/Tắt Jobs

Đặt `"enabled": false` trong config để tắt job:

```json
{
  "id": "my_job",
  "enabled": false,
  ...
}
```

## Lưu ý

1. **Rate limiting**: Tool có delay 2-3 giây giữa các request
2. **Duplicate handling**: Dùng UNIQUE constraint trên `title`
3. **Error handling**: Skip bài lỗi và tiếp tục
4. **Encoding**: Hỗ trợ gzip, brotli compression
