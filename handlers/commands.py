"""
Command handlers for the Telegram Video Downloader Bot
"""

import logging
import re
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from services.validator import validator
from utils.messages import MessageTemplates
from utils.keyboards import create_content_type_keyboard, create_main_menu_keyboard
from utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# URL pattern for detecting video URLs
URL_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"Start command from user {user.id} ({user.username})")
    
    welcome_text = MessageTemplates.welcome_message()
    keyboard = create_main_menu_keyboard()
    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    user = update.effective_user
    logger.info(f"Help command from user {user.id} ({user.username})")
    
    help_text = MessageTemplates.help_message()
    await update.message.reply_text(help_text, parse_mode='HTML')

async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /download command"""
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Download command from user {user_id} ({user.username})")
    
    # Check rate limit but don't consume it yet
    remaining = rate_limiter.get_remaining_requests(user_id)
    if remaining <= 0:
        reset_time = rate_limiter.get_reset_time(user_id)
        rate_limit_text = MessageTemplates.rate_limit_message(reset_time)
        await update.message.reply_text(rate_limit_text, parse_mode='HTML')
        return
    
    # Check if URL is provided
    if not context.args:
        invalid_url_text = MessageTemplates.invalid_url_message()
        await update.message.reply_text(invalid_url_text, parse_mode='HTML')
        return
    
    url = context.args[0]
    logger.info(f"Processing URL: {url}")
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        MessageTemplates.processing_url(),
        parse_mode='HTML'
    )
    
    try:
        # Validate URL format
        is_valid, message = validator.validate_format(url)
        if not is_valid:
            await processing_msg.edit_text(message, parse_mode='HTML')
            return
        
        # Extract video information
        video_info = await validator.extract_info(url)
        
        # Store URL in user data for callback handlers
        context.user_data['current_url'] = url
        context.user_data['video_info'] = video_info
        
        # Create content type selection keyboard
        keyboard = create_content_type_keyboard(url)
        
        # Update message with video info and content type selection
        content_selection_text = MessageTemplates.content_type_selection(video_info)
        await processing_msg.edit_text(
            content_selection_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        logger.info(f"Successfully processed URL for user {user_id}: {video_info['title']}")
        
    except ValueError as e:
        # Handle validation/extraction errors
        error_message = str(e)
        await processing_msg.edit_text(error_message, parse_mode='HTML')
        logger.warning(f"URL processing failed for user {user_id}: {error_message}")
        
    except Exception as e:
        # Handle unexpected errors
        error_message = f"❌ An unexpected error occurred. Please try again later."
        await processing_msg.edit_text(error_message, parse_mode='HTML')
        logger.error(f"Unexpected error in download command for user {user_id}: {e}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command (admin only)"""
    user = update.effective_user
    user_id = user.id
    
    # Simple admin check (you can implement proper admin system)
    # For now, just log the request
    logger.info(f"Stats command from user {user_id} ({user.username})")
    
    try:
        # Get rate limiter stats
        stats = rate_limiter.get_stats()
        
        stats_text = (
            f"📊 <b>Bot Statistics</b>\n\n"
            f"👥 Active users: {stats['active_users']}\n"
            f"📥 Total requests: {stats['total_requests']}\n"
            f"⏱️ Time window: {stats['time_window_hours']:.1f} hours\n"
            f"🔢 Max requests per user: {stats['max_requests_per_user']}\n"
        )
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Stats command error: {e}")
        await update.message.reply_text(
            "❌ Failed to retrieve statistics.",
            parse_mode='HTML'
        )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command"""
    user = update.effective_user
    logger.info(f"Cancel command from user {user.id} ({user.username})")
    
    # Clear user data
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ <b>Operation cancelled.</b>\n\nYou can start a new download with /download",
        parse_mode='HTML'
    )

async def url_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages containing URLs"""
    user = update.effective_user
    user_id = user.id
    message_text = update.message.text
    
    logger.info(f"URL message from user {user_id} ({user.username}): {message_text}")
    
    # Extract URL from message
    urls = URL_PATTERN.findall(message_text)
    if not urls:
        # If no URL found, show help message
        help_text = MessageTemplates.no_url_found_message()
        keyboard = create_main_menu_keyboard()
        await update.message.reply_text(
            help_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    url = urls[0]  # Use the first URL found
    
    # Check rate limit but don't consume it yet
    remaining = rate_limiter.get_remaining_requests(user_id)
    if remaining <= 0:
        reset_time = rate_limiter.get_reset_time(user_id)
        rate_limit_text = MessageTemplates.rate_limit_message(reset_time)
        await update.message.reply_text(rate_limit_text, parse_mode='HTML')
        return
    
    # Delete the user's message to reduce clutter
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete user message: {e}")
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        MessageTemplates.processing_url(),
        parse_mode='HTML'
    )
    
    try:
        # Validate URL format
        is_valid, message = validator.validate_format(url)
        if not is_valid:
            await processing_msg.edit_text(message, parse_mode='HTML')
            return
        
        # Extract video information
        video_info = await validator.extract_info(url)
        
        # Store URL in user data for callback handlers
        context.user_data['current_url'] = url
        context.user_data['video_info'] = video_info
        
        # Create content type selection keyboard
        keyboard = create_content_type_keyboard(url)
        
        # Update message with video info and content type selection
        content_selection_text = MessageTemplates.content_type_selection(video_info)
        await processing_msg.edit_text(
            content_selection_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        logger.info(f"Successfully processed URL for user {user_id}: {video_info['title']}")
        
    except ValueError as e:
        # Handle validation/extraction errors
        error_message = str(e)
        await processing_msg.edit_text(error_message, parse_mode='HTML')
        logger.warning(f"URL processing failed for user {user_id}: {error_message}")
        
    except Exception as e:
        # Handle unexpected errors
        error_message = f"❌ An unexpected error occurred. Please try again later."
        await processing_msg.edit_text(error_message, parse_mode='HTML')
        logger.error(f"Unexpected error in URL handler for user {user_id}: {e}")

def setup_command_handlers(application) -> None:
    """Set up all command handlers"""
    logger.info("Setting up command handlers")
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("download", download_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Add URL message handler (for messages containing URLs)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(URL_PATTERN),
        url_message_handler
    ))
    
    logger.info("Command handlers set up successfully")