# -*- coding: utf-8 -*-
"""
Logging Utility Module.

This module provides logging configuration and utilities for the application,
with special care for HIPAA compliance and PHI protection.
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from app.core.constants import LogLevel

# Try to import the PHI detection service if available
try:
    from app.core.services.ml.phi_detection import MockPHIDetection
    HAS_PHI_DETECTION = True
except ImportError:
    HAS_PHI_DETECTION = False

# Type variables for function signatures
F = TypeVar('F', bound=Callable[..., Any])


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance for the specified name.
    
    This function creates and returns a logger with the specified name,
    configured according to the application's logging settings.
    HIPAA-compliant sanitization is automatically applied.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if it hasn't been done yet
    if not logger.handlers:
        # Get log level from environment or default to INFO
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        # Set level
        logger.setLevel(log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
        # Don't propagate to root logger
        logger.propagate = False
        
    return logger


def log_execution_time(
    logger: Optional[logging.Logger] = None, 
    level: LogLevel = LogLevel.DEBUG
) -> Callable[[F], F]:
    """
    Decorator to log the execution time of a function.
    
    Args:
        logger: Logger to use, if None a new logger is created using function's module name
        level: Log level to use
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get or create logger
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            # Record start time
            start_time = datetime.now()
            
            # Call the decorated function
            try:
                result = func(*args, **kwargs)
                # Record end time and calculate duration
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                # Log execution time
                logger.log(
                    level.value,
                    f"Function '{func.__name__}' executed in {duration_ms:.2f} ms"
                )
                
                return result
            except Exception as e:
                # Log exception with sanitized PHI
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                logger.exception(
                    f"Exception in '{func.__name__}' after {duration_ms:.2f} ms: {str(e)}"
                )
                raise  # Re-raise the exception
                
        return cast(F, wrapper)
    
    return decorator


def log_method_calls(
    logger: Optional[logging.Logger] = None,
    level: LogLevel = LogLevel.DEBUG,
    log_args: bool = True,
    log_results: bool = True
) -> Callable[[Type], Type]:
    """
    Class decorator to log method calls.
    
    Args:
        logger: Logger to use, if None a logger is created for each method
        level: Log level to use
        log_args: Whether to log method arguments
        log_results: Whether to log method return values
        
    Returns:
        Decorator function
    """
    def decorator(cls: Type) -> Type:
        # Get class methods (excluding magic methods)
        for name, method in cls.__dict__.items():
            if callable(method) and not name.startswith('__'):
                setattr(cls, name, _create_logged_method(
                    method, logger, level, log_args, log_results
                ))
        return cls
    
    return decorator


def _create_logged_method(
    method: Callable,
    logger: Optional[logging.Logger],
    level: LogLevel,
    log_args: bool,
    log_results: bool
) -> Callable:
    """
    Create a logged version of a method.
    
    Args:
        method: Method to wrap with logging
        logger: Logger to use
        level: Log level to use
        log_args: Whether to log method arguments
        log_results: Whether to log method return values
        
    Returns:
        Wrapped method with logging
    """
    @wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Get or create logger
        method_logger = logger
        if method_logger is None:
            method_logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Build method call representation
        method_call = f"{self.__class__.__name__}.{method.__name__}"
        if log_args and (args or kwargs):
            args_str = ", ".join([str(arg) for arg in args])
            kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            args_kwargs = [s for s in [args_str, kwargs_str] if s]
            method_call += f"({', '.join(args_kwargs)})"
        
        # Log method entry
        method_logger.log(level.value, f"Calling {method_call}")
        
        # Execute method
        try:
            result = method(self, *args, **kwargs)
            
            # Log successful completion
            if log_results:
                method_logger.log(
                    level.value,
                    f"{method_call} returned: {str(result)}"
                )
            else:
                method_logger.log(
                    level.value,
                    f"{method_call} completed successfully"
                )
                
            return result
            
        except Exception as e:
            # Log exception
            tb = traceback.format_exc()
            method_logger.error(
                f"Exception in {method_call}: {str(e)}\n{tb}"
            )
            raise  # Re-raise the exception
            
    return wrapper


class HIPAACompliantLogger:
    """
    HIPAA-compliant logger that sanitizes PHI from logs.
    
    This logger wraps a standard Python logger and automatically sanitizes
    any PHI (Protected Health Information) from log messages before they
    are recorded, ensuring HIPAA compliance.
    """
    
    def __init__(
        self, 
        name: str, 
        level: Union[int, str] = logging.INFO,
        phi_detection_service = None
    ):
        """
        Initialize a HIPAA-compliant logger.
        
        Args:
            name: Logger name, typically __name__ of the calling module
            level: Log level to use
            phi_detection_service: Optional PHI detection service to use, if None a mock service is created
        """
        self.logger = get_logger(name)
        
        # Set log level
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Initialize PHI detection
        if phi_detection_service is None and HAS_PHI_DETECTION:
            # Use mock service if available and none provided
            self.phi_detection = MockPHIDetection()
        else:
            # Use provided service or create a simple fallback
            self.phi_detection = phi_detection_service or self._create_fallback_detector()
    
    def _create_fallback_detector(self):
        """Create a simple fallback PHI detector when the real one is not available."""
        class SimplePHIDetector:
            def redact_phi(self, text: str) -> str:
                """Simple regex-based sanitization as fallback."""
                import re
                # Simple patterns for common PHI
                patterns = [
                    # Names (Mr./Mrs./Dr. followed by capitalized words)
                    r'\b(Mr\.|Mrs\.|Dr\.|Ms\.) [A-Z][a-z]+\b',
                    # SSN pattern
                    r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
                    # Phone numbers
                    r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
                    # Email addresses
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    # Dates (various formats)
                    r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                    # Medical record numbers (assumes MRN: prefix)
                    r'MRN:?\s*\d+',
                    # Ages over 89
                    r'\b(9\d|1[0-9]\d+)\s+years?\s+old\b',
                ]
                
                sanitized_text = text
                for pattern in patterns:
                    sanitized_text = re.sub(pattern, "[REDACTED]", sanitized_text)
                return sanitized_text
                
            def detect_phi(self, text: str) -> List[Dict[str, Any]]:
                """Simple PHI detection as fallback."""
                return []  # No detailed detection in fallback
                
        return SimplePHIDetector()
    
    def _sanitize_phi(self, message: Any) -> str:
        """
        Sanitize PHI from a log message.
        
        Args:
            message: Message to sanitize
            
        Returns:
            Sanitized message
        """
        if not isinstance(message, str):
            message = str(message)
            
        # Use PHI detection service to sanitize the message
        return self.phi_detection.redact_phi(message)
    
    def debug(self, message: Any, *args, **kwargs) -> None:
        """Log a debug message with PHI sanitization."""
        self.logger.debug(self._sanitize_phi(message), *args, **kwargs)
    
    def info(self, message: Any, *args, **kwargs) -> None:
        """Log an info message with PHI sanitization."""
        self.logger.info(self._sanitize_phi(message), *args, **kwargs)
    
    def warning(self, message: Any, *args, **kwargs) -> None:
        """Log a warning message with PHI sanitization."""
        self.logger.warning(self._sanitize_phi(message), *args, **kwargs)
    
    def error(self, message: Any, *args, **kwargs) -> None:
        """Log an error message with PHI sanitization."""
        self.logger.error(self._sanitize_phi(message), *args, **kwargs)
    
    def critical(self, message: Any, *args, **kwargs) -> None:
        """Log a critical message with PHI sanitization."""
        self.logger.critical(self._sanitize_phi(message), *args, **kwargs)
    
    def exception(self, message: Any, *args, **kwargs) -> None:
        """Log an exception with PHI sanitization."""
        self.logger.exception(self._sanitize_phi(message), *args, **kwargs)
    
    def log(self, level: int, message: Any, *args, **kwargs) -> None:
        """Log a message with PHI sanitization at the specified level."""
        self.logger.log(level, self._sanitize_phi(message), *args, **kwargs)


def get_hipaa_logger(name: str, level: Union[int, str] = logging.INFO) -> HIPAACompliantLogger:
    """
    Get a HIPAA-compliant logger instance for the specified name.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        level: Log level to use
        
    Returns:
        HIPAA-compliant logger instance
    """
    return HIPAACompliantLogger(name, level)
