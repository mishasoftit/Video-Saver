"""
Inline keyboard layouts for the Telegram Video Downloader Bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import DOWNLOAD_OPTIONS

def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📥 Start Download", callback_data="menu_download")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")],
        [InlineKeyboardButton("📊 My Stats", callback_data="menu_stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_content_type_keyboard(video_url: str) -> InlineKeyboardMarkup:
    """Create keyboard for selecting content type (video/audio)"""
    url_hash = hash(video_url) % 10000
    keyboard = [
        [InlineKeyboardButton("🎬 Video Download", callback_data=f"type_video_{url_hash}")],
        [InlineKeyboardButton("🎵 Audio Only", callback_data=f"type_audio_{url_hash}")],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_quality_keyboard(content_type: str, video_url: str) -> InlineKeyboardMarkup:
    """Create keyboard for quality/format selection based on content type"""
    keyboard = []
    url_hash = hash(video_url) % 10000
    
    options = DOWNLOAD_OPTIONS[content_type]
    
    for quality_key, quality_info in options.items():
        callback_data = f"quality_{content_type}_{quality_key}_{url_hash}"
        button_text = f"{quality_info['emoji']} {quality_info['description']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data=f"back_type_{url_hash}"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_cancel_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with cancel and main menu options"""
    keyboard = [
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_retry_keyboard(video_url: str) -> InlineKeyboardMarkup:
    """Create keyboard with retry option"""
    url_hash = hash(video_url) % 10000
    keyboard = [
        [InlineKeyboardButton("🔄 Try Again", callback_data=f"retry_{url_hash}")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_completion_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard shown after successful download"""
    keyboard = [
        [InlineKeyboardButton("📥 Download Another", callback_data="menu_download")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_help_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for help message"""
    keyboard = [
        [InlineKeyboardButton("📥 Start Download", callback_data="menu_download")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_error_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for error messages"""
    keyboard = [
        [InlineKeyboardButton("🔄 Try Again", callback_data="menu_download")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_stats_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for stats message"""
    keyboard = [
        [InlineKeyboardButton("📥 Start Download", callback_data="menu_download")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu_main")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)