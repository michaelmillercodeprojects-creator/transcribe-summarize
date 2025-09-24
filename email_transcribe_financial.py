#!/usr/bin/env python3
"""
Email-Integrated Financial Transcription Tool
Processes audio attachments from email and sends back analysis
"""
import os
import sys
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import tempfile
import time
from datetime import datetime
import argparse
from typing import List, Tuple
import mimetypes

# Import our transcription functions
try:
    from transcribe_financial import transcribe_audio, create_financial_summary, load_api_key
except ImportError:
    print("Error: transcribe_financial.py not found in current directory")
    print("Please ensure transcribe_financial.py is in the same folder")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Missing required package: python-dotenv")
    print("Please install: pip install python-dotenv")
    sys.exit(1)

load_dotenv()

class EmailProcessor:
    def __init__(self):
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
        if not self.email_address or not self.email_password:
            raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in .env file")
    
    def connect_imap(self):
        """Connect to IMAP server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.email_password)
            return mail
        except Exception as e:
            raise RuntimeError(f"Failed to connect to IMAP: {e}")
    
    def connect_smtp(self):
        """Connect to SMTP server"""
        try:
            server = smtplib.SMTP(self.smtp_server, 587)
            server.starttls()
            server.login(self.email_address, self.email_password)
            return server
        except Exception as e:
            raise RuntimeError(f"Failed to connect to SMTP: {e}")
    
    def get_audio_links(self, msg) -> List[str]:
        """Extract audio/video links from email content with intelligent detection"""
        links = []
        
        # Get email body content and subject
        subject = msg['Subject'] or ""
        body = ""
        html_content = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif part.get_content_type() == "text/html":
                    html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    # Extract links from HTML
                    import re
                    html_links = re.findall(r'href=[\'"]?([^\'" >]+)', html_content)
                    body += " " + " ".join(html_links)
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        # Extract URLs from body using regex
        import re
        import html
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        raw_urls = re.findall(url_pattern, body)
        
        # Normalize and deduplicate URLs (handle HTML entities like &amp;)
        normalized_urls = []
        seen_urls = set()
        
        for url in raw_urls:
            # Decode HTML entities (&amp; -> &, etc.)
            normalized_url = html.unescape(url)
            
            # Remove trailing punctuation that might be picked up
            normalized_url = normalized_url.rstrip('.,;!?')
            
            # Only add if we haven't seen this normalized URL before
            if normalized_url not in seen_urls:
                normalized_urls.append(normalized_url)
                seen_urls.add(normalized_url)
        
        found_urls = normalized_urls
        
        print(f"Found {len(found_urls)} unique URLs in email:")
        for url in found_urls[:10]:  # Show first 10 URLs for debugging
            print(f"  - {url}")
        
        # Check if this looks like a webinar/audio content email
        webinar_indicators = [
            'webinar', 'replay', 'recording', 'watch', 'listen', 'audio', 'video',
            'presentation', 'meeting', 'conference', 'session', 'discussion',
            'podcast', 'interview', 'talk', 'seminar', 'workshop'
        ]
        
        email_text = (subject + " " + body).lower()
        has_webinar_indicators = any(indicator in email_text for indicator in webinar_indicators)
        
        if has_webinar_indicators:
            print("Email appears to contain webinar/audio content - checking all links")
        
        # Enhanced link detection strategy
        candidate_links = []
        
        for url in found_urls:
            # Check if it's a security-wrapped URL that might contain audio links
            unwrapped_url = self.unwrap_security_url(url)
            
            # Strategy 1: Direct audio/video platform detection
            urls_to_check = [url, unwrapped_url] if unwrapped_url != url else [url]
            
            for check_url in urls_to_check:
                # Direct platforms
                if any(domain in check_url.lower() for domain in [
                    'dropbox.com', 'drive.google.com', 'zoom.us', 'youtube.com', 'youtu.be',
                    'onedrive.live.com', 'box.com', 'mediafire.com', 'mega.nz',
                    'wetransfer.com', 'sendspace.com', 'zippyshare.com', 'vimeo.com',
                    'soundcloud.com', 'spotify.com', 'anchor.fm', 'libsyn.com',
                    'buzzsprout.com', 'simplecast.com', 'fireside.fm', 'transistor.fm',
                    'wistia.com', 'brightcove.com', 'jwplayer.com', 'vidyard.com',
                    'loom.com', 'webex.com', 'gotomeeting.com', 'teams.microsoft.com',
                    'meet.google.com', 'twitch.tv', '.mp3', '.mp4', '.wav', '.m4a', 
                    '.mov', '.avi', '.webm', 'amazonaws.com'
                ]):
                    print(f"Found direct audio/video platform link: {url}")
                    if unwrapped_url != url:
                        print(f"  -> Unwrapped to: {unwrapped_url}")
                    links.append(url)
                    break
            
            # Strategy 2: If this is a webinar email, check tracking/redirect links
            if has_webinar_indicators and not links:
                # Check for common webinar/event platforms and marketing redirects
                if any(platform in url.lower() for platform in [
                    'hubspot', 'eventbrite', 'zoom', 'webex', 'gotomeeting', 'teams',
                    'brighttalk', 'on24', 'bigmarker', 'livestorm', 'crowdcast',
                    'demio', 'getresponse', 'mailchimp', 'constantcontact'
                ]):
                    candidate_links.append(url)
        
        # Strategy 3: If we found webinar indicators but no direct links, 
        # try to follow redirect chains for the most promising candidates
        if has_webinar_indicators and not links and candidate_links:
            print("Webinar email detected but no direct links found. Checking redirect chains...")
            
            for candidate_url in candidate_links[:3]:  # Check top 3 candidates
                try:
                    final_url = self.follow_redirect_chain(candidate_url)
                    if final_url and final_url != candidate_url:
                        print(f"Redirect chain: {candidate_url} -> {final_url}")
                        
                        # Check if the final URL is an audio/video platform OR contains webinar content
                        if any(domain in final_url.lower() for domain in [
                            'dropbox.com', 'drive.google.com', 'zoom.us', 'youtube.com',
                            'vimeo.com', 'wistia.com', 'brightcove.com', 'jwplayer.com',
                            'vidyard.com', 'loom.com', '.mp3', '.mp4', '.wav', '.m4a',
                            'amazonaws.com', 'cloudfront.net', 'webex.com', 'gotomeeting.com',
                            'teams.microsoft.com', 'meet.google.com', 'bigmarker.com',
                            'brighttalk.com', 'on24.com', 'livestorm.com', 'crowdcast.com',
                            'demio.com', 'eventbrite.com'
                        ]):
                            print(f"Found webinar link via redirect: {final_url}")
                            links.append(candidate_url)  # Use original URL for processing
                            break
                        
                        # Also check if the final URL contains webinar-related keywords
                        elif any(keyword in final_url.lower() for keyword in [
                            'webinar', 'recording', 'replay', 'watch', 'video', 'audio',
                            'stream', 'presentation', 'meeting'
                        ]):
                            print(f"Found potential webinar content: {final_url}")
                            # Try to extract any embedded video/audio URLs from this page
                            embedded_links = self.extract_media_from_page(final_url)
                            if embedded_links:
                                print(f"Found embedded media links: {embedded_links}")
                                links.extend(embedded_links)
                                break
                            else:
                                # As a last resort, include the redirect URL itself
                                print(f"Including redirect URL as potential webinar source: {candidate_url}")
                                links.append(candidate_url)
                                break
                except Exception as e:
                    print(f"Error following redirect for {candidate_url}: {e}")
                    continue
        
        if found_urls and not links:
            if has_webinar_indicators:
                print("Webinar email detected but no processable audio/video links found")
            else:
                print("No webinar indicators or audio/video links found")
        
        return links
    
    def unwrap_security_url(self, url: str) -> str:
        """Unwrap URLs from corporate security services."""
        import urllib.parse
        
        # Handle Microsoft Defender/Office 365 URL wrapping
        if "urldefense.com/v3/" in url:
            try:
                # Extract the wrapped URL from urldefense.com format
                # Format: https://urldefense.com/v3/__ENCODED_URL__;!!...
                wrapped_part = url.split("__")[1].split("__;")[0]
                # Replace URL encoding
                unwrapped = wrapped_part.replace("*", "%")
                unwrapped = urllib.parse.unquote(unwrapped)
                return unwrapped
            except (IndexError, ValueError):
                return url
        
        # Handle Proofpoint URL wrapping
        if "urldefense.proofpoint.com" in url:
            try:
                # Extract URL parameter
                parsed = urllib.parse.urlparse(url)
                params = urllib.parse.parse_qs(parsed.query)
                if 'u' in params:
                    unwrapped = params['u'][0]
                    # Replace encoding
                    unwrapped = unwrapped.replace('-', '%').replace('_', '/')
                    unwrapped = urllib.parse.unquote(unwrapped)
                    return unwrapped
            except (IndexError, ValueError, KeyError):
                return url
        
        # Handle other common security wrappers
        for pattern in ["safelinks.protection.outlook.com", "protect-us.mimecast.com", "urlscan.io"]:
            if pattern in url:
                try:
                    parsed = urllib.parse.urlparse(url)
                    params = urllib.parse.parse_qs(parsed.query)
                    # Try common parameter names for the wrapped URL
                    for param in ['url', 'u', 'link', 'target']:
                        if param in params:
                            unwrapped = urllib.parse.unquote(params[param][0])
                            return unwrapped
                except:
                    pass
        
        return url
    
    def follow_redirect_chain(self, url: str, max_redirects: int = 10) -> str:
        """Follow redirect chain to get final URL with enhanced tracking"""
        try:
            import requests
            from urllib.parse import urljoin, urlparse
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            current_url = url
            visited_urls = set()
            
            for i in range(max_redirects):
                if current_url in visited_urls:
                    print(f"Redirect loop detected at {current_url}")
                    break
                visited_urls.add(current_url)
                
                try:
                    response = requests.get(current_url, headers=headers, allow_redirects=False, timeout=15)
                    
                    # Handle different redirect status codes
                    if response.status_code in [301, 302, 303, 307, 308]:
                        location = response.headers.get('Location')
                        if location:
                            if location.startswith('//'):
                                current_url = 'https:' + location
                            elif location.startswith('/'):
                                current_url = urljoin(current_url, location)
                            elif not location.startswith('http'):
                                current_url = urljoin(current_url, location)
                            else:
                                current_url = location
                            print(f"Redirect {i+1}: {current_url}")
                        else:
                            break
                    elif response.status_code == 200:
                        # Check for JavaScript redirects or meta refresh
                        content = response.text[:5000]  # First 5KB should be enough
                        
                        # Look for meta refresh
                        import re
                        meta_refresh = re.search(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\'][^"\']*url=([^"\']+)["\']', content, re.IGNORECASE)
                        if meta_refresh:
                            new_url = meta_refresh.group(1)
                            current_url = urljoin(current_url, new_url)
                            print(f"Meta refresh redirect: {current_url}")
                            continue
                        
                        # Look for JavaScript redirects
                        js_redirect = re.search(r'window\.location\.(?:href|assign|replace)\s*=\s*["\']([^"\']+)["\']', content)
                        if js_redirect:
                            new_url = js_redirect.group(1)
                            current_url = urljoin(current_url, new_url)
                            print(f"JavaScript redirect: {current_url}")
                            continue
                        
                        # Final URL reached
                        break
                    else:
                        print(f"Unexpected status code {response.status_code} for {current_url}")
                        break
                        
                except requests.exceptions.SSLError:
                    # Try with different SSL approach
                    try:
                        response = requests.get(current_url, headers=headers, allow_redirects=False, timeout=15, verify=False)
                        # Process same as above but skip SSL verification
                        if response.status_code in [301, 302, 303, 307, 308]:
                            location = response.headers.get('Location')
                            if location:
                                current_url = urljoin(current_url, location) if not location.startswith('http') else location
                                print(f"SSL-bypass redirect {i+1}: {current_url}")
                            else:
                                break
                        else:
                            break
                    except Exception:
                        break
                except Exception as e:
                    print(f"Error at redirect step {i+1}: {e}")
                    break
            
            return current_url
            
        except Exception as e:
            print(f"Error following redirects for {url}: {e}")
            return url
    
    def extract_media_from_page(self, url: str) -> List[str]:
        """Extract media URLs from a webpage with comprehensive search."""
        try:
            import requests
            import re
            try:
                from bs4 import BeautifulSoup
            except ImportError:
                print("BeautifulSoup not available for page parsing. Install with: pip install beautifulsoup4")
                return []
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            print(f"Parsing webpage content from: {url}")
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                print(f"Failed to fetch page: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            media_urls = []
            
            # Look for direct video/audio elements
            for element in soup.find_all(['video', 'audio']):
                src = element.get('src') or element.get('data-src')
                if src:
                    media_urls.append(self.make_absolute_url(src, url))
            
            # Look for iframes (common for embedded videos)
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src') or iframe.get('data-src')
                if src and any(platform in src for platform in ['youtube', 'vimeo', 'wistia', 'brightcove', 'jwplayer']):
                    media_urls.append(src)
            
            # Look for JavaScript variables containing media URLs
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for video/audio URLs in JavaScript
                    js_urls = re.findall(r'["\']https?://[^"\']*\.(?:mp4|mp3|m4v|m4a|webm|ogg|avi|mov|wav|flac)[^"\']*["\']', script.string)
                    for js_url in js_urls:
                        media_urls.append(js_url.strip('"\''))
                    
                    # Look for streaming service URLs
                    streaming_patterns = [
                        r'["\']https?://[^"\']*(?:youtube\.com|youtu\.be|vimeo\.com|wistia\.com)[^"\']*["\']',
                        r'["\']https?://[^"\']*\.(?:amazonaws\.com|cloudfront\.net)[^"\']*\.(?:mp4|mp3|m4v|m4a)[^"\']*["\']'
                    ]
                    for pattern in streaming_patterns:
                        js_urls = re.findall(pattern, script.string)
                        for js_url in js_urls:
                            media_urls.append(js_url.strip('"\''))
            
            # Look for links with media-related text or classes
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().lower().strip()
                classes = ' '.join(link.get('class', [])).lower()
                
                # Check for media-related keywords
                media_keywords = ['watch', 'play', 'video', 'recording', 'replay', 'webinar', 'listen', 'audio', 'stream']
                if any(word in text for word in media_keywords) or any(word in classes for word in media_keywords):
                    absolute_url = self.make_absolute_url(href, url)
                    media_urls.append(absolute_url)
                
                # Check if href directly points to media file or platform
                if any(platform in href.lower() for platform in [
                    'youtube.com', 'vimeo.com', 'dropbox.com', 'drive.google.com',
                    '.mp4', '.mp3', '.m4a', 'zoom.us', 'wistia.com', 'brightcove.com'
                ]):
                    absolute_url = self.make_absolute_url(href, url)
                    media_urls.append(absolute_url)
            
            # Look for data attributes that might contain media URLs
            for element in soup.find_all(attrs={'data-video': True}):
                media_urls.append(element['data-video'])
            
            for element in soup.find_all(attrs={'data-src': True}):
                src = element['data-src']
                if any(ext in src for ext in ['.mp4', '.mp3', '.m4v', '.webm', 'youtube', 'vimeo']):
                    media_urls.append(self.make_absolute_url(src, url))
            
            # Remove duplicates and clean up
            unique_urls = list(set(media_urls))
            
            print(f"Found {len(unique_urls)} potential media links on page")
            for i, link in enumerate(unique_urls[:5]):  # Show first 5
                print(f"  {i+1}: {link[:100]}...")
                
            return unique_urls
            
        except Exception as e:
            print(f"Error extracting media from {url}: {e}")
            return []
    
    def make_absolute_url(self, url: str, base_url: str) -> str:
        """Convert relative URL to absolute URL."""
        from urllib.parse import urljoin
        if url.startswith(('http://', 'https://')):
            return url
        elif url.startswith('//'):
            return 'https:' + url
        else:
            return urljoin(base_url, url)
    
    def get_audio_attachments(self, msg) -> List[Tuple[str, bytes]]:
        """Extract audio attachments from email message (fallback for small files)"""
        attachments = []
        
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                if filename:
                    content_type = part.get_content_type()
                    # Check if it's an audio file
                    if (content_type.startswith('audio/') or 
                        filename.lower().endswith(('.mp3', '.wav', '.m4a', '.mp4', '.mov', '.avi', '.flv'))):
                        content = part.get_payload(decode=True)
                        # Only process smaller attachments (< 25MB)
                        if len(content) < 25 * 1024 * 1024:
                            attachments.append((filename, content))
        
        return attachments
    
    def save_attachment(self, filename: str, content: bytes) -> str:
        """Save attachment to temporary file"""
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path
    
    def markdown_to_html(self, text: str) -> str:
        """Convert basic markdown to HTML for email formatting."""
        import re
        
        # Convert headers
        text = re.sub(r'^## (.+)$', r'<h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h1 style="color: #2c3e50;">\1</h1>', text, flags=re.MULTILINE)
        
        # Convert bold text
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        
        # Convert bullet points
        text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        
        # Wrap consecutive <li> items in <ul>
        text = re.sub(r'(<li>.*?</li>(?:\s*<li>.*?</li>)*)', r'<ul style="margin: 10px 0;">\1</ul>', text, flags=re.DOTALL)
        
        # Convert line breaks
        text = text.replace('\n\n', '</p><p style="margin: 15px 0;">')
        text = text.replace('\n', '<br>')
        
        # Wrap in paragraphs
        if not text.startswith('<'):
            text = f'<p style="margin: 15px 0;">{text}</p>'
        
        return text

    def send_reply(self, to_email: str, subject: str, content: str, original_msg_id: str = None):
        """Send reply email with analysis results using HTML formatting"""
        try:
            server = self.connect_smtp()
            
            # Create HTML formatted content
            html_content = self.markdown_to_html(content)
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                    h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 30px; }}
                    h3 {{ color: #34495e; margin-top: 25px; }}
                    strong {{ color: #2c3e50; }}
                    ul {{ padding-left: 20px; }}
                    li {{ margin: 5px 0; }}
                    .transcript {{ background-color: #f8f9fa; padding: 20px; border-left: 4px solid #3498db; margin-top: 30px; }}
                    .separator {{ border-top: 3px solid #3498db; margin: 30px 0; padding-top: 20px; }}
                    pre {{ white-space: pre-wrap; font-family: Arial, sans-serif; font-size: 14px; line-height: 1.4; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = f"Re: {subject}" if not subject.startswith("Re:") else subject
            
            if original_msg_id:
                msg['In-Reply-To'] = original_msg_id
                msg['References'] = original_msg_id
            
            # Attach both plain text and HTML versions
            msg.attach(MIMEText(content, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            server.sendmail(self.email_address, to_email, msg.as_string())
            server.quit()
            
            print(f"HTML-formatted reply sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send reply: {e}")
            return False
    
    def process_emails(self, folder: str = "INBOX", mark_as_read: bool = True):
        """Process unread emails with audio attachments"""
        try:
            mail = self.connect_imap()
            mail.select(folder)
            
            # Search for unread emails only
            status, messages = mail.search(None, 'UNSEEN')
            message_ids = messages[0].split() if status == 'OK' and messages[0] else []
            
            if not message_ids:
                print("No unread emails found.")
                return
            else:
                print(f"Found {len(message_ids)} unread emails")
            
            for msg_id in message_ids:
                try:
                    # Fetch the email
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parse the email
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    sender = email_message['From']
                    subject = email_message['Subject'] or "No Subject"
                    msg_id_header = email_message['Message-ID']
                    
                    print(f"\nProcessing email from {sender}: {subject}")
                    
                    # First, look for links in email content
                    links = self.get_audio_links(email_message)
                    
                    # Then check for small audio attachments as fallback
                    attachments = self.get_audio_attachments(email_message)
                    
                    if not links and not attachments:
                        print("No audio links or attachments found, skipping")
                        continue
                    
                    results = []
                    
                    # Process links first (preferred for large files)
                    for link in links:
                        print(f"Processing link: {link}")
                        
                        try:
                            # Transcribe and analyze directly from link
                            print("Transcribing audio from link...")
                            transcript = transcribe_audio(link)
                            
                            print("Creating financial analysis...")
                            summary = create_financial_summary(transcript)
                            
                            result = f"""
SOURCE: {link}
PROCESSED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{summary}

================================================================================
FULL TRANSCRIPT
================================================================================

{transcript}

================================================================================
"""
                            results.append(result)
                            
                        except Exception as e:
                            print(f"Error processing link {link}: {e}")
                            continue
                    
                    # Process attachments (for smaller files)
                    for filename, content in attachments:
                        print(f"Processing attachment: {filename}")
                        
                        # Save attachment temporarily
                        temp_path = self.save_attachment(filename, content)
                        
                        try:
                            # Transcribe and analyze
                            print("Transcribing audio...")
                            transcript = transcribe_audio(temp_path)
                            
                            print("Creating financial analysis...")
                            summary = create_financial_summary(transcript)
                            
                            result = f"""
FILE: {filename}
PROCESSED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{summary}

================================================================================
FULL TRANSCRIPT
================================================================================

{transcript}

================================================================================
"""
                            results.append(result)
                            
                        finally:
                            # Clean up temp file
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                    
                    if results:
                        # Combine all results
                        combined_results = f"""
Financial Analysis Results
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Original Subject: {subject}

{'='*80}
{'='*80}
""".join(results)
                        
                        # Send reply with results
                        reply_subject = f"Financial Analysis - {subject}"
                        self.send_reply(sender, reply_subject, combined_results, msg_id_header)
                        
                        print(f"Analysis completed and sent back to {sender}")
                    
                    # Mark as read if requested
                    if mark_as_read:
                        mail.store(msg_id, '+FLAGS', '\\Seen')
                
                except Exception as e:
                    print(f"Error processing email {msg_id}: {e}")
                    continue
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"Error processing emails: {e}")

def setup_email_config():
    """Interactive setup for email configuration"""
    print("Email Integration Setup")
    print("=" * 40)
    print()
    
    email_addr = input("Enter your email address: ")
    password = input("Enter your email password (or app password for Gmail): ")
    
    # Create or update .env file
    env_content = []
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if not line.startswith(('EMAIL_ADDRESS=', 'EMAIL_PASSWORD=', 'IMAP_SERVER=', 'SMTP_SERVER=')):
                    env_content.append(line.rstrip())
    
    env_content.extend([
        f"EMAIL_ADDRESS={email_addr}",
        f"EMAIL_PASSWORD={password}",
        "IMAP_SERVER=imap.gmail.com",
        "SMTP_SERVER=smtp.gmail.com"
    ])
    
    with open('.env', 'w') as f:
        f.write('\n'.join(env_content) + '\n')
    
    print()
    print("Email configuration saved to .env file")
    print()
    print("IMPORTANT for Gmail users:")
    print("- Enable 2-factor authentication")
    print("- Create an 'App Password' for this tool")
    print("- Use the app password instead of your regular password")
    print()

def main():
    parser = argparse.ArgumentParser(description="Email-Integrated Financial Transcription Tool")
    parser.add_argument("--setup", action="store_true", help="Set up email configuration")
    parser.add_argument("--folder", default="INBOX", help="Email folder to monitor")
    parser.add_argument("--once", action="store_true", help="Process emails once and exit")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_email_config()
        return
    
    # Check for API key
    if not load_api_key():
        print("Error: OpenAI API key not found")
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    # Check for email configuration
    if not os.getenv("EMAIL_ADDRESS") or not os.getenv("EMAIL_PASSWORD"):
        print("Error: Email configuration not found")
        print("Please run with --setup to configure email settings")
        return
    
    try:
        processor = EmailProcessor()
        
        if args.once:
            print("Processing emails once...")
            processor.process_emails(args.folder)
        else:
            print(f"Starting email monitoring (checking every {args.interval} seconds)")
            print(f"Monitoring folder: {args.folder}")
            print("Press Ctrl+C to stop")
            
            while True:
                try:
                    processor.process_emails(args.folder)
                    print(f"Waiting {args.interval} seconds before next check...")
                    time.sleep(args.interval)
                except KeyboardInterrupt:
                    print("\nStopping email monitoring")
                    break
                except Exception as e:
                    print(f"Error during monitoring: {e}")
                    print(f"Retrying in {args.interval} seconds...")
                    time.sleep(args.interval)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()