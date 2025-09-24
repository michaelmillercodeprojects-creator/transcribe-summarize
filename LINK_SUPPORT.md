# 🔗 File Sharing Link Support

The Financial Transcription Suite now supports processing large audio/video files through sharing links instead of requiring file uploads or email attachments.

## 📋 Supported Platforms

### ✅ **Fully Supported**
- **Dropbox** - `https://dropbox.com/s/...` or `https://dropbox.com/sh/...`
- **YouTube** - `https://youtube.com/watch?v=...` or `https://youtu.be/...`
- **Zoom Recordings** - `https://zoom.us/rec/...`

### 🔄 **Partial Support** (depends on link format)
- **Google Drive** - `https://drive.google.com/file/d/.../view`
- **OneDrive** - Direct download links
- **Box.com** - Shared file links
- **WeTransfer** - Download links

## 💡 How to Use

### Command Line
```bash
# Dropbox link
python transcribe_financial.py --input "https://dropbox.com/s/abc123/meeting.mp3?dl=0"

# Google Drive link  
python transcribe_financial.py --input "https://drive.google.com/file/d/1abc123xyz/view"

# Zoom recording
python transcribe_financial.py --input "https://zoom.us/rec/share/abc123..."

# With email results
python transcribe_financial.py --input "https://dropbox.com/s/abc123/call.mp3" --email "you@email.com"
```

### Email Integration
Simply **paste the sharing link in your email** and send it to your configured email address:

```
Subject: Transcribe this call

Hi, please analyze this recording:
https://dropbox.com/s/abc123def/quarterly_call.mp3

Thanks!
```

The tool will:
1. Extract the link from your email
2. Download and process the file
3. Reply with the financial analysis

## 🛠️ Link Conversion

The tool automatically converts sharing links to direct download URLs:

| Platform | Original Link | Converted To |
|----------|---------------|--------------|
| Dropbox | `?dl=0` | `?dl=1` (direct download) |
| Google Drive | `/view` | `/uc?export=download&id=...` |
| Zoom | Recording URL | Processed with yt-dlp |

## ⚡ Performance Benefits

**Large File Handling:**
- No file size limits (unlike email attachments)
- Progressive download with progress indication
- Automatic cleanup of temporary files
- Works with files several GB in size

**Email Integration:**
- No more "attachment too large" errors  
- Simply paste a link in email
- Works with corporate file sharing systems
- Maintains audit trail through email

## 🔍 Usage Examples

### 1. **Board Meeting Recording (2 hours)**
```bash
python transcribe_financial.py --input "https://dropbox.com/s/xyz789/board_meeting_q4.mp4"
```

### 2. **Earnings Call via Email**
Email content:
```
Please analyze: https://drive.google.com/file/d/1a2b3c4d5e6f/view
Focus on guidance and margin commentary.
```

### 3. **Zoom Recording Processing**
```bash  
python transcribe_financial.py --input "https://zoom.us/rec/share/conference_call_123" --email "team@company.com"
```

## 🚨 Tips for Best Results

### **Dropbox**
- Use share links ending in `?dl=0` - tool will convert automatically
- Public folder links work best
- Private links require appropriate permissions

### **Google Drive**  
- Use "Anyone with the link can view" permissions
- File must be less than 100MB for direct download
- Larger files may require alternative methods

### **Zoom**
- Recording must be accessible without password
- Cloud recordings work better than local uploads
- Some corporate Zoom accounts may block external access

### **General**
- Test links in a browser first to ensure accessibility
- For very large files (>1GB), consider using Dropbox or dedicated hosting
- Corporate networks may block some sharing domains

## 🔧 Troubleshooting

**"Failed to download file"**
- Check if link is publicly accessible
- Try opening the link in an incognito browser window  
- Ensure link hasn't expired

**"No audio found"**
- Some video files may need audio extraction
- Tool supports most common formats (MP3, MP4, WAV, M4A)
- Try converting to MP3 before sharing if issues persist

**Email links not detected**
- Ensure link is on its own line or properly formatted
- Links in HTML emails sometimes need manual copying
- Plain text emails work most reliably