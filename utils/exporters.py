import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class CSVExporter:
    """Export articles to CSV format"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self, 
        articles: List[Dict], 
        filename: Optional[str] = None,
        include_content: bool = True
    ) -> str:
        """
        Export danh sách articles ra file CSV.
        
        Args:
            articles: List các dict chứa thông tin bài báo
            filename: Tên file (không cần .csv)
            include_content: Có bao gồm nội dung đầy đủ không
        
        Returns:
            Đường dẫn đến file CSV đã tạo
        """
        if not articles:
            print("No articles to export!")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"articles_{timestamp}"
        
        filepath = self.output_dir / f"{filename}.csv"
        
        # Fieldnames theo cấu trúc bảng news mới
        fieldnames = [
            'published_at',
            'title',
            'link',
            'source',
            'stock_related',
            'sentiment_score',
            'server_pushed',
            'category',
        ]
        
        if include_content:
            fieldnames.insert(4, 'content')  # Insert content after link
        
        # Ghi file CSV
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for article in articles:
                row = {
                    'published_at': article.get('published_at', 0),
                    'title': article.get('title', ''),
                    'link': article.get('link', ''),
                    'source': article.get('source', ''),
                    'stock_related': article.get('stock_related', 'NA'),
                    'sentiment_score': article.get('sentiment_score', 'NA'),
                    'server_pushed': article.get('server_pushed', False),
                    'category': article.get('category', ''),
                }
                
                if include_content:
                    row['content'] = article.get('content', '')
                
                writer.writerow(row)
        
        print(f"✓ Exported {len(articles)} articles to: {filepath}")
        return str(filepath)
    
    def export_summary(
        self, 
        articles: List[Dict], 
        filename: Optional[str] = None
    ) -> str:
        """Export phiên bản tóm tắt (không có content)"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"articles_summary_{timestamp}"
        
        return self.export(articles, filename, include_content=False)


class JSONExporter:
    """Export articles to JSON format"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self, 
        articles: List[Dict], 
        filename: Optional[str] = None,
        indent: int = 2
    ) -> str:
        """Export danh sách articles ra file JSON"""
        if not articles:
            print("No articles to export!")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"articles_{timestamp}"
        
        filepath = self.output_dir / f"{filename}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=indent)
        
        print(f"✓ Exported {len(articles)} articles to: {filepath}")
        return str(filepath)


# Convenience functions
def export_to_csv(articles: List[Dict], filename: str = None, include_content: bool = True) -> str:
    """Quick export to CSV"""
    exporter = CSVExporter()
    return exporter.export(articles, filename, include_content)


def export_to_json(articles: List[Dict], filename: str = None) -> str:
    """Quick export to JSON"""
    exporter = JSONExporter()
    return exporter.export(articles, filename)
