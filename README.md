# Multi-Source News Scraper

Tool crawl tin tức từ **25 nguồn báo** Việt Nam và quốc tế, lưu vào PostgreSQL với khả năng tự động lập lịch.

## Supported Sources (25 nguồn)

| Source | URL | Status |
|--------|-----|--------|
| CafeF | cafef.vn | ✅ |
| CafeLand | cafeland.vn | ✅ |
| VnExpress | vnexpress.net | ✅ |
| VnEconomy | vneconomy.vn | ✅ |
| VOV | vov.vn | ✅ |
| Vietnamnet | vietnamnet.vn | ✅ |
| Dân trí | dantri.com.vn | ✅ |
| Thanh Niên | thanhnien.vn | ✅ |
| Tuổi Trẻ | tuoitre.vn | ✅ |
| Lao Động | laodong.vn | ✅ |
| Người Lao Động | nld.com.vn | ✅ |
| VietStock | vietstock.vn | ✅ |
| An ninh Thủ đô | anninhthudo.vn | ✅ |
| Channel NewsAsia | channelnewsasia.com | ✅ |
| Quân đội Nhân dân | qdnd.vn | ✅ |
| Kinh tế Ngoại thương | kinhtengaithuong.vn | ✅ |
| Thời báo Ngân hàng | thoibaonganhang.vn | ✅ |
| Tài chính Doanh nghiệp | taichinhdoanhnghiep.net.vn | ✅ |
| Báo Chính phủ | baochinhphu.vn | ✅ |
| Tin nhanh Chứng khoán | tinnhanhchungkhoan.vn | ✅ |
| Xây dựng Chính sách | chinhphu.vn | ✅ |
| Vietnam Finance | vietnamfinance.vn | ✅ |
| Coin68 | coin68.com | ✅ |
| Người Quan Sát | nguoiquansat.vn | ✅ |
| Thời báo Tài chính VN | thoibaotaichinhvietnam.vn | ✅ |

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
├── main.py                      # Entry point - 25 scraper functions
├── scheduler.py                 # ⭐ Scheduler tự động lập lịch
├── scheduler_config.json        # ⭐ Cấu hình 26 jobs
├── config.py                    # Configuration
├── requirements.txt             # Dependencies
├── checklist.md                 # Development checklist
├── README.md                    # Documentation
│
├── database/
│   ├── __init__.py
│   ├── models.py                # SQLAlchemy models (News table)
│   └── news.db                  # SQLite database (nếu dùng SQLite)
│
├── scrapers/
│   ├── __init__.py
│   ├── base.py                  # Base scraper class
│   │
│   ├── html/                    # HTML scrapers (18 sources)
│   │   ├── cafef.py
│   │   ├── cafeland.py
│   │   ├── vnexpress.py
│   │   ├── vietnamnet.py
│   │   ├── vov.py
│   │   ├── laodong.py
│   │   ├── nld.py
│   │   ├── kinhtengaithuong.py
│   │   ├── thoibaonganhang.py
│   │   ├── taichinhdoanhnghiep.py
│   │   ├── baochinhphu.py
│   │   ├── tinnhanhchungkhoan.py
│   │   ├── xaydungchinhsach.py
│   │   ├── vietnamfinance.py
│   │   ├── coin68.py
│   │   ├── nguoiquansat.py
│   │   ├── thoibaotaichinh.py
│   │   └── __init__.py
│   │
│   ├── rss/                     # RSS scrapers (7 sources)
│   │   ├── dantri.py
│   │   ├── thanhnien.py
│   │   ├── tuoitre.py
│   │   ├── vneconomy.py
│   │   ├── antt.py
│   │   ├── cna.py
│   │   ├── qdnd.py
│   │   └── __init__.py
│   │
│   └── selenium/                # Selenium scrapers (1 source)
│       ├── vietstock.py
│       └── __init__.py
│
├── utils/
│   ├── __init__.py
│   └── exporters.py             # CSV & JSON exporters
│
├── logs/                        # Scheduler logs
│   └── news_scheduler.log
│
└── exports/                     # Output CSV files
```



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
      "id": "scrape_all_",
      "name": "Scrape tất cả nguồn tin",
      "function": "scrape_all",
      "enabled": true,
      "schedule": {
        "type": "interval",
        "minutes": 30
      },
      "description": "Chạy scrape_all() mỗi 30 phút để thu thập tin từ tất cả 25 nguồn"
    }
  ],
  "timezone": "Asia/Ho_Chi_Minh",
  "log_file": "logs/news_scheduler.log",
  "log_level": "INFO",
  "run_on_startup": true
}
```

**Lưu ý:** File config thực tế có 26 jobs (1 `scrape_all` + 25 scrapers riêng lẻ). Mặc định chỉ `scrape_all` được bật.

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

### Các Scraper Functions có sẵn (25 functions)

- `scrape_all` - Scrape tất cả nguồn (26 in 1)
- `scrape_cafef` - CafeF
- `scrape_cafeland` - CafeLand
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
- `scrape_tinnhanhchungkhoan` - Tin nhanh Chứng khoán
- `scrape_xaydungchinhsach` - Xây dựng Chính sách
- `scrape_vietnamfinance` - Vietnam Finance
- `scrape_coin68` - Coin68
- `scrape_nguoiquansat` - Người Quan Sát
- `scrape_thoibaotaichinh` - Thời báo Tài chính VN

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

## 🤖 Sentiment Analysis - Phân tích cảm xúc bài báo

Tool tự động phân tích và cập nhật sentiment score cho các bài báo trong database sử dụng Hugging Face transformers.

### Cài đặt

```bash
pip install transformers torch
```

### Sử dụng

#### 1. Phân tích tất cả bài chưa có sentiment (Auto Loop)

```bash
python analyze_sentiment.py
```

Mặc định xử lý **50 bài/batch**, tự động loop cho đến khi hết.

#### 2. Tùy chỉnh batch size

```bash
python analyze_sentiment.py --batch 100    # 100 bài/batch
```

#### 3. Phân tích toàn bộ trong 1 batch duy nhất

```bash
python analyze_sentiment.py --all
```

#### 4. Chỉ phân tích 1 nguồn cụ thể

```bash
python analyze_sentiment.py --source cafef.vn
python analyze_sentiment.py --source vnexpress.net --batch 30
```

#### 5. Test với text riêng lẻ

```bash
python analyze_sentiment.py --test "Chứng khoán tăng mạnh trong phiên hôm nay"
```

#### 6. Xem thống kê sentiment

```bash
python analyze_sentiment.py --stats
```

### Output Format

Sentiment score được lưu ở format: `label:score`

Ví dụ:
- `positive:0.952` - Tích cực (95.2%)
- `negative:0.834` - Tiêu cực (83.4%)
- `neutral:0.678` - Trung lập (67.8%)

### Model sử dụng

**cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual**
- Multilingual model (hỗ trợ Tiếng Việt)
- 3 labels: positive, negative, neutral
- Hugging Face transformers

### Command Line Arguments

| Argument | Mô tả | Default |
|----------|-------|---------|
| `--batch N` | Số bài/batch | 50 |
| `--source SOURCE` | Lọc theo nguồn (cafef.vn, vnexpress.net...) | None |
| `--all` | Xử lý tất cả không giới hạn batch | False |
| `--stats` | Hiển thị thống kê sentiment | - |
| `--test TEXT` | Test với text riêng lẻ | - |

### Ví dụ Output

```
📦 BATCH #1 - Processing 50 articles
------------------------------------------------------------
[1/50] ✓ positive:0.892  | Chứng khoán tăng điểm trong phiên đầu tuần...
[2/50] ✓ negative:0.745  | Giá vàng giảm mạnh do áp lực bán...
[3/50] ✓ neutral:0.623   | Ngân hàng Nhà nước công bố lãi suất mới...
...
------------------------------------------------------------
Batch #1 Summary:
  Success: 48
  Errors:  2
  Total:   50
```

## Lưu ý

1. **Rate limiting**: Tool có delay 2-3 giây giữa các request
2. **Duplicate handling**: Dùng UNIQUE constraint trên `title`
3. **Error handling**: Skip bài lỗi và tiếp tục
4. **Encoding**: Hỗ trợ gzip, brotli compression
5. **Sentiment Analysis**: Model download ~400MB lần đầu chạy
