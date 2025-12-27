# Hướng dẫn Sentiment Analysis

## ✅ Đã hoàn thành

1. ✓ Tạo file `analyze_sentiment.py`
2. ✓ Thêm methods vào `database/models.py`:
   - `update_sentiment_score()`
   - `update_stock_related()` (bonus)

## 🚀 Cách sử dụng

### 1. Crawl data trước (nếu chưa có)

```bash
python main.py cafef
# Hoặc
python main.py vnexpress
# Hoặc crawl tất cả
python main.py
```

### 2. Chạy sentiment analysis

**Phân tích 50 bài đầu tiên:**
```bash
python analyze_sentiment.py
```

**Phân tích với batch size tùy chỉnh:**
```bash
python analyze_sentiment.py --batch 100
```

**Phân tích chỉ từ một nguồn cụ thể:**
```bash
python analyze_sentiment.py --source cafef.vn
python analyze_sentiment.py --source vnexpress.net
```

**Xem thống kê sentiment:**
```bash
python analyze_sentiment.py --stats
```

**Test với một đoạn text:**
```bash
python analyze_sentiment.py --test "Cổ phiếu VCB tăng mạnh 5% trong phiên hôm nay"
```

## 📊 Kết quả

Sau khi chạy xong, database sẽ được update:

```
sentiment_score: "positive:0.950"   (tin tích cực)
sentiment_score: "negative:0.873"   (tin tiêu cực)
sentiment_score: "neutral:0.654"    (tin trung lập)
```

## 🔍 Kiểm tra kết quả trong database

```sql
-- Xem các bài đã có sentiment
SELECT title, sentiment_score, source
FROM news
WHERE sentiment_score != 'NA'
LIMIT 10;

-- Thống kê theo sentiment
SELECT
    SPLIT_PART(sentiment_score, ':', 1) as sentiment,
    COUNT(*) as count
FROM news
WHERE sentiment_score != 'NA'
GROUP BY SPLIT_PART(sentiment_score, ':', 1);
```

## 📝 Model sử dụng

- **Model**: `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`
- **Hỗ trợ**: Multilingual (bao gồm tiếng Việt)
- **Output**: 3 labels (positive, negative, neutral)

## ⚙️ Tùy chỉnh

Nếu muốn đổi model, sửa trong `analyze_sentiment.py`:

```python
analyzer = SentimentAnalyzer(
    model_name="vinai/phobert-base"  # Hoặc model khác
)
```

## 🎯 Workflow đề xuất

```
1. Crawl data hàng ngày:
   python main.py

2. Sau đó chạy sentiment analysis:
   python analyze_sentiment.py --batch 100

3. Xem thống kê:
   python analyze_sentiment.py --stats
```

## 🐛 Troubleshooting

**Lỗi "No module named 'transformers'":**
```bash
pip install transformers torch
```

**Model download chậm:**
- Model sẽ tự động download lần đầu (~500MB)
- Lưu vào cache: `~/.cache/huggingface/`

**Out of memory:**
- Giảm batch size: `--batch 10`
- Model sẽ xử lý mỗi text tối đa 512 ký tự
