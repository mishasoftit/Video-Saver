"""
Helper functions and utilities for the Telegram Video Downloader Bot
"""

import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def cleanup_file(file_path: str) -> None:
    """Safely remove a file if it exists"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup file {file_path}: {e}")

def get_file_size(file_path: str) -> int:
    """Get file size in bytes, return 0 if file doesn't exist"""
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Failed to get file size for {file_path}: {e}")
    return 0

def is_file_too_large(file_path: str, max_size_mb: int = 50) -> bool:
    """Check if file is too large for Telegram"""
    file_size = get_file_size(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size > max_size_bytes

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:100]  # Limit length

def extract_video_id_from_url(url: str) -> Optional[str]:
    """Extract video ID from URL for caching purposes"""
    try:
        # Simple hash-based ID for any URL
        return str(hash(url) % 1000000)
    except Exception:
        return None

async def run_with_timeout(coro, timeout: int):
    """Run coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout} seconds")

def format_error_message(error: Exception, platform: str = None) -> str:
    """Format error message for user display"""
    error_str = str(error).lower()
    
    # Check for specific error types
    if 'private' in error_str or 'unavailable' in error_str:
        if platform:
            return f"❌ {platform.title()} content unavailable. It might be private or deleted."
        return "❌ Content unavailable. It might be private or deleted."
    
    elif 'network' in error_str or 'connection' in error_str:
        return "❌ Network error. Please check your connection and try again."
    
    elif 'timeout' in error_str:
        return "❌ Download timeout. The content might be too large or server is slow."
    
    elif 'format' in error_str:
        return "❌ Requested format not available. Try a different quality option."
    
    elif 'ffmpeg' in error_str:
        return "❌ Audio processing failed. FFmpeg might not be installed properly."
    
    else:
        return f"❌ Download failed: {str(error)[:100]}..."

def get_platform_from_url(url: str) -> str:
    """Extract platform name from URL"""
    url_lower = url.lower()
    
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'YouTube'
    elif 'tiktok.com' in url_lower:
        return 'TikTok'
    elif 'instagram.com' in url_lower:
        return 'Instagram'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'Twitter'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
        return 'Facebook'
    elif 'vimeo.com' in url_lower:
        return 'Vimeo'
    elif 'dailymotion.com' in url_lower:
        return 'Dailymotion'
    elif 'reddit.com' in url_lower:
        return 'Reddit'
    else:
        return 'Unknown'

def create_progress_bar(percent: float, length: int = 10) -> str:
    """Create a visual progress bar"""
    filled = int(percent / 100 * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

async def safe_delete_message(bot, chat_id: int, message_id: int):
    """Safely delete a message without raising exceptions"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.warning(f"Failed to delete message {message_id}: {e}")

def validate_bot_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    if not token:
        return False
    
    # Basic format check: should be like "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    parts = token.split(':')
    if len(parts) != 2:
        return False
    
    # First part should be numeric (bot ID)
    if not parts[0].isdigit():
        return False
    
    # Second part should be alphanumeric (token)
    if len(parts[1]) < 35:  # Minimum token length
        return False
    
    return True