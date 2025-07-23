"""
Logging configuration and utilities for tarsy.
"""

import logging
import logging.config
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOGS_DIR / "sre_agent.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": LOGS_DIR / "sre_agent_errors.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "llm_communications": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOGS_DIR / "llm_communications.log",
            "maxBytes": 52428800,  # 50MB (larger because of prompt/response content)
            "backupCount": 10,
        },
        "mcp_communications": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOGS_DIR / "mcp_communications.log",
            "maxBytes": 52428800,  # 50MB (larger because of tool output content)
            "backupCount": 10,
        },
    },
    "loggers": {
        "sre_agent": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "sre_agent.mcp": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "sre_agent.llm": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "sre_agent.services": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "sre_agent.llm.communications": {
            "level": "DEBUG",
            "handlers": ["llm_communications"],
            "propagate": False,
        },
        "sre_agent.mcp.communications": {
            "level": "DEBUG",
            "handlers": ["mcp_communications"],
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup logging configuration for the application.
    
    Args:
        log_level: The log level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Update log level in config
    LOGGING_CONFIG["handlers"]["console"]["level"] = log_level.upper()
    
    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The name of the logger, typically the module name
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Ensure the name starts with our application prefix
    if not name.startswith("sre_agent"):
        name = f"sre_agent.{name}"
    
    return logging.getLogger(name)


def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        module_name: The module name (e.g., __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    if module_name.startswith("app."):
        module_name = module_name[4:]  # Remove 'app.' prefix
    
    return get_logger(module_name) 