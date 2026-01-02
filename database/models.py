from sqlalchemy import create_engine, Column, String, Text, BigInteger, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
import sys
sys.path.append('..')
from config import config

Base = declarative_base()


class News(Base):
    """
    Model đại diện cho bảng news theo cấu trúc yêu cầu:
    
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
    )
    """
    __tablename__ = 'news'
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    
    # Thời gian đăng bài (Unix timestamp - bigint)
    published_at = Column(BigInteger, nullable=True)
    
    # Tiêu đề - NOT NULL, UNIQUE
    title = Column(Text, nullable=False, unique=True)
    
    # Link bài báo
    link = Column(Text, nullable=True)
    
    # Nội dung
    content = Column(Text, nullable=True)
    
    # Nguồn (cafef.vn, vnexpress.net, vneconomy.vn, ...)
    source = Column(Text, nullable=True)
    
    # Mã chứng khoán liên quan
    stock_related = Column(Text, nullable=True, default="NA")
    
    # Điểm sentiment
    sentiment_score = Column(Text, nullable=True, default="NA")
    
    # Đã push lên server chưa
    server_pushed = Column(Boolean, default=False)
    
    # Thời gian tạo record
    created_at = Column(Text, nullable=True, server_default=text("now()"))
    
    # Category/Chuyên mục
    category = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title[:50]}...')>"
    
    def to_dict(self):
        return {
            'id': str(self.id) if self.id else None,
            'published_at': self.published_at,
            'title': self.title,
            'link': self.link,
            'content': self.content,
            'source': self.source,
            'stock_related': self.stock_related,
            'sentiment_score': self.sentiment_score,
            'server_pushed': self.server_pushed,
            'created_at': self.created_at,
            'category': self.category,
        }


class Database:
    """Database connection và operations"""
    
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL, echo=False)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Tạo tất cả các tables"""
        Base.metadata.create_all(self.engine)
        print("✓ Database tables created successfully! - models.py:98")
    
    def get_session(self):
        """Lấy database session"""
        return self.Session()
    
    def insert_news(self, news_data: tuple) -> bool:
        """
        Insert một bài báo vào database.
        Tương tự hàm insert_news trong Rust.
        
        Args:
            news_data: tuple gồm (published_at, title, link, content, source, stock_related, sentiment_score, server_pushed)
        
        Returns:
            True nếu insert thành công, False nếu đã tồn tại hoặc lỗi
        """
        session = self.get_session()
        try:
            published_at, title, link, content, source, stock_related, sentiment_score, server_pushed = news_data
            
            # Kiểm tra xem title đã tồn tại chưa (UNIQUE constraint)
            existing = session.query(News).filter_by(title=title).first()
            if existing:
                print(f"⏭ Skipped (exists): {title[:50]}... - models.py:122")
                return False
            
            # Insert new record
            news = News(
                published_at=published_at,
                title=title,
                link=link,
                content=content,
                source=source,
                stock_related=stock_related,
                sentiment_score=sentiment_score,
                server_pushed=server_pushed,
            )
            session.add(news)
            session.commit()
            print(f"✓ Inserted: {title[:50]}... - models.py:138")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"✗ Error inserting news: {e} - models.py:143")
            return False
        finally:
            session.close()
    
    def insert_news_with_category(self, news_data: tuple, category: str = None) -> bool:
        """
        Insert một bài báo với category.
        
        Args:
            news_data: tuple gồm (published_at, title, link, content, source, stock_related, sentiment_score, server_pushed)
            category: Chuyên mục của bài báo
        """
        session = self.get_session()
        try:
            published_at, title, link, content, source, stock_related, sentiment_score, server_pushed = news_data
            
            existing = session.query(News).filter_by(title=title).first()
            if existing:
                print(f"⏭ Skipped (exists): {title[:50]}... - models.py:162")
                return False
            
            news = News(
                published_at=published_at,
                title=title,
                link=link,
                content=content,
                source=source,
                stock_related=stock_related,
                sentiment_score=sentiment_score,
                server_pushed=server_pushed,
                category=category,
            )
            session.add(news)
            session.commit()
            print(f"✓ Inserted: {title[:50]}... - models.py:178")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"✗ Error inserting news: {e} - models.py:183")
            return False
        finally:
            session.close()
    
    def update_content_by_id(self, news_id: str, content: str) -> bool:
        """
        Update content của bài báo theo ID.
        Tương tự hàm update_content_by_id trong Rust.
        """
        session = self.get_session()
        try:
            news = session.query(News).filter_by(id=news_id).first()
            if news:
                news.content = content
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"✗ Error updating content: {e} - models.py:203")
            return False
        finally:
            session.close()
    
    def fetch_id_and_links_by_source(self, source: str) -> list:
        """
        Lấy danh sách (id, link) theo source.
        Tương tự hàm fetch_id_and_links_by_source trong Rust.
        """
        session = self.get_session()
        try:
            results = session.query(News.id, News.link).filter_by(source=source).all()
            return [(str(r.id), r.link) for r in results]
        finally:
            session.close()
    
    def get_all_news(self, limit: int = 100) -> list:
        """Lấy tất cả news"""
        session = self.get_session()
        try:
            return session.query(News).limit(limit).all()
        finally:
            session.close()
    
    def news_exists(self, title: str) -> bool:
        """Kiểm tra news đã tồn tại chưa (theo title)"""
        session = self.get_session()
        try:
            return session.query(News).filter_by(title=title).first() is not None
        finally:
            session.close()
    
    def get_news_without_content(self, source: str = None) -> list:
        """Lấy các bài chưa có content để fetch sau"""
        session = self.get_session()
        try:
            query = session.query(News).filter(
                (News.content == None) | (News.content == "") | (News.content == "NA")
            )
            if source:
                query = query.filter_by(source=source)
            return query.all()
        finally:
            session.close()

    def update_sentiment_score(self, news_id: str, sentiment: str) -> bool:
        """
        Update sentiment score của một bài báo

        Args:
            news_id: UUID của bài báo
            sentiment: Sentiment score (e.g., "positive:0.95")

        Returns:
            True nếu update thành công, False nếu không tìm thấy hoặc lỗi
        """
        session = self.get_session()
        try:
            news = session.query(News).filter_by(id=news_id).first()
            if news:
                news.sentiment_score = sentiment
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"✗ Error updating sentiment: {e} - models.py:270")
            return False
        finally:
            session.close()

    def update_stock_related(self, news_id: str, stock_codes: str) -> bool:
        """
        Update stock_related của một bài báo

        Args:
            news_id: UUID của bài báo
            stock_codes: Mã chứng khoán (e.g., "VCB,HPG,VNM")

        Returns:
            True nếu update thành công, False nếu không tìm thấy hoặc lỗi
        """
        session = self.get_session()
        try:
            news = session.query(News).filter_by(id=news_id).first()
            if news:
                news.stock_related = stock_codes
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"✗ Error updating stock_related: {e} - models.py:296")
            return False
        finally:
            session.close()


# Singleton instance
db = Database()
