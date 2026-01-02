# Hướng dẫn sử dụng Scheduler

## 📋 Mục lục

1. [Cài đặt](#cài-đặt)
2. [Cấu hình](#cấu-hình)
3. [Chạy Scheduler](#chạy-scheduler)
4. [Các loại Schedule](#các-loại-schedule)
5. [Ví dụ Config](#ví-dụ-config)
6. [Troubleshooting](#troubleshooting)

---

## Cài đặt

### Bước 1: Install APScheduler

```bash
pip install -r requirements.txt
```

Hoặc cài riêng:

```bash
pip install APScheduler==3.10.4
```

### Bước 2: Verify installation

```bash
python -c "import apscheduler; print(apscheduler.__version__)"
```

Expected output: `3.10.4`

---

## Cấu hình

### File cấu hình: `scheduler_config.json`

Đây là file JSON chứa tất cả cấu hình cho scheduler.

#### Cấu trúc cơ bản:

```json
{
  "database": {
    "user": "postgres",
    "password": "your_password",
    "database": "news_db",
    "host": "localhost",
    "port": 5432
  },
  "jobs": [...],
  "timezone": "Asia/Ho_Chi_Minh",
  "log_file": "logs/news_scheduler.log",
  "log_level": "INFO",
  "run_on_startup": false
}
```

#### Các tham số:

| Tham số | Mô tả | Mặc định |
|---------|-------|----------|
| `database` | Cấu hình database (tùy chọn) | - |
| `jobs` | Danh sách các jobs | `[]` |
| `timezone` | Múi giờ | `Asia/Ho_Chi_Minh` |
| `log_file` | Đường dẫn file log | `logs/news_scheduler.log` |
| `log_level` | Mức độ log (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `run_on_startup` | Chạy ngay khi start scheduler | `false` |

---

## Chạy Scheduler

### Chạy cơ bản:

```bash
python scheduler.py
```

### Output mẫu:

```
============================================================
📰 News Scraper Scheduler
============================================================

✓ Loaded config from: scheduler_config.json
[2026-01-02 10:00:00] INFO - ============================================================
[2026-01-02 10:00:00] INFO - 📰 News Scraper Scheduler Initialized
[2026-01-02 10:00:00] INFO - ============================================================
[2026-01-02 10:00:00] INFO - ⏰ Timezone: Asia/Ho_Chi_Minh
[2026-01-02 10:00:00] INFO - ✓ Added job: Scrape tất cả nguồn tin mỗi giờ - Chạy scrape_all() mỗi 1 giờ
[2026-01-02 10:00:00] INFO - ⏭️  Skipped (disabled): Scrape CafeF mỗi 30 phút
[2026-01-02 10:00:00] INFO -
📋 Summary: 1 jobs enabled, 4 jobs disabled
[2026-01-02 10:00:00] INFO -
🚀 Scheduler started successfully!
[2026-01-02 10:00:00] INFO - ⏰ Timezone: Asia/Ho_Chi_Minh
[2026-01-02 10:00:00] INFO - 📋 Total active jobs: 1

[2026-01-02 10:00:00] INFO -   🕐 Scrape tất cả nguồn tin mỗi giờ
[2026-01-02 10:00:00] INFO -      Next run: 2026-01-02 11:00:00
[2026-01-02 10:00:00] INFO -
============================================================
[2026-01-02 10:00:00] INFO - Press Ctrl+C to stop scheduler
[2026-01-02 10:00:00] INFO - ============================================================
```

### Dừng scheduler:

Nhấn `Ctrl+C`:

```
⏸️  Shutting down scheduler...
⏳ Waiting for running jobs to complete...
✅ Scheduler stopped gracefully
```

---

## Các loại Schedule

### 1. Interval Schedule (Lặp lại theo khoảng thời gian)

Chạy job mỗi X giây/phút/giờ/ngày.

#### Ví dụ:

**Mỗi 30 phút:**
```json
{
  "schedule": {
    "type": "interval",
    "minutes": 30
  }
}
```

**Mỗi 2 giờ:**
```json
{
  "schedule": {
    "type": "interval",
    "hours": 2
  }
}
```

**Mỗi 1 ngày:**
```json
{
  "schedule": {
    "type": "interval",
    "days": 1
  }
}
```

**Mỗi 90 giây:**
```json
{
  "schedule": {
    "type": "interval",
    "seconds": 90
  }
}
```

#### Tham số interval:

| Tham số | Đơn vị | Ví dụ |
|---------|--------|-------|
| `seconds` | Giây | `30` = mỗi 30 giây |
| `minutes` | Phút | `15` = mỗi 15 phút |
| `hours` | Giờ | `2` = mỗi 2 giờ |
| `days` | Ngày | `1` = mỗi 1 ngày |

### 2. Cron Schedule (Lịch cụ thể)

Chạy job theo lịch như cron.

#### Ví dụ:

**Chạy lúc 8:00 sáng mỗi ngày:**
```json
{
  "schedule": {
    "type": "cron",
    "hour": "8",
    "minute": "0"
  }
}
```

**Chạy lúc 8:00 sáng các ngày trong tuần (thứ 2-6):**
```json
{
  "schedule": {
    "type": "cron",
    "hour": "8",
    "minute": "0",
    "day_of_week": "mon-fri"
  }
}
```

**Chạy mỗi 15 phút:**
```json
{
  "schedule": {
    "type": "cron",
    "minute": "*/15"
  }
}
```

**Chạy lúc 9h, 12h, 15h mỗi ngày:**
```json
{
  "schedule": {
    "type": "cron",
    "hour": "9,12,15",
    "minute": "0"
  }
}
```

**Chạy từ 9h-17h, mỗi giờ vào phút thứ 30:**
```json
{
  "schedule": {
    "type": "cron",
    "hour": "9-17",
    "minute": "30"
  }
}
```

**Chạy lúc 0h chủ nhật hàng tuần:**
```json
{
  "schedule": {
    "type": "cron",
    "hour": "0",
    "minute": "0",
    "day_of_week": "sun"
  }
}
```

#### Tham số cron:

| Tham số | Giá trị | Ví dụ |
|---------|---------|-------|
| `minute` | 0-59 hoặc `*/X` | `0`, `30`, `*/15` |
| `hour` | 0-23 | `8`, `9-17`, `9,12,15` |
| `day` | 1-31 | `1`, `15`, `1,15` |
| `month` | 1-12 | `1`, `6-8` |
| `day_of_week` | mon-sun | `mon-fri`, `sat,sun` |

---

## Ví dụ Config

### Config 1: Scrape mỗi giờ (mặc định)

```json
{
  "jobs": [
    {
      "id": "scrape_all_hourly",
      "name": "Scrape tất cả mỗi giờ",
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

### Config 2: Multiple jobs với lịch khác nhau

```json
{
  "jobs": [
    {
      "id": "scrape_all_morning",
      "name": "Scrape tất cả buổi sáng",
      "function": "scrape_all",
      "enabled": true,
      "schedule": {
        "type": "cron",
        "hour": "8",
        "minute": "0",
        "day_of_week": "mon-fri"
      },
      "description": "8:00 sáng thứ 2-6"
    },
    {
      "id": "scrape_cafef_frequent",
      "name": "Scrape CafeF thường xuyên",
      "function": "scrape_cafef",
      "enabled": true,
      "schedule": {
        "type": "interval",
        "minutes": 30
      },
      "description": "Mỗi 30 phút"
    },
    {
      "id": "scrape_vietstock_trading_hours",
      "name": "Scrape VietStock giờ giao dịch",
      "function": "scrape_vietstock",
      "enabled": true,
      "schedule": {
        "type": "cron",
        "hour": "9-15",
        "minute": "0",
        "day_of_week": "mon-fri"
      },
      "description": "Mỗi giờ từ 9h-15h, thứ 2-6"
    }
  ],
  "timezone": "Asia/Ho_Chi_Minh",
  "log_file": "logs/news_scheduler.log",
  "log_level": "INFO"
}
```

### Config 3: Test mode (chạy mỗi 2 phút)

Dùng để test nhanh:

```json
{
  "jobs": [
    {
      "id": "test_cafef",
      "name": "Test CafeF",
      "function": "scrape_cafef",
      "enabled": true,
      "schedule": {
        "type": "interval",
        "minutes": 2
      },
      "description": "Test - Chạy mỗi 2 phút"
    }
  ],
  "timezone": "Asia/Ho_Chi_Minh",
  "log_file": "logs/news_scheduler.log",
  "log_level": "DEBUG",
  "run_on_startup": true
}
```

---

## Các Scraper Functions

Danh sách đầy đủ các function bạn có thể dùng trong config:

| Function Name | Mô tả |
|---------------|-------|
| `scrape_all` | Scrape tất cả 19 nguồn tin |
| `scrape_cafef` | CafeF.vn |
| `scrape_cafeland` | Cafeland.vn |
| `scrape_vnexpress` | VnExpress.net |
| `scrape_vneconomy` | VnEconomy.vn |
| `scrape_vov` | VOV.vn |
| `scrape_vietnamnet` | Vietnamnet.vn |
| `scrape_dantri` | Dantri.com.vn |
| `scrape_thanhnien` | Thanhnien.vn |
| `scrape_tuoitre` | Tuoitre.vn |
| `scrape_laodong` | Laodong.vn |
| `scrape_nld` | NLD.com.vn |
| `scrape_vietstock` | VietStock.vn |
| `scrape_antt` | ANTT.vn |
| `scrape_cna` | Channel NewsAsia |
| `scrape_qdnd` | Quân đội Nhân dân |
| `scrape_kinhte` | Kinh tế Ngoại thương |
| `scrape_thoibaonganhang` | Thời báo Ngân hàng |
| `scrape_taichinhdoanhnghiep` | Tài chính Doanh nghiệp |
| `scrape_baochinhphu` | Báo Chính phủ |

---

## Troubleshooting

### Lỗi: "Config file not found"

```
❌ Config file not found: scheduler_config.json
```

**Giải pháp:** Đảm bảo file `scheduler_config.json` nằm cùng folder với `scheduler.py`

### Lỗi: "Invalid JSON in config file"

```
❌ Invalid JSON in config file: ...
```

**Giải pháp:**
- Kiểm tra syntax JSON (dùng JSONLint.com)
- Đảm bảo không có dấu phẩy thừa
- Đảm bảo dùng double quotes `"` chứ không phải single quotes `'`

### Lỗi: "Unknown function: xyz"

```
❌ Unknown function: xyz for job abc
```

**Giải pháp:** Kiểm tra tên function trong config có khớp với danh sách functions ở trên không.

### Job không chạy đúng giờ

**Nguyên nhân:** Timezone sai

**Giải pháp:** Kiểm tra timezone trong config:

```json
{
  "timezone": "Asia/Ho_Chi_Minh"
}
```

### Logs không được ghi

**Nguyên nhân:** Folder `logs/` chưa tồn tại

**Giải pháp:**

```bash
mkdir logs
```

### Job bị skip

```
⏭️  Skipped (disabled): Job name
```

**Nguyên nhân:** Job có `"enabled": false`

**Giải pháp:** Đổi thành `"enabled": true`

---

## Xem Logs

### Xem logs real-time:

**Linux/Mac:**
```bash
tail -f logs/news_scheduler.log
```

**Windows PowerShell:**
```powershell
Get-Content logs\news_scheduler.log -Wait -Tail 50
```

### Xem logs cũ:

```bash
cat logs/news_scheduler.log
```

### Log format:

```
[2026-01-02 10:00:00] INFO - Message
[2026-01-02 10:00:01] WARNING - Warning message
[2026-01-02 10:00:02] ERROR - Error message
```

---

## Tips & Best Practices

### 1. Test trước khi deploy

Dùng config với interval ngắn (2-5 phút) để test:

```json
{
  "schedule": {
    "type": "interval",
    "minutes": 2
  }
}
```

### 2. Không scrape quá thường xuyên

Tránh bị block IP:
- Scrape tất cả sources: mỗi 1-2 giờ
- Scrape từng source: mỗi 15-30 phút

### 3. Sử dụng log level phù hợp

- **DEBUG**: Khi đang debug, test
- **INFO**: Sử dụng hàng ngày
- **WARNING**: Production, chỉ log khi có vấn đề
- **ERROR**: Chỉ log errors

### 4. Monitor disk space

Logs có thể chiếm nhiều dung lượng. File được auto-rotate khi đạt 10MB.

### 5. Backup config

```bash
cp scheduler_config.json scheduler_config.json.backup
```

---

## Chạy Scheduler như Windows Service (Nâng cao)

Để scheduler chạy khi Windows khởi động:

### Sử dụng NSSM (Non-Sucking Service Manager)

1. Download NSSM: https://nssm.cc/download
2. Cài đặt service:

```cmd
nssm install NewsScheduler "C:\path\to\python.exe" "C:\path\to\news-scraper\scheduler.py"
```

3. Start service:

```cmd
nssm start NewsScheduler
```

### Hoặc dùng Task Scheduler

1. Mở Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start a program
   - Program: `python.exe`
   - Arguments: `C:\path\to\news-scraper\scheduler.py`
   - Start in: `C:\path\to\news-scraper`

---

Chúc bạn sử dụng scheduler hiệu quả! 🚀
