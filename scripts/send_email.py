import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import sqlite3
import os

def clean_text(text):
    """Clean text to remove problematic characters"""
    if not text:
        return ""
    
    # Replace non-breaking spaces and other problematic characters
    text = text.replace('\xa0', ' ')  # Non-breaking space
    text = text.replace('\u2019', "'")  # Right single quotation mark
    text = text.replace('\u2018', "'")  # Left single quotation mark
    text = text.replace('\u201c', '"')  # Left double quotation mark
    text = text.replace('\u201d', '"')  # Right double quotation mark
    text = text.replace('\u2013', '-')  # En dash
    text = text.replace('\u2014', '--')  # Em dash
    
    # Encode to UTF-8 and decode to ensure clean text
    try:
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
    except:
        text = str(text)
    
    return text

def send_news_email():
    """Send AI news email with proper encoding"""
    try:
        # Get articles from database
        conn = sqlite3.connect("data/articles.db")
        cursor = conn.execute("SELECT title, content, source, url FROM articles ORDER BY published_date DESC LIMIT 10")
        articles = cursor.fetchall()
        conn.close()
        
        if not articles:
            print("No articles found to send")
            return
        
        # Build email content
        email_content = "<h2>🤖 Daily AI News & Research</h2>\n"
        
        for title, content, source, url in articles:
            # Clean all text content
            clean_title = clean_text(title)
            clean_content = clean_text(content)
            clean_source = clean_text(source)
            
            email_content += f"""
            <div style="margin-bottom: 20px; padding: 15px; border-left: 3px solid #007acc;">
                <h3 style="color: #007acc; margin: 0 0 10px 0;">{clean_title}</h3>
                <p style="margin: 0 0 10px 0; color: #333;">{clean_content}</p>
                <p style="margin: 0; font-size: 12px; color: #666;">
                    <strong>Source:</strong> {clean_source}
                    {f' | <a href="{url}">Read more</a>' if url else ''}
                </p>
            </div>
            """
        
        # Email configuration from environment variables
        smtp_server = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('EMAIL_PORT', '587'))
        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        recipient_email = os.getenv('TO_EMAIL')
        
        if not all([sender_email, sender_password, recipient_email]):
            print("❌ Missing email configuration. Check your environment variables.")
            return
        
        # Create message with proper encoding
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header('🤖 Daily AI News & Research Update', 'utf-8')
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Create HTML part with UTF-8 encoding
        html_part = MIMEText(email_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Send with proper encoding
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text.encode('utf-8'))
        server.quit()
        
        print("✅ Email sent successfully!")
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")

if __name__ == "__main__":
    send_news_email()
