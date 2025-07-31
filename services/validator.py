"""
URL validation and video information extraction service
"""

import re
import logging
import yt_dlp
from urllib.parse import urlparse
from typing import Dict, Tuple, Optional
from utils.helpers import get_platform_from_url, format_error_message

logger = logging.getLogger(__name__)

class URLValidator:
    """URL validation and video information extraction"""
    
    def __init__(self):
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        logger.info("URL validator initialized")
    
    def validate_format(self, url: str) -> Tuple[bool, str]:
        """
        Validate URL format
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not url:
            return False, "❌ No URL provided"
        
        if not self.url_pattern.match(url):
            return False, "❌ Invalid URL format. Please provide a valid video URL."
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "❌ Invalid URL structure."
            
            logger.debug(f"URL format validation passed for: {url}")
            return True, "✅ URL format is valid"
            
        except Exception as e:
            logger.error(f"URL parsing error: {e}")
            return False, "❌ Unable to parse URL."
    
    async def extract_info(self, url: str) -> Dict:
        """
        Extract video information without downloading
        
        Args:
            url: Video URL
            
        Returns:
            Dictionary with video information
            
        Raises:
            ValueError: If extraction fails
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
        }
        
        try:
            logger.info(f"Extracting info for URL: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Extract relevant information
                video_info = {
                    'title': self._clean_title(info.get('title', 'Unknown')),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'platform': info.get('extractor', get_platform_from_url(url)),
                    'thumbnail': info.get('thumbnail'),
                    'filesize': info.get('filesize', 0),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date'),
                    'description': info.get('description', '')[:200] if info.get('description') else '',
                    'url': url
                }
                
                logger.info(f"Successfully extracted info for: {video_info['title']}")
                return video_info
                
        except Exception as e:
            platform = get_platform_from_url(url)
            error_msg = format_error_message(e, platform)
            logger.error(f"Failed to extract info for {url}: {e}")
            raise ValueError(error_msg)
    
    def _clean_title(self, title: str) -> str:
        """Clean and truncate video title"""
        if not title:
            return "Unknown"
        
        # Remove or replace problematic characters
        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        
        # Truncate if too long
        if len(title) > 100:
            title = title[:97] + "..."
        
        return title.strip()
    
    def is_supported_platform(self, url: str) -> bool:
        """
        Check if the platform is supported by yt-dlp
        
        Args:
            url: URL to check
            
        Returns:
            True if platform is supported
        """
        try:
            # Try to extract info without downloading
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)
                return True
                
        except Exception as e:
            logger.warning(f"Platform not supported for {url}: {e}")
            return False
    
    def get_available_formats(self, url: str) -> Optional[Dict]:
        """
        Get available formats for a video
        
        Args:
            url: Video URL
            
        Returns:
            Dictionary with available formats or None if failed
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'listformats': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                formats = info.get('formats', [])
                available_formats = {
                    'video_formats': [],
                    'audio_formats': [],
                    'best_video': None,
                    'best_audio': None
                }
                
                for fmt in formats:
                    if fmt.get('vcodec') != 'none':  # Has video
                        available_formats['video_formats'].append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'resolution': fmt.get('resolution'),
                            'filesize': fmt.get('filesize'),
                        })
                    
                    if fmt.get('acodec') != 'none':  # Has audio
                        available_formats['audio_formats'].append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'abr': fmt.get('abr'),  # Audio bitrate
                            'filesize': fmt.get('filesize'),
                        })
                
                return available_formats
                
        except Exception as e:
            logger.error(f"Failed to get formats for {url}: {e}")
            return None
    
    def validate_and_extract(self, url: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate URL and extract info in one step
        
        Args:
            url: URL to validate and extract info from
            
        Returns:
            Tuple of (is_valid, message, video_info)
        """
        # First validate format
        is_valid, message = self.validate_format(url)
        if not is_valid:
            return False, message, None
        
        # Then extract info
        try:
            import asyncio
            video_info = asyncio.run(self.extract_info(url))
            return True, "✅ Video info extracted successfully", video_info
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            error_msg = format_error_message(e, get_platform_from_url(url))
            return False, error_msg, None

# Global validator instance
validator = URLValidator()