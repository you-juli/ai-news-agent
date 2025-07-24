import smtplib
from email.mime.text import MIMEText
import sqlite3
import os
import re

def super_clean_text(text):
    """Ultra-aggressive text cleaning to remove ALL problematic characters"""
    if not text:
        return ""
    
    # Convert to string
    text = str(text)
    
    # Remove ALL non-standard characters, keep only basic ASCII
    # Keep only letters, numbers, spaces, and basic punctuation
    text = re.sub(r'[^\x20-\x7E]', ' ', text)  # Remove non-printable ASCII
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = text.strip()
    
    return text

def send_news_email():
    """Send AI news email with ultra-safe encoding"""
    try:
        # Get articles from database
        conn = sqlite3.connect("data/articles.db")
        cursor = conn.execute("SELECT title, content, source, url FROM articles ORDER BY published_date DESC LIMIT 5")
        articles = cursor.fetchall()
        conn.close()
        
        if not articles:
            print("No articles found to send")
            return
        
        # Build simple text email (no HTML to avoid encoding issues)
        email_content = "Daily AI News and Research Update\n"
        email_content += "=" * 40 + "\n\n"
        
        for i, (title, content, source, url) in enumerate(articles, 1):
            # Super clean all text
            clean_title = super_clean_text(title)
            clean_content = super_clean_text(content)
            clean_source = super_clean_text(source)
            
            email_content += f"{i}. {clean_title}\n"
            email_content += f"   {clean_content[:200]}...\n"
            email_content += f"   Source: {clean_source}\n"
            if url:
                email_content += f"   URL: {url}\n"
            email_content += "\n" + "-" * 40 + "\n\n"
        
        # Email configuration
        smtp_server = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('EMAIL_PORT', '587'))
        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        recipient_email = os.getenv('TO_EMAIL')
        
        if not all([sender_email, sender_password, recipient_email]):
            print("Missing email configuration. Check your environment variables.")
            return
        
        # Create simple text message (no HTML, no special encoding)
        msg = MIMEText(email_content, 'plain')
        msg['Subject'] = "Daily AI News Update"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        print("Email sent successfully!")
        
    except Exception as e:
        print(f"Error sending email: {e}")
        import traceback
        traceback.print_exc()  # Print full error details

if __name__ == "__main__":
    send_news_email()
