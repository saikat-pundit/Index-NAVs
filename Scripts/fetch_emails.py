import imaplib
import email
from email.header import decode_header
import csv
import os
from datetime import datetime
import sys

def decode_mime_words(text):
    """Helper function to decode email subject/sender names."""
    if text is None:
        return ""
    decoded_parts = decode_header(text)
    result = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(encoding if encoding else 'utf-8', errors='ignore'))
        else:
            result.append(part)
    return " ".join(result)

def fetch_emails():
    # Get credentials from environment variables (set in GitHub Actions)
    email_user = os.getenv('YANDEX_EMAIL')
    email_pass = os.getenv('YANDEX_APP_PASSWORD')
    
    if not email_user or not email_pass:
        print("ERROR: Email or App Password not set in environment.")
        sys.exit(1)
    
    # IMAP server settings for Yandex
    IMAP_SERVER = 'imap.yandex.com'
    IMAP_PORT = 993
    
    try:
        # Connect to server
        print("Connecting to Yandex IMAP server...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(email_user, email_pass)
        mail.select('INBOX')
        
        # Search for ALL emails (use 'UNSEEN' for only unread)
        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            print("No emails found.")
            return
        
        email_ids = messages[0].split()
        print(f"Found {len(email_ids)} emails.")
        
        emails_data = []
        
        # Fetch latest 50 emails (adjust as needed)
        for eid in email_ids[-50:]:
            status, msg_data = mail.fetch(eid, '(RFC822)')
            if status != 'OK':
                continue
                
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract headers
            subject = decode_mime_words(msg.get('Subject'))
            from_ = decode_mime_words(msg.get('From'))
            date_ = msg.get('Date')
            
            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            body = part.get_payload(decode=True).decode('latin-1', errors='ignore')
                        break
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    body = msg.get_payload(decode=True).decode('latin-1', errors='ignore')
            
            # Clean body (first 200 chars)
            body_preview = body[:200].replace('\n', ' ').replace('\r', ' ').strip()
            
            emails_data.append([from_, subject, date_, body_preview])
        
        # Generate CSV filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'email_export_{timestamp}.csv'
        
        # Write to CSV
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['From', 'Subject', 'Date', 'Body_Preview'])
            writer.writerows(emails_data)
        
        print(f"✅ Saved {len(emails_data)} emails to {csv_filename}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_emails()
