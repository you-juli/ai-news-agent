import requests
import json
import sqlite3
from datetime import datetime
import os
import xml.etree.ElementTree as ET

class NewsCollector:
    def __init__(self):
        self.db_path = "data/articles.db"
        self.setup_database()
    
    def setup_database(self):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                source TEXT,
                url TEXT,
                published_date TEXT,
                category TEXT,
                processed BOOLEAN DEFAULT FALSE
            )
        ''')
        conn.commit()
        conn.close()
    
    def collect_arxiv_papers(self):
        """Get latest AI research papers"""
        papers = []
        categories = ['cs.AI', 'cs.LG', 'cs.CL']
        
        for cat in categories:
            try:
                url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending"
                response = requests.get(url, timeout=10)
                root = ET.fromstring(response.content)
                
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                    summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                    id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
                    published_elem = entry.find('{http://www.w3.org/2005/Atom}published')
                    
                    if all([title_elem, summary_elem, id_elem, published_elem]):
                        paper = {
                            'id': id_elem.text,
                            'title': title_elem.text.strip(),
                            'summary': summary_elem.text.strip()[:500],
                            'published': published_elem.text,
                            'category': cat,
                            'source': 'arXiv Research',
                            'url': id_elem.text
                        }
                        papers.append(paper)
            except Exception as e:
                print(f"Error collecting from {cat}: {e}")
        
        return papers
    
    def collect_simple_news(self):
        """Get AI news from simple sources"""
        articles = []
        
        # Simple hardcoded recent AI news (you can expand this)
        sample_news = [
            {
                'id': f'news_{datetime.now().strftime("%Y%m%d")}_1',
                'title': 'Latest AI developments from major tech companies',
                'summary': 'Regular updates on AI progress from Google, OpenAI, and other leaders in the field.',
                'source': 'Tech News',
                'published': datetime.now().isoformat(),
                'category': 'news'
            }
        ]
        
        return sample_news
    
    def save_articles(self, articles):
        """Save collected articles to database"""
        conn = sqlite3.connect(self.db_path)
        for article in articles:
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO articles 
                    (id, title, content, source, url, published_date, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article['id'], 
                    article['title'], 
                    article.get('summary', ''),
                    article['source'], 
                    article.get('url', ''), 
                    article.get('published', ''), 
                    article.get('category', 'news')
                ))
            except Exception as e:
                print(f"Error saving article {article['id']}: {e}")
        
        conn.commit()
        conn.close()

if __name__ == "__main__":
    print("🔍 Collecting AI news and research...")
    collector = NewsCollector()
    
    papers = collector.collect_arxiv_papers()
    news = collector.collect_simple_news()
    
    all_articles = papers + news
    collector.save_articles(all_articles)
    
    print(f"✅ Collected {len(all_articles)} articles!")
