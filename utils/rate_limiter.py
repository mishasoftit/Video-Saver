"""
Rate limiting functionality for the Telegram Video Downloader Bot
"""

import time
import logging
from collections import defaultdict
from typing import Tuple

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter to prevent abuse and manage download limits"""
    
    def __init__(self, max_requests: int = 5, time_window: int = 3600):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed per time window
            time_window: Time window in seconds (default: 1 hour)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
        logger.info(f"Rate limiter initialized: {max_requests} requests per {time_window} seconds")
    
    def is_allowed(self, user_id: int) -> Tuple[bool, int]:
        """
        Check if user is allowed to make a request
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Tuple of (is_allowed, reset_time_minutes)
        """
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests outside the time window
        user_requests[:] = [req_time for req_time in user_requests 
                           if now - req_time < self.time_window]
        
        # Check if user has exceeded the limit
        if len(user_requests) >= self.max_requests:
            # Calculate when the oldest request will expire
            oldest_request = min(user_requests)
            reset_time_seconds = int(oldest_request + self.time_window - now)
            reset_time_minutes = max(1, reset_time_seconds // 60)
            
            logger.warning(f"Rate limit exceeded for user {user_id}. Reset in {reset_time_minutes} minutes")
            return False, reset_time_minutes
        
        # Add current request
        user_requests.append(now)
        logger.debug(f"Request allowed for user {user_id}. Count: {len(user_requests)}/{self.max_requests}")
        return True, 0
    
    def get_remaining_requests(self, user_id: int) -> int:
        """Get number of remaining requests for user"""
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        user_requests[:] = [req_time for req_time in user_requests 
                           if now - req_time < self.time_window]
        
        return max(0, self.max_requests - len(user_requests))
    
    def get_reset_time(self, user_id: int) -> int:
        """Get time until rate limit resets for user (in minutes)"""
        now = time.time()
        user_requests = self.requests[user_id]
        
        if not user_requests:
            return 0
        
        # Remove old requests
        user_requests[:] = [req_time for req_time in user_requests 
                           if now - req_time < self.time_window]
        
        if len(user_requests) < self.max_requests:
            return 0
        
        oldest_request = min(user_requests)
        reset_time_seconds = int(oldest_request + self.time_window - now)
        return max(1, reset_time_seconds // 60)
    
    def reset_user_limit(self, user_id: int) -> None:
        """Reset rate limit for a specific user (admin function)"""
        if user_id in self.requests:
            del self.requests[user_id]
            logger.info(f"Rate limit reset for user {user_id}")
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        now = time.time()
        active_users = 0
        total_requests = 0
        
        for user_id, user_requests in self.requests.items():
            # Clean old requests
            user_requests[:] = [req_time for req_time in user_requests 
                               if now - req_time < self.time_window]
            
            if user_requests:
                active_users += 1
                total_requests += len(user_requests)
        
        return {
            'active_users': active_users,
            'total_requests': total_requests,
            'max_requests_per_user': self.max_requests,
            'time_window_hours': self.time_window / 3600
        }
    
    def cleanup_old_entries(self) -> None:
        """Clean up old entries to prevent memory leaks"""
        now = time.time()
        users_to_remove = []
        
        for user_id, user_requests in self.requests.items():
            # Remove old requests
            user_requests[:] = [req_time for req_time in user_requests 
                               if now - req_time < self.time_window]
            
            # If no recent requests, mark user for removal
            if not user_requests:
                users_to_remove.append(user_id)
        
        # Remove users with no recent requests
        for user_id in users_to_remove:
            del self.requests[user_id]
        
        if users_to_remove:
            logger.debug(f"Cleaned up {len(users_to_remove)} inactive users from rate limiter")

# Global rate limiter instance
rate_limiter = RateLimiter()