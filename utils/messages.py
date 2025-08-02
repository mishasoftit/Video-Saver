"""
Message templates and formatting for the Telegram Video Downloader Bot
"""

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if not seconds:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def format_filesize(bytes_size: int) -> str:
    """Format file size in bytes to human readable format"""
    if not bytes_size:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

class MessageTemplates:
    @staticmethod
    def welcome_message() -> str:
        return (
            "🎬 <b>Video Downloader Bot</b>\n\n"
            "I can download videos from YouTube, TikTok, Instagram, Twitter, and many other platforms!\n\n"
            "🚀 <b>How to use:</b>\n"
            "• Just send me any video URL\n"
            "• Or use the buttons below\n\n"
            "✨ <b>No commands needed!</b> Simply paste a link and I'll handle the rest!"
        )
    
    @staticmethod
    def help_message() -> str:
        return (
            "🆘 <b>Help - Video Downloader Bot</b>\n\n"
            "🚀 <b>How to Download:</b>\n"
            "1. Send me any video URL\n"
            "2. Choose Video or Audio\n"
            "3. Select quality/format\n"
            "4. Wait for your download!\n\n"
            "🌐 <b>Supported Platforms:</b>\n"
            "• YouTube (youtube.com, youtu.be)\n"
            "• TikTok (tiktok.com)\n"
            "• Instagram (instagram.com)\n"
            "• Twitter (twitter.com, x.com)\n"
            "• And 1000+ more platforms!\n\n"
            "🎬 <b>Video Quality Options:</b>\n"
            "• 📱 720p - Fast download, smaller file\n"
            "• 🎬 1080p - Balanced quality and size\n"
            "• ⭐ Best - Highest available quality\n\n"
            "🎵 <b>Audio Format Options:</b>\n"
            "• 🎵 MP3 - Universal compatibility\n"
            "• 🎼 M4A - High quality, smaller size\n"
            "• 🎶 OGG - Open source format\n\n"
            "⚠️ <b>Limitations:</b>\n"
            "• Maximum file size: 50MB\n"
            "• Rate limit: 5 downloads per hour\n"
            "• Private content not supported\n\n"
            "💡 <b>Tip:</b> Just paste any video link - no commands needed!"
        )
    
    @staticmethod
    def content_type_selection(video_info: dict) -> str:
        platform_emoji = {
            'youtube': '📺',
            'tiktok': '🎵',
            'instagram': '📸',
            'twitter': '🐦',
        }.get(video_info['platform'].lower(), '🎬')
        
        return (
            f"🎯 <b>Choose download type for:</b>\n"
            f"{platform_emoji} <b>{video_info['platform']}</b> - {video_info['title'][:50]}...\n\n"
            f"👤 <b>Uploader:</b> {video_info['uploader']}\n"
            f"⏱️ <b>Duration:</b> {format_duration(video_info['duration'])}\n\n"
            "What would you like to download?"
        )
    
    @staticmethod
    def quality_selection(content_type: str, video_info: dict) -> str:
        platform_emoji = {
            'youtube': '📺',
            'tiktok': '🎵',
            'instagram': '📸',
            'twitter': '🐦',
        }.get(video_info['platform'].lower(), '🎬')
        
        type_text = "🎬 Video Quality" if content_type == 'video' else "🎵 Audio Format"
        
        return (
            f"🎯 <b>Choose {type_text.lower()} for:</b>\n"
            f"{platform_emoji} <b>{video_info['platform']}</b> - {video_info['title'][:50]}...\n\n"
            f"👤 <b>Uploader:</b> {video_info['uploader']}\n"
            f"⏱️ <b>Duration:</b> {format_duration(video_info['duration'])}\n\n"
            f"Select your preferred {type_text.lower()}:"
        )
    
    @staticmethod
    def download_starting(content_type: str, quality: str) -> str:
        type_emoji = "🎬" if content_type == 'video' else "🎵"
        action = "Downloading" if content_type == 'video' else "Extracting audio"
        
        return f"{type_emoji} <b>{action}...</b>\n📊 Preparing download..."
    
    @staticmethod
    def download_progress(percent: float, speed: str = "N/A") -> str:
        # Create progress bar
        filled = int(percent / 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        return (
            f"⬇️ <b>Downloading...</b>\n"
            f"📊 Progress: [{bar}] {percent:.1f}%\n"
            f"🚀 Speed: {speed}"
        )
    
    @staticmethod
    def upload_starting() -> str:
        return "📤 <b>Uploading to Telegram...</b>\nPlease wait..."
    
    @staticmethod
    def download_complete(filename: str, filesize: int, content_type: str) -> str:
        type_emoji = "🎬" if content_type == 'video' else "🎵"
        type_text = "Video" if content_type == 'video' else "Audio"
        
        return (
            f"✅ <b>{type_text} Download Complete!</b>\n\n"
            f"📁 <b>File:</b> {filename}\n"
            f"📊 <b>Size:</b> {format_filesize(filesize)}\n\n"
            f"{type_emoji} Enjoy your {type_text.lower()}!"
        )
    
    @staticmethod
    def processing_url() -> str:
        return "🔍 <b>Analyzing video...</b>\nPlease wait..."
    
    @staticmethod
    def rate_limit_message(reset_time: int) -> str:
        return (
            f"⏰ <b>Rate Limit Exceeded</b>\n\n"
            f"You've reached the maximum of 5 downloads per hour.\n"
            f"⏳ Try again in {reset_time} minutes."
        )
    
    @staticmethod
    def invalid_url_message() -> str:
        return (
            "❌ <b>Invalid URL</b>\n\n"
            "Please provide a valid video URL.\n\n"
            "📝 <b>Usage:</b> /download &lt;video_url&gt;\n"
            "💡 <b>Example:</b> /download https://youtube.com/watch?v=..."
        )
    
    @staticmethod
    def no_url_found_message() -> str:
        return (
            "🤔 <b>No video URL found!</b>\n\n"
            "Please send me a valid video URL from any supported platform.\n\n"
            "💡 <b>Examples:</b>\n"
            "• https://youtube.com/watch?v=...\n"
            "• https://tiktok.com/@user/video/...\n"
            "• https://instagram.com/p/...\n\n"
            "Or use the buttons below to get started!"
        )
    
    @staticmethod
    def download_prompt_message() -> str:
        return (
            "📥 <b>Ready to Download!</b>\n\n"
            "Send me any video URL and I'll help you download it.\n\n"
            "🌐 <b>Supported platforms:</b> YouTube, TikTok, Instagram, Twitter, and 1000+ more!\n\n"
            "Just paste the link - no commands needed! ✨"
        )
    
    @staticmethod
    def main_menu_message() -> str:
        return (
            "🏠 <b>Main Menu</b>\n\n"
            "What would you like to do?\n\n"
            "💡 <b>Tip:</b> You can also just send me any video URL directly!"
        )