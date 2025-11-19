"""
Logging utility for consistent logging across app
"""

import logging
from pathlib import Path
from datetime import datetime

class Logger:
    """Centralized logging"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
    
    def debug(self, msg):
        self.logger.debug(f"🔍 {msg}")
    
    def info(self, msg):
        self.logger.info(f"ℹ️  {msg}")
    
    def success(self, msg):
        self.logger.info(f"✅ {msg}")
    
    def warning(self, msg):
        self.logger.warning(f"⚠️  {msg}")
    
    def error(self, msg):
        self.logger.error(f"❌ {msg}")
    
    def critical(self, msg):
        self.logger.critical(f"🔴 {msg}")
