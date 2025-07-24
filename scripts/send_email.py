import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_email():
    """Send the daily AI news email"""
    
    # Email settings - these come from GitHub secrets
    sender_email = "you.juli@gmail.com"  # You'll change this later
    password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('RECIPIENT_EMAIL')
    
    if not password or not recipient:
        print("❌ Email credentials not found in environment variables")
        print("Make sure GMAIL_APP_PASSWORD and RECIPIENT_EMAIL are set in GitHub secrets")
        return
    
    # Load today's summary
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        with open(f'data/summary_{today}.json', 'r') as f:
            summary_data = json.load(f)
        email_content = summary_data['email_content']
    except FileNotFoundError:
        email_content = f"""🤖 Your Daily AI News Summary - {datetime.now().strftime('%B %d, %Y')}

Sorry, no AI news was collected today. This might be because:
- The news sources were temporarily unavailable
- No new articles were published
- There was a technical issue

Your AI agent will try again tomorrow! 🚀
"""
    
    # Create email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = f"🤖 Daily AI News - {datetime.now().strftime('%B %d, %Y')}"
    
    # Add the email content
    message.attach(MIMEText(email_content, "plain"))
    
    # Send the email
    try:
        print("📧 Connecting to Gmail...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Enable encryption
            server.login(sender_email, password)
            
            print("📤 Sending email...")
            server.sendmail(sender_email, recipient, message.as_string())
            
        print("✅ Email sent successfully!")
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Email authentication failed!")
        print("Please check your Gmail app password is correct")
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")

if __name__ == "__main__":
    print("🚀 Starting email delivery...")
    send_email()
