"""
Logging configuration for the backend services.
Sets up both console and file logging with appropriate formatting.
"""

import logging
import os
from pathlib import Path
from datetime import datetime


def setup_backend_logging(log_level: str = None, service_name: str = "backend"):
    """
    Configure logging for backend services.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR). 
                  If None, uses LOG_LEVEL env var or defaults to INFO.
        service_name: Name of the service for log file naming.
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
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
    # Create logs directory in backend
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"{service_name}_{timestamp}.log"
    
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
    
    # Suppress uvicorn verbose logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    # Suppress other verbose libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("concurrent.futures").setLevel(logging.WARNING)
    
    return root_logger


def get_backend_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for backend components.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)