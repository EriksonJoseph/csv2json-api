"""
Logging configuration for CSV2JSON API
"""
import logging
import sys
from typing import List

class LoggerFilter(logging.Filter):
    """Filter to show only specific loggers"""
    
    def __init__(self, allowed_loggers: List[str]):
        super().__init__()
        self.allowed_loggers = allowed_loggers
    
    def filter(self, record):
        # Allow the record if its logger name starts with any of the allowed patterns
        return any(record.name.startswith(logger) for logger in self.allowed_loggers)

def setup_specific_logging(allowed_loggers: List[str] = None):
    """
    Setup logging to show only specific loggers
    
    Args:
        allowed_loggers: List of logger names to show (e.g., ['background_worker', 'search'])
                        If None, shows all loggers
    """
    
    # Default loggers if none specified
    if allowed_loggers is None:
        allowed_loggers = ['background_worker', 'search', 'task', 'auth']
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # Add filter for specific loggers
    if allowed_loggers:
        logger_filter = LoggerFilter(allowed_loggers)
        console_handler.addFilter(logger_filter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)
    
    print(f"🔍 Logging configured to show only: {', '.join(allowed_loggers)}")
    return allowed_loggers

def setup_logger_levels(logger_configs: dict):
    """
    Setup individual logger levels
    
    Args:
        logger_configs: Dict of logger_name: level (e.g., {'background_worker': 'DEBUG', 'uvicorn': 'WARNING'})
    """
    for logger_name, level in logger_configs.items():
        logger = logging.getLogger(logger_name)
        level_obj = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(level_obj)
        print(f"📋 Logger '{logger_name}' set to {level.upper()}")

# Predefined logger configurations
LOGGER_PRESETS = {
    "background_only": ["background_worker"],
    "search_only": ["search"],
    "workers": ["background_worker", "search"],
    "api_only": ["uvicorn", "fastapi"],
    "database": ["mongodb", "motor"],
    "auth": ["auth"],
    "all_app": ["background_worker", "search", "task", "auth", "file", "user"],
    "minimal": ["background_worker", "search"],
    "debug": ["background_worker", "search", "task", "auth", "file", "user", "database"]
}

def use_preset(preset_name: str):
    """Use a predefined logger configuration"""
    if preset_name in LOGGER_PRESETS:
        allowed_loggers = LOGGER_PRESETS[preset_name]
        setup_specific_logging(allowed_loggers)
        return allowed_loggers
    else:
        available = ", ".join(LOGGER_PRESETS.keys())
        print(f"❌ Unknown preset '{preset_name}'. Available: {available}")
        return None