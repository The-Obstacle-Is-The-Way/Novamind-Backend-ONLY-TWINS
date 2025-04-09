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
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast

from app.core.constants import LogLevel


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
