"""
Video and audio download service using yt-dlp
"""

import os
import asyncio
import logging
import yt_dlp
from typing import Dict, Optional, Callable
from config import Config, DOWNLOAD_OPTIONS
from utils.helpers import cleanup_file, get_file_size, is_file_too_large, sanitize_filename

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Track download progress and update user"""
    
    def __init__(self, message, bot, update_interval: int = 10):
        self.message = message
        self.bot = bot
        self.last_update = 0
        self.update_interval = update_interval  # Update every N percent
        
    async def progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0%').strip('%')
                percent = float(percent_str)
                
                # Update every N% to avoid rate limits
                if percent - self.last_update >= self.update_interval:
                    speed = d.get('_speed_str', 'N/A')
                    
                    # Create progress bar
                    filled = int(percent / 10)
                    bar = "█" * filled + "░" * (10 - filled)
                    
                    text = (
                        f"⬇️ <b>Downloading...</b>\n"
                        f"📊 Progress: [{bar}] {percent:.1f}%\n"
                        f"🚀 Speed: {speed}"
                    )
                    
                    await self.bot.edit_message_text(
                        chat_id=self.message.chat_id,
                        message_id=self.message.message_id,
                        text=text,
                        parse_mode='HTML'
                    )
                    
                    self.last_update = percent
                    
            except Exception as e:
                logger.warning(f"Progress update failed: {e}")
        
        elif d['status'] == 'finished':
            try:
                text = "✅ <b>Download completed!</b>\n📤 Uploading to Telegram..."
                await self.bot.edit_message_text(
                    chat_id=self.message.chat_id,
                    message_id=self.message.message_id,
                    text=text,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.warning(f"Completion update failed: {e}")

class EnhancedVideoDownloader:
    """Enhanced video and audio downloader with progress tracking"""
    
    def __init__(self):
        self.active_downloads = {}
        logger.info("Enhanced video downloader initialized")
    
    async def download_content(self, url: str, content_type: str, quality: str, 
                             progress_callback: Optional[Callable] = None) -> Dict:
        """
        Download video or extract audio based on content type
        
        Args:
            url: Video URL
            content_type: 'video' or 'audio'
            quality: Quality/format key
            progress_callback: Optional progress callback
            
        Returns:
            Dictionary with download result information
            
        Raises:
            ValueError: If download fails or already in progress
        """
        download_id = hash(f"{url}_{content_type}_{quality}")
        
        if download_id in self.active_downloads:
            raise ValueError("Download already in progress for this content")
        
        self.active_downloads[download_id] = True
        
        try:
            logger.info(f"Starting {content_type} download: {quality} from {url}")
            
            # Get download options
            if content_type not in DOWNLOAD_OPTIONS or quality not in DOWNLOAD_OPTIONS[content_type]:
                raise ValueError(f"Invalid {content_type} quality: {quality}")
            
            options = DOWNLOAD_OPTIONS[content_type][quality]
            
            # Configure yt-dlp options
            ydl_opts = Config.YT_DLP_OPTIONS.copy()
            ydl_opts['format'] = options['format']
            
            # Add postprocessors for audio
            if content_type == 'audio' and 'postprocessors' in options:
                ydl_opts['postprocessors'] = options['postprocessors']
                ydl_opts['keepvideo'] = False  # Don't keep original video for audio extraction
            
            # Add progress hook if provided
            if progress_callback:
                ydl_opts['progress_hooks'] = [progress_callback]
            
            # Perform download in thread pool to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._download_sync, url, ydl_opts
            )
            
            # Process result
            filename = result['filename']
            
            # For audio, the filename might change after postprocessing
            if content_type == 'audio':
                filename = self._find_audio_file(filename, quality)
            
            # Verify file exists and get size
            if not os.path.exists(filename):
                raise ValueError(f"Downloaded file not found: {filename}")
            
            filesize = get_file_size(filename)
            if filesize == 0:
                raise ValueError("Downloaded file is empty")
            
            # Check file size limit
            if is_file_too_large(filename):
                cleanup_file(filename)
                raise ValueError("File too large for Telegram (>50MB)")
            
            download_result = {
                'filename': filename,
                'title': result['title'],
                'filesize': filesize,
                'content_type': content_type,
                'format': quality,
                'duration': result.get('duration', 0),
                'uploader': result.get('uploader', 'Unknown')
            }
            
            logger.info(f"Successfully downloaded {content_type}: {filename} ({filesize} bytes)")
            return download_result
            
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            raise ValueError(f"Download failed: {str(e)}")
            
        finally:
            self.active_downloads.pop(download_id, None)
    
    def _download_sync(self, url: str, ydl_opts: Dict) -> Dict:
        """Synchronous download function to run in thread pool"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            return {
                'filename': filename,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'filesize': info.get('filesize', 0)
            }
    
    def _find_audio_file(self, base_filename: str, quality: str) -> str:
        """Find the actual audio file after postprocessing"""
        base_path = os.path.splitext(base_filename)[0]
        
        # Map quality to expected extension
        extension_map = {
            'mp3': '.mp3',
            'm4a': '.m4a',
            'ogg': '.ogg'
        }
        
        expected_ext = extension_map.get(quality, '.mp3')
        audio_file = base_path + expected_ext
        
        if os.path.exists(audio_file):
            return audio_file
        
        # Fallback: check for any audio file with the base name
        for ext in ['.mp3', '.m4a', '.ogg', '.wav', '.flac']:
            candidate = base_path + ext
            if os.path.exists(candidate):
                return candidate
        
        # If no audio file found, return original filename
        return base_filename
    
    def is_download_active(self, url: str, content_type: str, quality: str) -> bool:
        """Check if a download is currently active"""
        download_id = hash(f"{url}_{content_type}_{quality}")
        return download_id in self.active_downloads
    
    def get_active_downloads_count(self) -> int:
        """Get number of active downloads"""
        return len(self.active_downloads)
    
    def cancel_download(self, url: str, content_type: str, quality: str) -> bool:
        """Cancel an active download (if possible)"""
        download_id = hash(f"{url}_{content_type}_{quality}")
        if download_id in self.active_downloads:
            # Note: yt-dlp doesn't support cancellation easily
            # This is more of a placeholder for future implementation
            logger.warning(f"Download cancellation requested for {download_id}")
            return True
        return False

class FileUploader:
    """Handle file uploads to Telegram"""
    
    @staticmethod
    async def upload_to_telegram(bot, chat_id: int, file_path: str, 
                                content_type: str, caption: str = None) -> bool:
        """
        Upload file to Telegram
        
        Args:
            bot: Telegram bot instance
            chat_id: Chat ID to send to
            file_path: Path to file to upload
            content_type: 'video' or 'audio'
            caption: Optional caption
            
        Returns:
            True if upload successful
            
        Raises:
            ValueError: If upload fails
        """
        try:
            logger.info(f"Uploading {content_type} file: {file_path}")
            
            # Check file exists and size
            if not os.path.exists(file_path):
                raise ValueError("File not found")
            
            filesize = get_file_size(file_path)
            if filesize == 0:
                raise ValueError("File is empty")
            
            if is_file_too_large(file_path):
                raise ValueError("File too large for Telegram")
            
            # Upload based on content type
            with open(file_path, 'rb') as file:
                if content_type == 'video':
                    await bot.send_video(
                        chat_id=chat_id,
                        video=file,
                        caption=caption,
                        supports_streaming=True,
                        read_timeout=300,
                        write_timeout=300
                    )
                else:  # audio
                    await bot.send_audio(
                        chat_id=chat_id,
                        audio=file,
                        caption=caption,
                        read_timeout=300,
                        write_timeout=300
                    )
            
            logger.info(f"Successfully uploaded {content_type} file")
            return True
            
        except Exception as e:
            logger.error(f"Upload failed for {file_path}: {e}")
            raise ValueError(f"Upload failed: {str(e)}")
        
        finally:
            # Always cleanup the file after upload attempt
            cleanup_file(file_path)

# Global downloader instance
downloader = EnhancedVideoDownloader()