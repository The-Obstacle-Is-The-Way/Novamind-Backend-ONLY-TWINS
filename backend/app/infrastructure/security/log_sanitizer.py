# -*- coding: utf-8 -*-
"""
Log Sanitizer and Formatter for HIPAA Compliance.

This module provides infrastructure components (Formatter, Handler)
that integrate with Python's logging system to sanitize PHI using
the core PHISanitizer service.
"""

import logging
import functools
from typing import Any, Dict, Optional, Union, List, Tuple, Set, Callable

# Import the core SSOT sanitizer
from app.core.security.phi_sanitizer import PHISanitizer

# Configuration dataclass (Simplified for infrastructure layer)
from dataclasses import dataclass

@dataclass
class LogSanitizerConfig:
    """Basic configuration for enabling/disabling sanitization at the infrastructure level."""
    enabled: bool = True
    # Add other infrastructure-specific logging configs if needed.

class LogSanitizer:
    """
    Infrastructure wrapper for the core PHISanitizer.
    Delegates sanitization tasks to PHISanitizer.
    """
    def __init__(self, config: Optional[LogSanitizerConfig] = None):
        """Initialize the LogSanitizer."""
        self.config = config or LogSanitizerConfig()
        # Instantiate the core sanitizer which holds the actual logic
        # Made this a class attribute to ensure single instance for consistency
        # if LogSanitizer itself is instantiated multiple times by the logger.
        # Alternatively, could use dependency injection if a shared instance is managed elsewhere.
        self._core_sanitizer = PHISanitizer() 

    def sanitize(self, data: Any) -> Any:
        """Sanitize data using the core PHISanitizer."""
        if not self.config.enabled:
            return data
        # Delegate directly to the core sanitizer's main entry point
        return self._core_sanitizer.sanitize(data)

    def sanitize_log_record(self, record: logging.LogRecord) -> logging.LogRecord:
        """
        Sanitize a logging.LogRecord object using the core sanitizer.

        Args:
            record: LogRecord to sanitize

        Returns:
            Sanitized LogRecord
        """
        if not self.config.enabled:
            return record

        # Sanitize the message itself
        record.msg = self.sanitize(record.msg)

        # Sanitize args tuple/list/dict using the core recursive sanitizer
        if record.args:
            record.args = self.sanitize(record.args)

        # Sanitize exception info if present
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            # Sanitize the string representation of the exception value
            sanitized_exc_value_str = self.sanitize(str(exc_value))
            try:
                # Attempt to recreate the exception with the sanitized string
                sanitized_exc_value = exc_type(sanitized_exc_value_str)
            except Exception:
                 # Fallback if recreation fails
                sanitized_exc_value = Exception(sanitized_exc_value_str)

            record.exc_info = (exc_type, sanitized_exc_value, exc_traceback)
            if record.exc_text:
                 record.exc_text = self.sanitize(record.exc_text)

        # Sanitize stack info if present
        if hasattr(record, 'stack_info') and record.stack_info:
             record.stack_info = self.sanitize(record.stack_info)

        return record


class PHIFormatter(logging.Formatter):
    """
    Log formatter that uses LogSanitizer (which delegates to core PHISanitizer)
    before formatting log messages.
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        validate: bool = True,
        sanitizer_config: Optional[LogSanitizerConfig] = None # Accept config
    ):
        """Initialize the PHI formatter."""
        super().__init__(fmt, datefmt, style, validate=validate)
        # Instantiate the infrastructure LogSanitizer with optional config
        self.sanitizer = LogSanitizer(config=sanitizer_config)

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record, sanitizing PHI first."""
        # Create a copy to avoid modifying the original record passed to other handlers
        record_copy = logging.makeLogRecord(record.__dict__)
        sanitized_record = self.sanitizer.sanitize_log_record(record_copy)
        return super().format(sanitized_record)


class PHIRedactionHandler(logging.Handler):
    """
    Custom logging handler that ensures PHI is redacted before emission
    by delegating to the configured Formatter (expected to be PHIFormatter).
    """
    def __init__(self, handler: logging.Handler):
        """
        Initialize the handler.

        Args:
            handler: The underlying handler to forward records to.
                     This handler is expected to have a PHIFormatter set.
        """
        super().__init__()
        self.handler = handler
        # Copy level/filters from the wrapped handler
        self.setLevel(handler.level)
        for f in handler.filters:
            self.addFilter(f)
        # Ensure the wrapped handler has a formatter, preferably PHIFormatter
        if not isinstance(self.handler.formatter, PHIFormatter):
             # Log a warning or raise an error if the formatter isn't the expected type
             logging.warning(f"PHIRedactionHandler expects wrapped handler {handler} to use PHIFormatter.")


    def emit(self, record: logging.LogRecord):
        """
        Format the record using the handler's formatter (which should sanitize)
        and then emit using the wrapped handler.
        Note: Sanitization now primarily happens in the PHIFormatter.
              This handler acts more as a structural element if specific
              pre-emission logic were needed beyond formatting.
        """
        try:
            # Formatting (which includes sanitization via PHIFormatter) happens here
            formatted_message = self.format(record)
            # The handler's emit method might re-format if it has its own formatter,
            # but standard handlers use the formatted message.
            # To ensure sanitization happens *once* via the formatter:
            record.message = formatted_message # Store the sanitized, formatted message
            self.handler.emit(record)
        except Exception:
            self.handleError(record)

    def close(self):
        """Close the wrapped handler."""
        self.handler.close()
        super().close()

# Example utility functions (can be moved to a dedicated logging setup module)

def get_sanitized_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Gets a logger configured with PHI sanitization via PHIFormatter."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if already configured
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        # Use PHIFormatter which internally uses LogSanitizer -> PHISanitizer
        formatter = PHIFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Prevent logs from propagating to the root logger if handlers are added here
    logger.propagate = False
    return logger

def sanitize_logs(logger_name: Optional[str] = None):
    """
    Decorator to automatically sanitize arguments passed to a function
    and log entry/exit using a sanitized logger.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            effective_logger_name = logger_name or f"{func.__module__}.{func.__name__}"
            logger = get_sanitized_logger(effective_logger_name)

            # Use the core sanitizer directly for logging args/results
            core_sanitizer = PHISanitizer()
            sanitized_args = core_sanitizer.sanitize(args)
            sanitized_kwargs = core_sanitizer.sanitize(kwargs)

            logger.debug(f"Entering '{func.__name__}' with args: {sanitized_args}, kwargs: {sanitized_kwargs}")
            try:
                result = func(*args, **kwargs)
                sanitized_result = core_sanitizer.sanitize(result)
                logger.debug(f"Exiting '{func.__name__}' with result: {sanitized_result}")
                return result
            except Exception as e:
                sanitized_exception = core_sanitizer.sanitize(e)
                logger.exception(f"Exception in '{func.__name__}': {sanitized_exception}")
                raise
        return wrapper
    return decorator
