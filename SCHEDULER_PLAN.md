# News Scraper - Scheduler Implementation Plan

## 📋 Tổng quan

Tài liệu này mô tả chi tiết kế hoạch implement hệ thống scheduler tự động cho news-scraper project.

**Yêu cầu:**
- Tần suất: Mỗi giờ
- Môi trường: Windows local
- Sources: Tất cả 5 nguồn (CafeF, VnExpress, VnEconomy, VOV, Vietnamnet)

## 🎯 Mục tiêu

1. Tự động chạy scraper mỗi giờ để thu thập tin tức mới
2. Logging chi tiết để theo dõi quá trình
3. Error handling và recovery
4. Dễ dàng config và điều chỉnh lịch trình
5. Graceful shutdown khi dừng service

## 🏗️ Kiến trúc

```
news-scraper/
├── scheduler.py           # 🆕 Main scheduler file
├── config.py              # ✏️ Thêm scheduler config
├── requirements.txt       # ✏️ Thêm APScheduler
├── logs/                  # 🆕 Folder chứa logs
│   └── scheduler.log      # 🆕 Log file
├── .env                   # ✏️ Thêm scheduler settings
└── README.md              # ✏️ Cập nhật hướng dẫn
```

## 📦 Thư viện sử dụng

### APScheduler v3.10.4
- **Lý do chọn:**
  - Pure Python, không cần service bên ngoài
  - Hỗ trợ nhiều loại lịch trình (interval, cron, date)
  - Persistent jobs (lưu jobs khi restart)
  - Thread-safe, process-safe
  - Tích hợp tốt với Python logging

- **Alternatives đã xem xét:**
  - ❌ Windows Task Scheduler: Khó config từ code
  - ❌ Celery: Quá phức tạp cho use case này, cần Redis/RabbitMQ
  - ❌ Cron: Không có sẵn trên Windows

## 📝 Chi tiết Implementation

### 1. File: `scheduler.py` (MỚI)

**Chức năng chính:**

```python
# Cấu trúc tổng quan
class NewsScraperScheduler:
    def __init__(self):
        - Khởi tạo APScheduler với BackgroundScheduler
        - Setup logging
        - Load config từ .env

    def setup_jobs(self):
        - Thêm job chạy mỗi giờ
        - Có thể config interval từ .env

    def run_scraping_job(self):
        - Wrap hàm scrape_all() từ main.py
        - Try-catch để handle errors
        - Log kết quả (success/fail, số bài crawl được)

    def start(self):
        - Start scheduler
        - Chạy ngay 1 lần khi khởi động (optional)
        - Graceful shutdown handler (Ctrl+C)

    def stop(self):
        - Shutdown scheduler safely
```

**Tính năng:**

1. **Logging nâng cao:**
   ```
   [2025-12-29 10:00:00] INFO - Starting scheduled scraping job...
   [2025-12-29 10:00:05] INFO - Scraping CafeF: 45 articles collected
   [2025-12-29 10:01:30] INFO - Scraping VnExpress: 32 articles collected
   [2025-12-29 10:15:22] INFO - ✓ Job completed: 150 total articles
   [2025-12-29 10:15:22] INFO - Next run: 2025-12-29 11:00:00
   ```

2. **Error handling:**
   - Nếu 1 source fail → skip, tiếp tục sources khác
   - Nếu database fail → fallback to CSV export only
   - Retry mechanism (optional)

3. **Monitoring:**
   - Log file rotation (max 10MB, keep 5 files)
   - Console output cho debugging
   - Job execution statistics

4. **Graceful shutdown:**
   - Catch Ctrl+C signal
   - Đợi job hiện tại hoàn thành
   - Cleanup resources

### 2. File: `config.py` (CẬP NHẬT)

**Thêm config cho scheduler:**

```python
class Config:
    # ... existing configs ...

    # Scheduler settings
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    SCHEDULER_INTERVAL_HOURS = int(os.getenv("SCHEDULER_INTERVAL_HOURS", "1"))
    SCHEDULER_RUN_ON_STARTUP = os.getenv("SCHEDULER_RUN_ON_STARTUP", "false").lower() == "true"

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/scheduler.log")
```

### 3. File: `requirements.txt` (CẬP NHẬT)

**Thêm dependencies:**

```
APScheduler==3.10.4
```

### 4. File: `.env` (CẬP NHẬT)

**Thêm settings:**

```bash
# Scheduler Settings
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_HOURS=1
SCHEDULER_RUN_ON_STARTUP=false  # true = chạy ngay khi start scheduler

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/scheduler.log
```

### 5. File: `README.md` (CẬP NHẬT)

**Thêm section:**

- Hướng dẫn sử dụng scheduler
- Cách config lịch trình
- Troubleshooting common issues

## 🚀 Usage Flow

### Cách sử dụng:

1. **Chạy scraper thủ công (như hiện tại):**
   ```bash
   python main.py
   ```

2. **Chạy scheduler tự động:**
   ```bash
   python scheduler.py
   ```

3. **Chạy scheduler như Windows Service (nâng cao):**
   - Sử dụng `NSSM` (Non-Sucking Service Manager)
   - Hoặc `Task Scheduler` để chạy khi Windows khởi động

### Lịch trình mặc định:

- **Mỗi giờ:** 00:00, 01:00, 02:00, ..., 23:00
- **Tùy chỉnh:** Thay đổi `SCHEDULER_INTERVAL_HOURS` trong `.env`

## 📊 Logging Strategy

### Log levels:

- **INFO:** Normal operations (job started, completed, articles count)
- **WARNING:** Recoverable errors (1 source failed, fallback to CSV)
- **ERROR:** Serious errors (database connection failed, all sources failed)
- **DEBUG:** Detailed info cho troubleshooting (chỉ dùng khi cần)

### Log rotation:

- Max file size: 10MB
- Keep last 5 files
- Format: `scheduler.log`, `scheduler.log.1`, `scheduler.log.2`, ...

## 🛡️ Error Handling Strategy

### Level 1: Source-level errors
```python
try:
    articles = scrape_cafef()
except Exception as e:
    logger.warning(f"CafeF scraping failed: {e}")
    # Continue với sources khác
```

### Level 2: Database errors
```python
try:
    db.insert_news(articles)
except Exception as e:
    logger.error(f"Database insert failed: {e}")
    # Fallback to CSV export
    export_to_csv(articles)
```

### Level 3: Scheduler errors
```python
try:
    scheduler.start()
except KeyboardInterrupt:
    logger.info("Scheduler stopped by user")
    scheduler.shutdown()
except Exception as e:
    logger.error(f"Scheduler crashed: {e}")
    # Email notification (optional)
```

## 🔄 Job Execution Flow

```
[Scheduler starts]
    ↓
[Wait until next scheduled time]
    ↓
[10:00:00] Job triggered
    ↓
[10:00:01] Log: "Starting scraping job..."
    ↓
[10:00:05] Scrape CafeF → 45 articles
    ↓
[10:02:10] Scrape VnExpress → 32 articles
    ↓
[10:04:30] Scrape VnEconomy → 28 articles
    ↓
[10:07:15] Scrape VOV → 25 articles
    ↓
[10:10:50] Scrape Vietnamnet → 20 articles
    ↓
[10:11:00] Save to database (150 articles)
    ↓
[10:11:05] Export to CSV
    ↓
[10:11:10] Log: "✓ Job completed: 150 articles"
    ↓
[10:11:10] Log: "Next run: 11:00:00"
    ↓
[Wait until 11:00:00]
```

## 📈 Advanced Features (Optional - Có thể thêm sau)

### 1. Email notifications
- Gửi email khi job fail
- Daily summary report

### 2. Web dashboard
- Flask web UI để xem job status
- Real-time logs
- Manual trigger button

### 3. Persistent job store
- Lưu job state vào SQLite
- Recovery sau khi restart

### 4. Multiple schedules
- Một số sources chạy frequent hơn
- VD: CafeF mỗi 30 phút, sources khác mỗi 2 giờ

### 5. Webhook integration
- POST kết quả đến API endpoint
- Integration với Telegram bot

## 🧪 Testing Plan

### 1. Unit tests
- Test scheduler initialization
- Test job execution
- Test error handling

### 2. Integration tests
- Test với database connection
- Test CSV export fallback

### 3. Manual tests
- Chạy scheduler 24h liên tục
- Test graceful shutdown
- Test recovery sau crash

## 📋 Implementation Checklist

### Phase 1: Core functionality
- [ ] Tạo `scheduler.py` với APScheduler
- [ ] Setup logging system
- [ ] Implement job execution logic
- [ ] Error handling và recovery
- [ ] Graceful shutdown

### Phase 2: Configuration
- [ ] Update `config.py` với scheduler settings
- [ ] Update `.env.example` với scheduler vars
- [ ] Update `requirements.txt`

### Phase 3: Documentation
- [ ] Update `README.md` với scheduler usage
- [ ] Thêm troubleshooting guide
- [ ] Tạo `SCHEDULER.md` (chi tiết hơn)

### Phase 4: Testing
- [ ] Test manual execution
- [ ] Test scheduled execution
- [ ] Test error scenarios
- [ ] Test log rotation

### Phase 5: Deployment
- [ ] Hướng dẫn chạy như Windows Service
- [ ] Auto-start on Windows boot (optional)

## 🎯 Success Criteria

1. ✅ Scheduler chạy ổn định 24/7
2. ✅ Scrape data mỗi giờ thành công
3. ✅ Error recovery tự động
4. ✅ Logs đầy đủ, dễ debug
5. ✅ Resource usage hợp lý (<100MB RAM)
6. ✅ Không miss scheduled runs

## ⚠️ Potential Issues & Solutions

### Issue 1: Memory leak sau nhiều giờ chạy
**Solution:**
- Cleanup session objects sau mỗi job
- Monitor memory usage trong logs

### Issue 2: Network timeout
**Solution:**
- Tăng timeout trong config
- Retry mechanism với exponential backoff

### Issue 3: Database connection pool exhausted
**Solution:**
- Close connections properly
- Use connection pooling

### Issue 4: Disk space đầy (do logs)
**Solution:**
- Log rotation
- Compress old logs
- Auto cleanup logs > 30 days

## 📞 Support & Maintenance

### Monitoring checklist:
- [ ] Check logs daily cho errors
- [ ] Monitor disk space (logs folder)
- [ ] Check database size growth
- [ ] Verify data quality (duplicate check)

### Regular maintenance:
- [ ] Weekly: Review error logs
- [ ] Monthly: Clean old CSV exports
- [ ] Monthly: Vacuum database

---

## 🚦 Next Steps

**Nếu bạn approve plan này, tôi sẽ:**

1. Tạo `scheduler.py` với đầy đủ tính năng
2. Update `config.py`, `requirements.txt`
3. Tạo folder `logs/`
4. Update `README.md` với hướng dẫn
5. Test thử chạy 1 vòng để verify

**Timeline ước tính:**
- Implementation: ~30 phút
- Testing: ~15 phút
- Documentation: ~10 phút

**Bạn có muốn điều chỉnh gì trong plan này không?**
