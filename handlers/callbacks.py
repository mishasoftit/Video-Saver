"""
Callback handlers for inline keyboards
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from services.downloader import downloader, ProgressTracker, FileUploader
from utils.keyboards import create_quality_keyboard, create_content_type_keyboard
from utils.messages import MessageTemplates

logger = logging.getLogger(__name__)

async def content_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle content type selection (video/audio)"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Content type callback from user {user_id}: {query.data}")
    
    try:
        # Parse callback data
        callback_data = query.data
        parts = callback_data.split('_')
        
        if len(parts) != 3 or parts[0] != 'type':
            await query.edit_message_text("❌ Invalid selection.")
            return
        
        content_type = parts[1]  # 'video' or 'audio'
        url_hash = parts[2]
        
        # Get stored video info
        video_info = context.user_data.get('video_info')
        current_url = context.user_data.get('current_url')
        
        if not video_info or not current_url:
            await query.edit_message_text(
                "❌ Session expired. Please use /download again.",
                parse_mode='HTML'
            )
            return
        
        # Verify URL hash matches
        if str(hash(current_url) % 10000) != url_hash:
            await query.edit_message_text(
                "❌ Invalid session. Please use /download again.",
                parse_mode='HTML'
            )
            return
        
        # Store selected content type
        context.user_data['content_type'] = content_type
        
        # Create quality selection keyboard
        keyboard = create_quality_keyboard(content_type, current_url)
        
        # Update message with quality selection
        quality_selection_text = MessageTemplates.quality_selection(content_type, video_info)
        await query.edit_message_text(
            quality_selection_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        logger.info(f"Content type selected by user {user_id}: {content_type}")
        
    except Exception as e:
        logger.error(f"Content type callback error for user {user_id}: {e}")
        await query.edit_message_text(
            "❌ An error occurred. Please try again with /download",
            parse_mode='HTML'
        )

async def quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quality/format selection"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Quality callback from user {user_id}: {query.data}")
    
    try:
        # Parse callback data
        callback_data = query.data
        parts = callback_data.split('_')
        
        if len(parts) != 4 or parts[0] != 'quality':
            await query.edit_message_text("❌ Invalid selection.")
            return
        
        content_type = parts[1]  # 'video' or 'audio'
        quality = parts[2]       # quality/format key
        url_hash = parts[3]
        
        # Get stored data
        video_info = context.user_data.get('video_info')
        current_url = context.user_data.get('current_url')
        stored_content_type = context.user_data.get('content_type')
        
        if not all([video_info, current_url, stored_content_type]):
            await query.edit_message_text(
                "❌ Session expired. Please use /download again.",
                parse_mode='HTML'
            )
            return
        
        # Verify data consistency
        if (str(hash(current_url) % 10000) != url_hash or 
            content_type != stored_content_type):
            await query.edit_message_text(
                "❌ Invalid session. Please use /download again.",
                parse_mode='HTML'
            )
            return
        
        # Start download process
        await start_download(query, current_url, content_type, quality, video_info, context)
        
    except Exception as e:
        logger.error(f"Quality callback error for user {user_id}: {e}")
        await query.edit_message_text(
            "❌ An error occurred during download. Please try again.",
            parse_mode='HTML'
        )

async def back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle back button"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Back callback from user {user_id}: {query.data}")
    
    try:
        # Parse callback data
        callback_data = query.data
        parts = callback_data.split('_')
        
        if len(parts) != 3 or parts[0] != 'back' or parts[1] != 'type':
            await query.edit_message_text("❌ Invalid selection.")
            return
        
        url_hash = parts[2]
        
        # Get stored data
        video_info = context.user_data.get('video_info')
        current_url = context.user_data.get('current_url')
        
        if not video_info or not current_url:
            await query.edit_message_text(
                "❌ Session expired. Please use /download again.",
                parse_mode='HTML'
            )
            return
        
        # Verify URL hash
        if str(hash(current_url) % 10000) != url_hash:
            await query.edit_message_text(
                "❌ Invalid session. Please use /download again.",
                parse_mode='HTML'
            )
            return
        
        # Clear content type selection
        context.user_data.pop('content_type', None)
        
        # Show content type selection again
        keyboard = create_content_type_keyboard(current_url)
        content_selection_text = MessageTemplates.content_type_selection(video_info)
        
        await query.edit_message_text(
            content_selection_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        logger.info(f"User {user_id} went back to content type selection")
        
    except Exception as e:
        logger.error(f"Back callback error for user {user_id}: {e}")
        await query.edit_message_text(
            "❌ An error occurred. Please try again with /download",
            parse_mode='HTML'
        )

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancel button"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Cancel callback from user {user_id}")
    
    # Clear user data
    context.user_data.clear()
    
    await query.edit_message_text(
        "❌ <b>Download cancelled.</b>\n\nYou can start a new download with /download",
        parse_mode='HTML'
    )

async def start_download(query, url: str, content_type: str, quality: str, 
                        video_info: dict, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the download process"""
    user_id = query.from_user.id
    
    logger.info(f"Starting {content_type} download for user {user_id}: {quality}")
    
    try:
        # Update message to show download starting
        download_starting_text = MessageTemplates.download_starting(content_type, quality)
        await query.edit_message_text(download_starting_text, parse_mode='HTML')
        
        # Create progress tracker
        progress_tracker = ProgressTracker(query.message, context.bot)
        
        # Start download
        result = await downloader.download_content(
            url=url,
            content_type=content_type,
            quality=quality,
            progress_callback=progress_tracker.progress_hook
        )
        
        # Upload to Telegram
        caption = f"🎬 {result['title']}\n👤 {result['uploader']}"
        if len(caption) > 1024:  # Telegram caption limit
            caption = caption[:1021] + "..."
        
        await FileUploader.upload_to_telegram(
            bot=context.bot,
            chat_id=query.message.chat_id,
            file_path=result['filename'],
            content_type=content_type,
            caption=caption
        )
        
        # Send completion message
        completion_text = MessageTemplates.download_complete(
            filename=result['title'],
            filesize=result['filesize'],
            content_type=content_type
        )
        
        await query.edit_message_text(completion_text, parse_mode='HTML')
        
        # Clear user data
        context.user_data.clear()
        
        logger.info(f"Successfully completed {content_type} download for user {user_id}")
        
    except ValueError as e:
        # Handle expected errors
        error_message = str(e)
        await query.edit_message_text(f"❌ {error_message}", parse_mode='HTML')
        logger.warning(f"Download failed for user {user_id}: {error_message}")
        
    except Exception as e:
        # Handle unexpected errors
        error_message = "❌ Download failed due to an unexpected error. Please try again."
        await query.edit_message_text(error_message, parse_mode='HTML')
        logger.error(f"Unexpected download error for user {user_id}: {e}")

def setup_callback_handlers(application) -> None:
    """Set up all callback handlers"""
    logger.info("Setting up callback handlers")
    
    # Add callback handlers with pattern matching
    application.add_handler(CallbackQueryHandler(
        content_type_callback, 
        pattern=r'^type_(video|audio)_\d+$'
    ))
    
    application.add_handler(CallbackQueryHandler(
        quality_callback, 
        pattern=r'^quality_(video|audio)_\w+_\d+$'
    ))
    
    application.add_handler(CallbackQueryHandler(
        back_callback, 
        pattern=r'^back_type_\d+$'
    ))
    
    application.add_handler(CallbackQueryHandler(
        cancel_callback, 
        pattern=r'^cancel$'
    ))
    
    logger.info("Callback handlers set up successfully")