"""
Logging configuration for the evaluation framework.
Sets up both console and file logging with appropriate formatting.
"""

import logging
import os
from pathlib import Path
from datetime import datetime


def setup_evaluation_logging(log_level: str = None, log_to_file: bool = True, log_dir: Path = None):
    """
    Configure logging for evaluation runs.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR). 
                  If None, uses LOG_LEVEL env var or defaults to INFO.
        log_to_file: Whether to also log to a file.
        log_dir: Directory to write log file to. If None, uses default logs directory.
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    
    # Console handler (simple format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (detailed format)
    if log_to_file:
        # Use provided log_dir or default to evaluation/logs directory
        if log_dir is None:
            # Use evaluation/logs directory for evaluation-specific logs
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        else:
            # If specific log_dir provided, use it directly
            log_file = log_dir / "evaluation.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Log the log file location
        root_logger.info(f"Logging to file: {log_file}")
    
    # Set specific loggers to appropriate levels
    # Suppress verbose HTTP and connection logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.INFO)
    
    # Suppress Snowflake connector verbose logs
    logging.getLogger("snowflake.connector").setLevel(logging.WARNING)
    logging.getLogger("snowflake.connector.network").setLevel(logging.ERROR)
    logging.getLogger("snowflake.connector.connection").setLevel(logging.WARNING)
    logging.getLogger("snowflake.connector.cursor").setLevel(logging.WARNING)
    logging.getLogger("snowflake.connector.telemetry").setLevel(logging.ERROR)
    
    # Suppress urllib3 connection pool logs
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    
    # Suppress other verbose libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("concurrent.futures").setLevel(logging.WARNING)
    
    return root_logger


def get_evaluation_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for evaluation components.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_evaluation_log_level(level: str):
    """
    Change the logging level for evaluation components at runtime.
    
    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR)
    
    Usage:
        set_evaluation_log_level("DEBUG")  # Enable detailed logging
        set_evaluation_log_level("INFO")   # Normal logging
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Update root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Update console handler level
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(numeric_level)
    
    logging.info(f"🔧 Evaluation logging level changed to {level.upper()}")


def toggle_debug_mode():
    """
    Toggle between DEBUG and INFO logging levels.
    
    Usage:
        toggle_debug_mode()  # Switch to DEBUG if currently INFO, or vice versa
    """
    root_logger = logging.getLogger()
    current_level = root_logger.level
    
    if current_level == logging.DEBUG:
        set_evaluation_log_level("INFO")
        print("📊 Switched to INFO logging (concise)")
    else:
        set_evaluation_log_level("DEBUG")
        print("🔍 Switched to DEBUG logging (detailed)")