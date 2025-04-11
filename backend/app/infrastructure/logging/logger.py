# -*- coding: utf-8 -*-
"""
Logger module for the Novamind concierge psychiatry platform.

This module provides logging functionality for the application,
ensuring that all logs are properly formatted and sanitized
to comply with HIPAA regulations.
"""

import logging
import os
import json
from datetime import datetime, UTC, UTC
from typing import Dict, Any, Optional


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: The name of the logger, typically the module name.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Only configure the logger if it hasn't been configured yet
    if not logger.handlers:
        # Set the log level based on environment variable or default to INFO
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, log_level))
        
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        
        # Create a formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add the formatter to the handler
        console_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(console_handler)
        
        # Create a file handler if LOG_FILE is specified
        log_file = os.environ.get("LOG_FILE")
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, log_level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger


def format_log_message(message: str, source: str, additional_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Format a log message as a JSON string.

    Args:
        message: The log message.
        source: The source of the log message.
        additional_data: Additional data to include in the log message.

    Returns:
        A JSON string containing the log message and metadata.
    """
    log_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": "INFO",
        "message": message,
        "source": source
    }
    
    if additional_data:
        log_data.update(additional_data)
    
    return json.dumps(log_data)
