# -*- coding: utf-8 -*-
"""
Log Sanitizer and Formatter for HIPAA Compliance.

This module provides infrastructure components (Formatter, Handler)
that integrate with Python's logging system to sanitize PHI using
the core PHIService.
"""

import logging
import functools
from typing import Any, Dict, Optional, Union, List, Tuple, Set, Callable

# Import the NEW core PHI service
# from app.core.security.phi_sanitizer import PHISanitizer # Old import REMOVED
from .phi_service import PHIService, PHIType  # Import the consolidated service and PHIType

# Configuration dataclass (Simplified for infrastructure layer)
from dataclasses import dataclass, field

@dataclass
class LogSanitizerConfig:
    """Configuration for PHI sanitization in logging."""
    enabled: bool = True
    # Define default sensitivity for logging
    default_sensitivity: str = field(default=PHIService.DEFAULT_SENSITIVITY)
    # Custom replacement template for logs (optional)
    replacement_template: Optional[str] = field(default=None) 
    # Add other infrastructure-specific logging configs if needed.

class LogSanitizer:
    """
    Infrastructure wrapper for the core PHIService.
    Delegates sanitization tasks to PHIService.
    """
    # Storage for custom regex patterns for static string sanitization
    _custom_patterns: Dict[str, Any] = {}
    def __init__(self, config: Optional[LogSanitizerConfig] = None):
        """Initialize the LogSanitizer with config and PHIService instance."""
        self.config = config or LogSanitizerConfig()
        # Instantiate the core PHI service 
        # Consider making this injectable if a singleton instance is preferred app-wide
        self._phi_service = PHIService() 

    def sanitize(self, data: Any, sensitivity: Optional[str] = None) -> Any:
        """Sanitize data using the core PHIService, with dict key overrides for names."""
        if not self.config.enabled:
            return data

        # Determine sensitivity and replacement
        effective_sensitivity = sensitivity or self.config.default_sensitivity
        replacement = self.config.replacement_template

        # Delegate to the core service for base sanitization
        sanitized = self._phi_service.sanitize(data,
                                              sensitivity=effective_sensitivity,
                                              replacement=replacement)
        # Override top-level name fields without relying on text context
        if isinstance(data, dict):
            for key in data:
                lower_key = key.lower()
                if lower_key in ("name", "patient_name"):
                    # Replace entire value with redaction marker for NAME
                    sanitized[key] = self._phi_service._get_replacement_value(PHIType.NAME, replacement)
        return sanitized

    def sanitize_log_record(self, record: logging.LogRecord) -> logging.LogRecord:
        """
        Sanitize a logging.LogRecord object using the PHIService.

        Args:
            record: LogRecord to sanitize

        Returns:
            Sanitized LogRecord
        """
        if not self.config.enabled:
            return record

        # Sanitize the message itself (potentially already interpolated)
        # Using default sensitivity for logs unless overridden elsewhere
        record.msg = self.sanitize(record.getMessage())

        # Sanitize args tuple/list/dict using the recursive sanitize method
        if record.args:
            # Ensure args are sanitized *before* formatting happens in super().format
            # Note: Direct sanitization of args might be complex if formatting relies on specific types
            # A safer approach is to sanitize the final formatted message, which format() does.
            # However, if args themselves need sanitization *before* %-style formatting, do it here.
            # For simplicity and safety, we primarily rely on sanitizing the formatted message.
            # If specific args need deep sanitization: record.args = self.sanitize(record.args)
            pass # Relying on sanitizing the final formatted message in PHIFormatter.format

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
                sanitized_exc_value = Exception(f"Sanitized Exception: {sanitized_exc_value_str}")

            record.exc_info = (exc_type, sanitized_exc_value, exc_traceback)
            if record.exc_text:
                 # Sanitize the pre-formatted exception text if available
                 record.exc_text = self.sanitize(record.exc_text)

        # Sanitize stack info if present
        if hasattr(record, 'stack_info') and record.stack_info:
             record.stack_info = self.sanitize(record.stack_info)

        # Clear args after sanitizing the message to prevent double formatting/interpolation issues
        record.args = [] 

        return record

    @classmethod
    def sanitize_string(cls, text: str) -> str:
        """Sanitize a simple string using custom patterns only."""
        result = text
        for name, pattern in cls._custom_patterns.items():
            # Use uppercase pattern name for redaction marker
            result = pattern.sub(lambda m, nm=name: f"[{nm.upper()} REDACTED]", result)
        return result

    @classmethod
    def update_patterns(cls, patterns: Dict[str, Any]) -> None:
        """Add or update custom regex patterns for sanitize_string."""
        cls._custom_patterns.update(patterns)

    @staticmethod
    def sanitize_log_entry(log_entry: str) -> str:
        """Sanitize a raw log entry string using default sanitization."""
        return LogSanitizer().sanitize(log_entry)


class PHIFormatter(logging.Formatter):
    """
    Log formatter that uses LogSanitizer (which delegates to PHIService)
    to sanitize the final formatted log message.
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        validate: bool = True,
        *, # Force keyword arguments for config
        sanitizer_config: Optional[LogSanitizerConfig] = None # Accept config
    ):
        """Initialize the PHI formatter."""
        # Set validate=False if style is '{' or '$' to avoid issues with our redaction format
        should_validate = validate if style == '%' else False
        super().__init__(fmt, datefmt, style, validate=should_validate)
        # Instantiate the infrastructure LogSanitizer with optional config
        self.log_sanitizer = LogSanitizer(config=sanitizer_config)

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record, then sanitize the resulting string."""
        # Let the standard formatter handle initial formatting and interpolation
        formatted_message = super().format(record)
        
        # Sanitize the fully formatted message using LogSanitizer -> PHIService
        # Pass the default sensitivity configured for the logger
        sanitized_message = self.log_sanitizer.sanitize(formatted_message)
        return sanitized_message

    def formatException(self, ei) -> str:
        """Formats and sanitizes the exception part of a log record."""
        s = super().formatException(ei)
        return self.log_sanitizer.sanitize(s)

    def formatStack(self, stack_info: str) -> str:
        """Formats and sanitizes the stack trace part of a log record."""
        s = super().formatStack(stack_info)
        return self.log_sanitizer.sanitize(s)


# PHIRedactionHandler might become less critical if sanitization is robustly handled
# by the PHIFormatter, but kept for structural compatibility or future use.
class PHIRedactionHandler(logging.Handler):
    """
    Custom logging handler wrapper. Ensures the underlying handler uses PHIFormatter.
    (Sanitization is primarily done by the formatter).
    """
    def __init__(self, handler: logging.Handler):
        """
        Initialize the handler.

        Args:
            handler: The underlying handler to forward records to.
                     This handler *must* have a PHIFormatter set.
        """
        super().__init__()
        self.handler = handler
        # Copy level/filters from the wrapped handler
        self.setLevel(handler.level)
        for f in handler.filters:
            self.addFilter(f)
            
        # Explicitly check if the formatter is PHIFormatter
        if not isinstance(self.handler.formatter, PHIFormatter):
             # Raise an error - this setup requires the specific formatter
             raise TypeError(f"Wrapped handler {handler} must use PHIFormatter for PHIRedactionHandler.")

    def emit(self, record: logging.LogRecord):
        """
        Emit a record using the wrapped handler.
        Sanitization is performed by the PHIFormatter during self.format().
        """
        try:
            # Formatting (which includes sanitization) happens implicitly via the handler
            self.handler.handle(record)
        except Exception:
            self.handleError(record)

    def close(self):
        """Close the wrapped handler."""
        self.handler.close()
        super().close()

# --- Utility Functions (Using PHIService) ---

# Store instantiated loggers to avoid duplicate handlers
_loggers: Dict[str, logging.Logger] = {}

def get_sanitized_logger(name: str, level: int = logging.INFO, config: Optional[LogSanitizerConfig] = None) -> logging.Logger:
    """Gets a logger configured with PHI sanitization via PHIFormatter."""
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if logger already has them (e.g., from root config)
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        # Use PHIFormatter with the provided or default config
        formatter = PHIFormatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                 sanitizer_config=config)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Prevent logs from propagating to the root logger if handlers are added here
    logger.propagate = False
    _loggers[name] = logger
    return logger

def sanitize_logs(logger_name: Optional[str] = None, log_level: int = logging.DEBUG, config: Optional[LogSanitizerConfig] = None):
    """
    Decorator to automatically sanitize arguments/return values passed to a function
    and log entry/exit using a sanitized logger.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            effective_logger_name = logger_name or f"{func.__module__}.{func.__name__}"
            logger = get_sanitized_logger(effective_logger_name, level=log_level, config=config)

            # Instantiate the service directly for sanitizing args/return before logging
            # This uses the default service config unless specific one passed via decorator
            phi_service = PHIService() 
            
            try:
                # Sanitize args/kwargs *before* calling the function if needed for logic,
                # but primarily for logging here.
                sanitized_args = phi_service.sanitize(args)
                sanitized_kwargs = phi_service.sanitize(kwargs)
                logger.log(log_level, f"Entering '{func.__name__}' with args: {sanitized_args}, kwargs: {sanitized_kwargs}")
            except Exception as log_e:
                logger.error(f"Error sanitizing/logging entry to '{func.__name__}': {log_e}")
                # Decide whether to proceed or raise based on logging failure policy

            try:
                result = func(*args, **kwargs)
                try:
                     sanitized_result = phi_service.sanitize(result)
                     logger.log(log_level, f"Exiting '{func.__name__}' with result: {sanitized_result}")
                except Exception as log_e:
                     logger.error(f"Error sanitizing/logging result from '{func.__name__}': {log_e}")
                return result
            except Exception as e:
                try:
                    sanitized_exception = phi_service.sanitize(str(e))
                    # Log the sanitized exception string
                    logger.exception(f"Exception in '{func.__name__}': {sanitized_exception}")
                except Exception as log_e:
                    logger.error(f"Error sanitizing/logging exception from '{func.__name__}': {log_e}")
                raise e # Re-raise the original exception
        return wrapper
    return decorator
