import logging
from datetime import datetime

class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def info(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(f"[{timestamp}] {message}")
    
    def error(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.error(f"[{timestamp}] ERROR: {message}")
    
    def warning(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.warning(f"[{timestamp}] WARNING: {message}")
    
    def success(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(f"[{timestamp}] ✓ {message}")
