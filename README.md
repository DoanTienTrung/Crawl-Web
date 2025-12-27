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
python main.py vneconomy    # Chỉ VnEconomy
python main.py vov          # Chỉ VOV
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

## Lưu ý

1. **Rate limiting**: Tool có delay 2-3 giây giữa các request
2. **Duplicate handling**: Dùng UNIQUE constraint trên `title`
3. **Error handling**: Skip bài lỗi và tiếp tục
4. **Encoding**: Hỗ trợ gzip, brotli compression
