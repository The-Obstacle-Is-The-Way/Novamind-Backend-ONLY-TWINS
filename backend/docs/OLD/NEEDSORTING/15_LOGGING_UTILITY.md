# NOVAMIND: HIPAA-Compliant Logging Utility

## 1. Overview

The Logging Utility is a critical component of the NOVAMIND platform that ensures all system logs are HIPAA-compliant by automatically redacting Protected Health Information (PHI) while maintaining comprehensive audit trails for security and compliance purposes.

## 2. Key Features

- **PHI Redaction**: Automatically identifies and redacts sensitive patient information from logs
- **Audit Trails**: Maintains secure, tamper-evident logs for compliance requirements
- **Performance Metrics**: Tracks function execution times for performance optimization
- **Log Levels**: Provides granular control over logging verbosity
- **Structured Logging**: Outputs logs in structured JSON format for easy parsing and analysis

## 3. Implementation

### 3.1 Core Logger Implementation

```python
# app/utils/logging.py
import json
import logging
import re
import time
import uuid
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

import structlog
from structlog.processors import JSONRenderer

# PHI patterns to detect and redact
PHI_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'phone': r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b',
    'mrn': r'\bMRN-\d{6,10}\b',
    'address': r'\b\d{1,5}\s[A-Za-z0-9\s]{1,20}(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|court|ct|lane|ln|way|parkway|pkwy)\b',
    'dob': r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
    'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
}

class HIPAACompliantLogger:
    """
    HIPAA-compliant logger that automatically redacts PHI from log messages
    while maintaining comprehensive audit trails.
    """
    
    def __init__(self, name: str, log_level: int = logging.INFO):
        """
        Initialize the HIPAA-compliant logger.
        
        Args:
            name: Logger name (typically __name__ of the calling module)
            log_level: Logging level (default: INFO)
        """
        self.logger = structlog.get_logger(name)
        self.log_level = log_level
        
        # Configure structured logging
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                self._redact_phi,
                JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def _redact_phi(self, _, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact PHI from log messages and structured data.
        
        Args:
            event_dict: Structured log event dictionary
            
        Returns:
            Dict with PHI redacted
        """
        # Process the event message
        if 'event' in event_dict and isinstance(event_dict['event'], str):
            event_dict['event'] = self._redact_text(event_dict['event'])
        
        # Process any additional fields that might contain PHI
        for key, value in event_dict.items():
            if isinstance(value, str) and key not in ['level', 'timestamp', 'logger']:
                event_dict[key] = self._redact_text(value)
            elif isinstance(value, dict):
                event_dict[key] = self._redact_dict(value)
            elif isinstance(value, list):
                event_dict[key] = self._redact_list(value)
                
        return event_dict
    
    def _redact_text(self, text: str) -> str:
        """
        Redact PHI from text using regex patterns.
        
        Args:
            text: Text that may contain PHI
            
        Returns:
            Text with PHI redacted
        """
        for phi_type, pattern in PHI_PATTERNS.items():
            text = re.sub(pattern, f"[REDACTED-{phi_type.upper()}]", text)
        return text
    
    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively redact PHI from dictionary values.
        
        Args:
            data: Dictionary that may contain PHI
            
        Returns:
            Dictionary with PHI redacted
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._redact_text(value)
            elif isinstance(value, dict):
                result[key] = self._redact_dict(value)
            elif isinstance(value, list):
                result[key] = self._redact_list(value)
            else:
                result[key] = value
        return result
    
    def _redact_list(self, data: List[Any]) -> List[Any]:
        """
        Recursively redact PHI from list items.
        
        Args:
            data: List that may contain PHI
            
        Returns:
            List with PHI redacted
        """
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(self._redact_text(item))
            elif isinstance(item, dict):
                result.append(self._redact_dict(item))
            elif isinstance(item, list):
                result.append(self._redact_list(item))
            else:
                result.append(item)
        return result
    
    def info(self, message: str, **kwargs):
        """Log an info message with optional structured data."""
        self.logger.info(message, **kwargs)
    
    def error(self, message: str, exc_info=None, **kwargs):
        """Log an error message with optional exception info and structured data."""
        self.logger.error(message, exc_info=exc_info, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message with optional structured data."""
        self.logger.warning(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log a debug message with optional structured data."""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, exc_info=None, **kwargs):
        """Log a critical message with optional exception info and structured data."""
        self.logger.critical(message, exc_info=exc_info, **kwargs)

# Decorator for logging function calls with execution time
def log_execution(logger: HIPAACompliantLogger):
    """
    Decorator to log function execution with timing information.
    
    Args:
        logger: HIPAA-compliant logger instance
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            request_id = str(uuid.uuid4())
            
            # Log function entry
            logger.info(
                f"Function {func_name} started",
                request_id=request_id,
                function=func_name
            )
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful execution
                logger.info(
                    f"Function {func_name} completed",
                    request_id=request_id,
                    function=func_name,
                    execution_time_ms=round(execution_time * 1000, 2)
                )
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log exception
                logger.error(
                    f"Function {func_name} failed",
                    request_id=request_id,
                    function=func_name,
                    execution_time_ms=round(execution_time * 1000, 2),
                    error=str(e),
                    exc_info=True
                )
                
                raise
        
        return wrapper
    
    return decorator

# Helper function to get a logger instance
def get_logger(name: str) -> HIPAACompliantLogger:
    """
    Get a HIPAA-compliant logger instance.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        HIPAACompliantLogger instance
    """
    return HIPAACompliantLogger(name)
```

### 3.2 Audit Logger Implementation

```python
# app/utils/audit_logger.py
import datetime
import json
from typing import Any, Dict, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)

class AuditLogger:
    """
    HIPAA-compliant audit logger for tracking security-relevant events.
    Maintains a comprehensive audit trail for compliance requirements.
    """
    
    @staticmethod
    def log_access(
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log a resource access event.
        
        Args:
            user_id: ID of the user performing the action
            resource_type: Type of resource being accessed (e.g., 'patient', 'appointment')
            resource_id: ID of the resource being accessed
            action: Action being performed (e.g., 'read', 'update', 'delete')
            success: Whether the access was successful
            details: Additional details about the access
        """
        audit_data = {
            "event_type": "resource_access",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "success": success,
            "details": details or {}
        }
        
        logger.info(
            f"AUDIT: User {user_id} {action} {resource_type} {resource_id}",
            **audit_data
        )
    
    @staticmethod
    def log_authentication(
        user_id: str,
        auth_type: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log an authentication event.
        
        Args:
            user_id: ID of the user being authenticated
            auth_type: Type of authentication (e.g., 'login', 'token_refresh')
            success: Whether the authentication was successful
            ip_address: IP address of the client
            user_agent: User agent of the client
            details: Additional details about the authentication
        """
        audit_data = {
            "event_type": "authentication",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "user_id": user_id,
            "auth_type": auth_type,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {}
        }
        
        logger.info(
            f"AUDIT: User {user_id} authentication ({auth_type}): {'Success' if success else 'Failure'}",
            **audit_data
        )
    
    @staticmethod
    def log_data_modification(
        user_id: str,
        resource_type: str,
        resource_id: str,
        modification_type: str,
        fields_modified: Optional[Dict[str, Any]] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log a data modification event.
        
        Args:
            user_id: ID of the user performing the modification
            resource_type: Type of resource being modified
            resource_id: ID of the resource being modified
            modification_type: Type of modification (e.g., 'create', 'update', 'delete')
            fields_modified: Fields that were modified (for updates)
            success: Whether the modification was successful
            details: Additional details about the modification
        """
        audit_data = {
            "event_type": "data_modification",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "modification_type": modification_type,
            "fields_modified": fields_modified or {},
            "success": success,
            "details": details or {}
        }
        
        logger.info(
            f"AUDIT: User {user_id} {modification_type} {resource_type} {resource_id}",
            **audit_data
        )
```

## 4. Usage Examples

### 4.1 Basic Logging

```python
from app.utils.logging import get_logger

# Get a logger instance
logger = get_logger(__name__)

# Log messages at different levels
logger.info("Processing patient request", patient_id="12345")
logger.error("Failed to update patient record", patient_id="12345", error="Database connection failed")
logger.warning("Patient record missing recommended fields", patient_id="12345", missing_fields=["allergies", "medications"])
logger.debug("Detailed processing information", patient_id="12345", processing_steps=["validation", "normalization"])
```

### 4.2 Function Execution Logging

```python
from app.utils.logging import get_logger, log_execution

logger = get_logger(__name__)

@log_execution(logger)
def process_patient_data(patient_id: str, data: dict):
    """
    Process patient data with automatic logging of execution time.
    
    Args:
        patient_id: Patient identifier
        data: Patient data to process
    """
    # Function implementation...
    return processed_data
```

### 4.3 Audit Logging

```python
from app.utils.audit_logger import AuditLogger

# Log patient record access
AuditLogger.log_access(
    user_id="doctor_123",
    resource_type="patient",
    resource_id="patient_456",
    action="view",
    success=True,
    details={"reason": "scheduled appointment"}
)

# Log authentication event
AuditLogger.log_authentication(
    user_id="doctor_123",
    auth_type="login",
    success=True,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    details={"mfa_used": True}
)

# Log data modification
AuditLogger.log_data_modification(
    user_id="doctor_123",
    resource_type="patient",
    resource_id="patient_456",
    modification_type="update",
    fields_modified={"allergies": ["penicillin", "sulfa"], "medications": ["lisinopril"]},
    success=True
)
```

## 5. Best Practices

1. **Always Use the HIPAA-Compliant Logger**: Never use Python's built-in logging or print statements for production code.

2. **Include Contextual Information**: Add relevant context to log messages using structured fields.

3. **Avoid Logging PHI Directly**: While the logger will attempt to redact PHI, avoid explicitly logging sensitive information.

4. **Log Authentication Events**: Always log login attempts, token refreshes, and logouts.

5. **Log Access to PHI**: Record all access to protected health information for audit purposes.

6. **Log Data Modifications**: Track all changes to patient data with before/after values when appropriate.

7. **Use Appropriate Log Levels**:
   - DEBUG: Detailed information for debugging
   - INFO: Confirmation that things are working as expected
   - WARNING: Indication that something unexpected happened
   - ERROR: Due to a more serious problem, the software couldn't perform some function
   - CRITICAL: A serious error indicating that the program itself may be unable to continue running

8. **Regular Audit Log Reviews**: Implement a process for regular review of audit logs.

## 6. HIPAA Compliance Considerations

- **Automatic PHI Redaction**: The logging utility automatically redacts common PHI patterns, but developers should still be cautious about what they log.

- **Log Storage**: Logs containing PHI (even redacted) must be stored securely with appropriate access controls.

- **Log Retention**: Maintain logs for at least 6 years as required by HIPAA.

- **Access Controls**: Restrict access to logs containing PHI to authorized personnel only.

- **Transmission Security**: Ensure logs are transmitted securely when moved between systems.

## 7. Integration with Monitoring Systems

The structured JSON logs produced by the HIPAA-compliant logger can be easily integrated with monitoring systems:

- **CloudWatch**: For AWS-based deployments
- **ELK Stack**: For on-premises or custom cloud deployments
- **Datadog**: For comprehensive application performance monitoring
- **Prometheus/Grafana**: For metrics visualization and alerting

## 8. Conclusion

The HIPAA-compliant logging utility is a critical component of the NOVAMIND platform's security and compliance infrastructure. By automatically redacting PHI while maintaining comprehensive audit trails, it helps ensure that the platform meets HIPAA requirements while providing valuable insights for debugging, performance optimization, and security monitoring.
