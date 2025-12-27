"""
Sentiment Analysis - Phân tích cảm xúc cho bài báo
Sử dụng Hugging Face transformers
"""

from transformers import pipeline
from database.models import db, News
from sqlalchemy import and_
import sys


class SentimentAnalyzer:
    """Phân tích sentiment cho bài báo"""

    def __init__(self, model_name: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual"):
        """
        Khởi tạo sentiment analyzer

        Args:
            model_name: Tên model từ Hugging Face
        """
        print(f"Loading sentiment model: {model_name}... - analyze_sentiment.py:22")
        try:
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                top_k=None  # Return all labels with scores
            )
            print("✓ Model loaded successfully! - analyze_sentiment.py:29")
        except Exception as e:
            print(f"✗ Error loading model: {e} - analyze_sentiment.py:31")
            sys.exit(1)

    def analyze(self, text: str) -> str:
        """
        Phân tích sentiment của text

        Args:
            text: Text cần phân tích (title + content)

        Returns:
            String format: "label:score" (e.g., "positive:0.95")
        """
        if not text or not text.strip():
            return "NA"

        try:
            # Limit text length (models có max token limit ~512)
            text_truncated = text[:512]

            # Run sentiment analysis
            results = self.pipeline(text_truncated)[0]

            # Lấy label có score cao nhất
            best_result = max(results, key=lambda x: x['score'])
            label = best_result['label'].lower()  # positive/negative/neutral
            score = best_result['score']

            return f"{label}:{score:.3f}"

        except Exception as e:
            print(f"⚠ Error analyzing text: {e} - analyze_sentiment.py:62")
            return "NA"


def update_sentiment_scores(batch_size: int = 50, source: str = None, all_records: bool = False):
    """
    Update sentiment scores cho các bài báo chưa có score
    Tự động loop xử lý từng batch cho đến khi hết

    Args:
        batch_size: Số lượng bài phân tích mỗi batch (mặc định 50)
        source: Chỉ phân tích từ nguồn cụ thể (cafef.vn, vnexpress.net, ...)
        all_records: Nếu True, xử lý trong 1 batch duy nhất (không loop)
    """
    print("="*60)
    print("🤖 SENTIMENT ANALYSIS")
    if all_records:
        print("Mode: ALL RECORDS - Single batch (không giới hạn)")
    else:
        print(f"Mode: AUTO LOOP - Mỗi batch {batch_size} bài, tự động loop đến khi hết")
    print("="*60)

    # Initialize analyzer (chỉ 1 lần)
    analyzer = SentimentAnalyzer()

    # Thống kê tổng
    total_success = 0
    total_errors = 0
    batch_number = 0

    # Loop cho đến khi không còn bài nào
    while True:
        batch_number += 1

        # Get database session mới cho mỗi batch
        session = db.get_session()

        try:
            # Query bài chưa có sentiment score
            query = session.query(News).filter(
                and_(
                    News.sentiment_score == "NA",
                    News.content != None,
                    News.content != ""
                )
            )

            # Filter by source nếu có
            if source:
                query = query.filter(News.source == source)

            # Limit batch size
            if not all_records:
                news_items = query.limit(batch_size).all()
            else:
                news_items = query.all()

            # Nếu không còn bài → break loop
            if not news_items:
                if batch_number == 1:
                    print("\n✓ No articles to analyze. All done!")
                else:
                    print(f"\n✓ All batches completed!")
                break

            # Hiển thị thông tin batch
            if not all_records:
                print(f"\n{'='*60}")
                print(f"📦 BATCH #{batch_number} - Processing {len(news_items)} articles")
                print(f"{'='*60}")
            else:
                print(f"\nProcessing {len(news_items)} articles...")
            print("-" * 60)

            success_count = 0
            error_count = 0

            for i, news in enumerate(news_items, 1):
                try:
                    # Combine title + content preview for analysis
                    text = f"{news.title}. {news.content[:300]}"

                    # Analyze sentiment
                    sentiment = analyzer.analyze(text)

                    # Update database
                    news.sentiment_score = sentiment
                    session.commit()

                    success_count += 1
                    print(f"[{i}/{len(news_items)}] ✓ {sentiment:15} | {news.title[:50]}...")

                except Exception as e:
                    error_count += 1
                    print(f"[{i}/{len(news_items)}] ✗ Error: {e}")
                    session.rollback()

            # Cập nhật thống kê tổng
            total_success += success_count
            total_errors += error_count

            # Hiển thị summary của batch
            print("-" * 60)
            print(f"Batch #{batch_number} Summary:")
            print(f"  Success: {success_count}")
            print(f"  Errors:  {error_count}")
            print(f"  Total:   {len(news_items)}")

            # Nếu chạy all_records, chỉ chạy 1 lần rồi break
            if all_records:
                break

        except Exception as e:
            print(f"\n❌ Fatal error in batch #{batch_number}: {e}")
            session.rollback()
            break
        finally:
            session.close()

    # Hiển thị tổng kết cuối cùng
    if batch_number > 1 or (batch_number == 1 and total_success > 0):
        print(f"\n{'='*60}")
        print(f"📊 FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"  Total batches:  {batch_number}")
        print(f"  Total success:  {total_success}")
        print(f"  Total errors:   {total_errors}")
        print(f"  Grand total:    {total_success + total_errors}")
        print(f"{'='*60}")


def analyze_single_text(text: str):
    """
    Test sentiment analysis với một đoạn text

    Args:
        text: Text cần phân tích
    """
    analyzer = SentimentAnalyzer()
    sentiment = analyzer.analyze(text)
    print(f"\nText: {text[:100]}... - analyze_sentiment.py:161")
    print(f"Sentiment: {sentiment} - analyze_sentiment.py:162")


def show_statistics():
    """Hiển thị thống kê sentiment scores trong database"""
    session = db.get_session()

    try:
        from sqlalchemy import func

        # Count by sentiment
        results = session.query(
            News.sentiment_score,
            func.count(News.id)
        ).group_by(News.sentiment_score).all()

        print("\n📊 Sentiment Statistics: - analyze_sentiment.py:178")
        print("" * 40)
        for sentiment, count in results:
            # Parse sentiment (e.g., "positive:0.95")
            label = sentiment.split(':')[0] if ':' in sentiment else sentiment
            print(f"{label:15} : {count:5} articles - analyze_sentiment.py:183")
        print("" * 40)

    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Sentiment Analysis for News Articles')
    parser.add_argument('--batch', type=int, default=50, help='Batch size (default: 50, ignored if --all is set)')
    parser.add_argument('--source', type=str, help='Filter by source (e.g., cafef.vn)')
    parser.add_argument('--all', action='store_true', help='Process ALL records (no limit)')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    parser.add_argument('--test', type=str, help='Test with a single text')

    args = parser.parse_args()

    if args.stats:
        show_statistics()
    elif args.test:
        analyze_single_text(args.test)
    else:
        update_sentiment_scores(batch_size=args.batch, source=args.source, all_records=args.all)
