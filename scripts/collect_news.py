import sqlite3
import json
from datetime import datetime
import re
import os

class LLMSummarizer:
    def __init__(self):
        self.db_path = "data/articles.db"
        self.summarizer = None
        self.setup_model()
    
    def setup_model(self):
        """Initialize the open-source summarization model"""
        try:
            print("🤖 Loading AI summarization model...")
            from transformers import pipeline
            
            # Use a lightweight but effective model that works well in GitHub Actions
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1,  # Use CPU (GitHub Actions doesn't have GPU)
                max_length=1024,
                truncation=True
            )
            print("✅ AI model loaded successfully!")
            
        except Exception as e:
            print(f"⚠️ Could not load AI model: {e}")
            print("📝 Falling back to simple text extraction...")
            self.summarizer = None
    
    def get_recent_articles(self):
        """Get articles from the last day"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('''
                SELECT * FROM articles 
                WHERE processed = FALSE 
                ORDER BY published_date DESC
                LIMIT 20
            ''')
            articles = cursor.fetchall()
            conn.close()
            return articles
        except Exception as e:
            print(f"Error getting articles: {e}")
            return []
    
    def ai_summarize(self, text, summary_type="general"):
        """Use AI to create intelligent summaries"""
        if not self.summarizer or not text or len(text.strip()) < 50:
            return self.fallback_summarize(text)
        
        try:
            # Clean the text
            clean_text = self.clean_text(text)
            
            # Adjust parameters based on summary type
            if summary_type == "research":
                max_length = 150
                min_length = 60
            elif summary_type == "news":
                max_length = 100
                min_length = 40
            else:
                max_length = 120
                min_length = 50
            
            # Generate summary using AI
            summary_result = self.summarizer(
                clean_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True
            )
            
            ai_summary = summary_result[0]['summary_text']
            
            # Post-process the summary
            processed_summary = self.enhance_summary(ai_summary, summary_type)
            
            return processed_summary
            
        except Exception as e:
            print(f"AI summarization failed: {e}")
            return self.fallback_summarize(text)
    
    def clean_text(self, text):
        """Clean and prepare text for summarization"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Limit length for the model (BART can handle ~1024 tokens)
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        return text.strip()
    
    def enhance_summary(self, summary, summary_type):
        """Post-process AI summary to make it more useful"""
        if not summary:
            return "No summary available."
        
        # Add context based on type
        if summary_type == "research":
            if not any(word in summary.lower() for word in ['research', 'study', 'paper', 'method']):
                summary = f"Research: {summary}"
        
        # Ensure proper capitalization
        summary = summary[0].upper() + summary[1:] if len(summary) > 1 else summary.upper()
        
        # Ensure it ends with proper punctuation
        if summary and summary[-1] not in '.!?':
            summary += '.'
        
        return summary
    
    def fallback_summarize(self, text, max_sentences=2):
        """Fallback method if AI summarization fails"""
        if not text:
            return "No summary available."
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        # Take first 2 sentences or less
        summary_sentences = sentences[:max_sentences]
        summary = '. '.join(summary_sentences)
        
        if len(summary) > 250:
            summary = summary[:250] + "..."
        
        return summary if summary else "Brief summary not available."
    
    def categorize_content(self, title, content):
        """Intelligent categorization using keyword analysis"""
        text = (title + " " + (content or "")).lower()
        
        # Research indicators
        research_words = [
            'paper', 'research', 'study', 'arxiv', 'algorithm', 'model', 
            'method', 'approach', 'framework', 'evaluation', 'experiment',
            'analysis', 'dataset', 'benchmark', 'neural', 'learning'
        ]
        
        # Business/Industry indicators
        business_words = [
            'funding', 'startup', 'company', 'investment', 'acquisition',
            'partnership', 'product', 'launch', 'market', 'revenue',
            'ceo', 'announcement', 'enterprise', 'commercial'
        ]
        
        # Tools/Resources indicators
        tool_words = [
            'tool', 'open source', 'github', 'release', 'library',
            'framework', 'api', 'platform', 'software', 'code',
            'implementation', 'available', 'download'
        ]
        
        # Breakthrough/Important news
        breakthrough_words = [
            'breakthrough', 'milestone', 'achievement', 'record',
            'first', 'new', 'revolutionary', 'significant', 'major',
            'advance', 'innovation', 'discovery'
        ]
        
        research_score = sum(1 for word in research_words if word in text)
        business_score = sum(1 for word in business_words if word in text)
        tool_score = sum(1 for word in tool_words if word in text)
        breakthrough_score = sum(1 for word in breakthrough_words if word in text)
        
        # Determine category based on highest score
        scores = {
            'research': research_score + breakthrough_score * 0.5,
            'business': business_score,
            'tools': tool_score,
            'breakthrough': breakthrough_score
        }
        
        max_category = max(scores, key=scores.get)
        
        # If breakthrough has high score, prioritize it
        if breakthrough_score >= 2:
            return 'breakthrough'
        
        return max_category if scores[max_category] > 0 else 'news'
    
    def generate_daily_summary(self):
        """Create the daily email summary using AI"""
        articles = self.get_recent_articles()
        
        if not articles:
            return "No new AI articles found today. The AI research world might be taking a coffee break! ☕"
        
        categories = {
            'breakthrough': [],
            'research': [],
            'business': [],
            'tools': [],
            'news': []
        }
        
        print(f"📊 Processing {len(articles)} articles with AI...")
        
        # Process each article with AI
        for i, article in enumerate(articles):
            try:
                _, title, content, source, url, published, category, _ = article
                
                print(f"🧠 AI processing article {i+1}/{len(articles)}: {title[:50]}...")
                
                # Categorize content intelligently
                cat = self.categorize_content(title, content or "")
                
                # Determine summary type for better AI processing
                summary_type = "research" if cat in ['research', 'breakthrough'] else "news"
                
                # Generate AI summary
                ai_summary = self.ai_summarize(content or title, summary_type)
                
                # Create enhanced article entry
                article_entry = {
                    'title': title,
                    'summary': ai_summary,
                    'source': source,
                    'url': url or "",
                    'category_detected': cat,
                    'summary_type': summary_type
                }
                
                categories[cat].append(article_entry)
                
            except Exception as e:
                print(f"Error processing article: {e}")
        
        # Generate email content
        email_content = self.format_enhanced_email(categories)
        
        # Save summary
        today = datetime.now().strftime('%Y-%m-%d')
        os.makedirs('data', exist_ok=True)
        
        with open(f'data/summary_{today}.json', 'w') as f:
            json.dump({
                'date': today,
                'categories': categories,
                'email_content': email_content,
                'total_articles': len(articles),
                'ai_processed': True
            }, f, indent=2)
        
        # Mark articles as processed
        self.mark_processed(articles)
        
        print("✅ AI summary generation complete!")
        return email_content
    
    def format_enhanced_email(self, categories):
        """Format email with AI-generated insights"""
        date = datetime.now().strftime('%B %d, %Y')
        
        # Count total articles
        total = sum(len(articles) for articles in categories.values())
        
        email = f"""🤖 Your AI-Powered Daily Research Summary - {date}

🌟 Today's AI Intelligence Report
═══════════════════════════════════════

Hello! Your AI assistant analyzed {total} articles today and found some fascinating developments:

"""
        
        # Breakthrough section (highest priority)
        if categories['breakthrough']:
            email += f"🚀 BREAKTHROUGH DISCOVERIES ({len(categories['breakthrough'])})\n"
            email += "═" * 55 + "\n"
            for item in categories['breakthrough'][:2]:
                email += f"💥 {item['title']}\n"
                email += f"   🧠 AI Analysis: {item['summary']}\n"
                email += f"   📍 Source: {item['source']}\n\n"
        
        # Research papers
        if categories['research']:
            email += f"🔬 RESEARCH PAPERS ({len(categories['research'])})\n"
            email += "═" * 55 + "\n"
            for item in categories['research'][:3]:
                email += f"📄 {item['title']}\n"
                email += f"   🧠 AI Analysis: {item['summary']}\n"
                email += f"   📍 Source: {item['source']}\n\n"
        
        # Industry news
        if categories['business']:
            email += f"💼 INDUSTRY & BUSINESS ({len(categories['business'])})\n"
            email += "═" * 55 + "\n"
            for item in categories['business'][:3]:
                email += f"💰 {item['title']}\n"
                email += f"   🧠 AI Analysis: {item['summary']}\n"
                email += f"   📍 Source: {item['source']}\n\n"
        
        # Tools and resources
        if categories['tools']:
            email += f"🛠️ NEW TOOLS & RESOURCES ({len(categories['tools'])})\n"
            email += "═" * 55 + "\n"
            for item in categories['tools']:
                email += f"⚒️  {item['title']}\n"
                email += f"   🧠 AI Analysis: {item['summary']}\n"
                email += f"   📍 Source: {item['source']}\n\n"
        
        # General news
        if categories['news']:
            email += f"📰 GENERAL AI NEWS ({len(categories['news'])})\n"
            email += "═" * 55 + "\n"
            for item in categories['news'][:3]:
                email += f"📢 {item['title']}\n"
                email += f"   🧠 AI Analysis: {item['summary']}\n"
                email += f"   📍 Source: {item['source']}\n\n"
        
        # Footer
        email += "\n" + "═"*60 + "\n"
        email += "🤖 Powered by Open-Source AI Summarization\n"
        email += f"📊 Processed {total} articles with artificial intelligence\n"
        email += f"⏰ Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M UTC')}\n"
        email += "═"*60 + "\n"
        
        return email
    
    def mark_processed(self, articles):
        """Mark articles as processed"""
        try:
            conn = sqlite3.connect(self.db_path)
            for article in articles:
                conn.execute('UPDATE articles SET processed = TRUE WHERE id = ?', (article[0],))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error marking articles as processed: {e}")

if __name__ == "__main__":
    print("🚀 Starting AI-powered summary generation...")
    summarizer = LLMSummarizer()
    email_content = summarizer.generate_daily_summary()
    print("\n📧 Email preview:")
    print("=" * 60)
    print(email_content[:800] + "..." if len(email_content) > 800 else email_content)
