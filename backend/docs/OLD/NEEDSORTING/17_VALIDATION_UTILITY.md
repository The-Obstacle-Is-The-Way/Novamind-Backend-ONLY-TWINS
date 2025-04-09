# NOVAMIND: HIPAA-Compliant Validation Utility

## 1. Overview

The Validation Utility is a critical component of the NOVAMIND platform that ensures data integrity and security by providing comprehensive validation for all user inputs and data processing operations. This utility implements robust validation mechanisms for patient information, enforces data quality standards, and prevents security vulnerabilities such as injection attacks, all while maintaining HIPAA compliance.

## 2. Key Features

- **Comprehensive Data Validation**: Validates all types of patient and clinical data
- **PHI Validation**: Specialized validation for Protected Health Information (PHI)
- **Pydantic Models**: Structured validation using Pydantic models
- **Input Sanitization**: Prevents SQL injection, XSS, and other attacks
- **Custom Validators**: Domain-specific validation rules for medical data

## 3. Implementation

### 3.1 Core Validation Implementation

```python
# app/utils/validation.py
import re
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Tuple, Union

from pydantic import BaseModel, EmailStr, Field, validator

# Regular expression patterns for validating common fields
PATTERNS = {
    'name': r'^[A-Za-z\'\-\. ]+$',
    'phone': r'^\+?[0-9]{1,3}?[-. ]?\(?[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}$',
    'ssn': r'^(?!000|666|9\d{2})(?!00)\d{3}-(?!00)\d{2}-(?!0000)\d{4}$',
    'zip_code': r'^\d{5}(?:-\d{4})?$',
    'address': r'^[A-Za-z0-9\'\-\.\, ]+$',
    'mrn': r'^[A-Z0-9\-]+$',  # Medical Record Number
    'npi': r'^\d{10}$',  # National Provider Identifier
    'icd10': r'^[A-Z]\d{2}(?:\.\d{1,2})?$',  # ICD-10 code
    'cpt': r'^\d{5}$',  # CPT code
    'ndc': r'^\d{4,5}-\d{3,4}-\d{1,2}$',  # National Drug Code
    'date': r'^\d{4}-\d{2}-\d{2}$',  # ISO format date (YYYY-MM-DD)
    'time': r'^\d{2}:\d{2}(:\d{2})?$',  # 24-hour time format (HH:MM or HH:MM:SS)
    'datetime': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$',  # ISO format datetime
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',  # Strong password
    'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    'credit_card': r'^\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}$',
    'url': r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$'
}

class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error for field '{field}': {message}")


class Validator:
    """
    HIPAA-compliant validator for ensuring data integrity and security.
    Provides methods for validating various types of data, including PHI.
    """
    
    @staticmethod
    def validate_pattern(value: str, pattern: str, field_name: str) -> bool:
        """
        Validate a string against a regex pattern.
        
        Args:
            value: String to validate
            pattern: Regex pattern to validate against
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        if not value:
            raise ValidationError(field_name, "Value cannot be empty")
        
        if not re.match(pattern, value):
            raise ValidationError(field_name, f"Invalid format for {field_name}")
        
        return True
    
    @staticmethod
    def validate_name(name: str, field_name: str = "name") -> bool:
        """
        Validate a person's name.
        
        Args:
            name: Name to validate
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        return Validator.validate_pattern(name, PATTERNS['name'], field_name)
    
    @staticmethod
    def validate_email(email: str, field_name: str = "email") -> bool:
        """
        Validate an email address.
        
        Args:
            email: Email to validate
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        return Validator.validate_pattern(email, PATTERNS['email'], field_name)
    
    @staticmethod
    def validate_phone(phone: str, field_name: str = "phone") -> bool:
        """
        Validate a phone number.
        
        Args:
            phone: Phone number to validate
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        return Validator.validate_pattern(phone, PATTERNS['phone'], field_name)
    
    @staticmethod
    def validate_ssn(ssn: str, field_name: str = "ssn") -> bool:
        """
        Validate a Social Security Number.
        
        Args:
            ssn: SSN to validate
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        return Validator.validate_pattern(ssn, PATTERNS['ssn'], field_name)
    
    @staticmethod
    def validate_date(date_str: str, field_name: str = "date") -> bool:
        """
        Validate a date string in ISO format (YYYY-MM-DD).
        
        Args:
            date_str: Date string to validate
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        if not Validator.validate_pattern(date_str, PATTERNS['date'], field_name):
            return False
        
        try:
            year, month, day = map(int, date_str.split('-'))
            date(year, month, day)
            return True
        except ValueError:
            raise ValidationError(field_name, "Invalid date")
    
    @staticmethod
    def validate_datetime(datetime_str: str, field_name: str = "datetime") -> bool:
        """
        Validate a datetime string in ISO format.
        
        Args:
            datetime_str: Datetime string to validate
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        if not Validator.validate_pattern(datetime_str, PATTERNS['datetime'], field_name):
            return False
        
        try:
            datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return True
        except ValueError:
            raise ValidationError(field_name, "Invalid datetime")
    
    @staticmethod
    def validate_password(password: str, field_name: str = "password") -> bool:
        """
        Validate a password for strength requirements.
        
        Args:
            password: Password to validate
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        if len(password) < 8:
            raise ValidationError(field_name, "Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(field_name, "Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(field_name, "Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            raise ValidationError(field_name, "Password must contain at least one digit")
        
        if not re.search(r'[@$!%*?&]', password):
            raise ValidationError(field_name, "Password must contain at least one special character (@$!%*?&)")
        
        return True
    
    @staticmethod
    def validate_credit_card(credit_card: str, field_name: str = "credit_card") -> bool:
        """
        Validate a credit card number using the Luhn algorithm.
        
        Args:
            credit_card: Credit card number to validate
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        # Remove spaces and dashes
        credit_card = credit_card.replace(' ', '').replace('-', '')
        
        if not credit_card.isdigit():
            raise ValidationError(field_name, "Credit card number must contain only digits")
        
        if len(credit_card) < 13 or len(credit_card) > 19:
            raise ValidationError(field_name, "Credit card number must be between 13 and 19 digits")
        
        # Luhn algorithm
        digits = [int(d) for d in credit_card]
        checksum = 0
        
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        
        if checksum % 10 != 0:
            raise ValidationError(field_name, "Invalid credit card number")
        
        return True
    
    @staticmethod
    def validate_icd10(icd10: str, field_name: str = "icd10") -> bool:
        """
        Validate an ICD-10 diagnosis code.
        
        Args:
            icd10: ICD-10 code to validate
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        return Validator.validate_pattern(icd10, PATTERNS['icd10'], field_name)
    
    @staticmethod
    def validate_npi(npi: str, field_name: str = "npi") -> bool:
        """
        Validate a National Provider Identifier.
        
        Args:
            npi: NPI to validate
            field_name: Name of the field being validated
            
        Returns:
            True if valid, raises ValidationError otherwise
        """
        return Validator.validate_pattern(npi, PATTERNS['npi'], field_name)
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """
        Sanitize input to prevent injection attacks.
        
        Args:
            input_str: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\'&;]', '', input_str)
        
        # Prevent SQL injection
        sanitized = sanitized.replace('--', '')
        sanitized = sanitized.replace(';', '')
        sanitized = re.sub(r'\bOR\b', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\bAND\b', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\bUNION\b', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\bSELECT\b', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\bDROP\b', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\bINSERT\b', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\bDELETE\b', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\bUPDATE\b', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def validate_dict(data: Dict[str, Any], validators: Dict[str, Callable[[Any], bool]]) -> Dict[str, str]:
        """
        Validate a dictionary of data using provided validators.
        
        Args:
            data: Dictionary of data to validate
            validators: Dictionary mapping field names to validator functions
            
        Returns:
            Dictionary of validation errors (empty if all valid)
        """
        errors = {}
        
        for field, validator_func in validators.items():
            if field in data:
                try:
                    validator_func(data[field])
                except ValidationError as e:
                    errors[field] = e.message
        
        return errors
```

### 3.2 Pydantic Models Implementation

```python
# app/utils/validation_models.py
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from app.utils.validation import PATTERNS, Validator

class Gender(str, Enum):
    """Enumeration of gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class InsuranceType(str, Enum):
    """Enumeration of insurance types."""
    PRIVATE = "private"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    SELF_PAY = "self_pay"
    OTHER = "other"

class PatientBase(BaseModel):
    """Base model for patient data validation."""
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender
    email: EmailStr
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    ssn: Optional[str] = None
    insurance_type: InsuranceType
    insurance_member_id: Optional[str] = None
    insurance_group_id: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    @validator('first_name', 'last_name', 'emergency_contact_name')
    def validate_name(cls, v, values, **kwargs):
        if v is not None:
            Validator.validate_name(v)
        return v
    
    @validator('phone', 'emergency_contact_phone')
    def validate_phone(cls, v, values, **kwargs):
        if v is not None:
            Validator.validate_phone(v)
        return v
    
    @validator('ssn')
    def validate_ssn(cls, v, values, **kwargs):
        if v is not None:
            Validator.validate_ssn(v)
        return v
    
    @validator('zip_code')
    def validate_zip_code(cls, v, values, **kwargs):
        if not re.match(PATTERNS['zip_code'], v):
            raise ValueError("Invalid ZIP code format")
        return v

class MedicationBase(BaseModel):
    """Base model for medication data validation."""
    name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    prescribing_provider: str
    ndc_code: Optional[str] = None
    
    @validator('ndc_code')
    def validate_ndc(cls, v, values, **kwargs):
        if v is not None and not re.match(PATTERNS['ndc'], v):
            raise ValueError("Invalid NDC code format")
        return v
    
    @validator('end_date')
    def validate_end_date(cls, v, values, **kwargs):
        if v is not None and 'start_date' in values and v < values['start_date']:
            raise ValueError("End date cannot be before start date")
        return v

class DiagnosisBase(BaseModel):
    """Base model for diagnosis data validation."""
    code: str
    description: str
    diagnosis_date: date
    diagnosing_provider: str
    
    @validator('code')
    def validate_icd10(cls, v, values, **kwargs):
        Validator.validate_icd10(v)
        return v

class AppointmentBase(BaseModel):
    """Base model for appointment data validation."""
    patient_id: UUID
    provider_id: UUID
    start_time: datetime
    end_time: datetime
    appointment_type: str
    status: str
    notes: Optional[str] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values, **kwargs):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError("End time must be after start time")
        return v

class ProviderBase(BaseModel):
    """Base model for provider data validation."""
    first_name: str
    last_name: str
    npi: str
    specialization: str
    email: EmailStr
    phone: str
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v, values, **kwargs):
        Validator.validate_name(v)
        return v
    
    @validator('phone')
    def validate_phone(cls, v, values, **kwargs):
        Validator.validate_phone(v)
        return v
    
    @validator('npi')
    def validate_npi(cls, v, values, **kwargs):
        Validator.validate_npi(v)
        return v

class UserBase(BaseModel):
    """Base model for user data validation."""
    email: EmailStr
    password: Optional[str] = None
    first_name: str
    last_name: str
    role: str
    
    @validator('password')
    def validate_password(cls, v, values, **kwargs):
        if v is not None:
            Validator.validate_password(v)
        return v
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v, values, **kwargs):
        Validator.validate_name(v)
        return v

class PaymentBase(BaseModel):
    """Base model for payment data validation."""
    patient_id: UUID
    amount: float
    payment_date: date
    payment_method: str
    transaction_id: str
    description: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v, values, **kwargs):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v
```

## 4. Usage Examples

### 4.1 Basic Validation

```python
from app.utils.validation import Validator, ValidationError

# Validate a patient's name
try:
    Validator.validate_name("John Doe")
    print("Name is valid")
except ValidationError as e:
    print(e)

# Validate an email address
try:
    Validator.validate_email("john.doe@example.com")
    print("Email is valid")
except ValidationError as e:
    print(e)

# Validate a phone number
try:
    Validator.validate_phone("555-123-4567")
    print("Phone number is valid")
except ValidationError as e:
    print(e)

# Validate an SSN
try:
    Validator.validate_ssn("123-45-6789")
    print("SSN is valid")
except ValidationError as e:
    print(e)

# Validate a date
try:
    Validator.validate_date("2023-01-15")
    print("Date is valid")
except ValidationError as e:
    print(e)

# Validate a password
try:
    Validator.validate_password("SecureP@ss123")
    print("Password is valid")
except ValidationError as e:
    print(e)
```

### 4.2 Dictionary Validation

```python
from app.utils.validation import Validator

# Define validators for a patient record
patient_validators = {
    'first_name': lambda x: Validator.validate_name(x, 'first_name'),
    'last_name': lambda x: Validator.validate_name(x, 'last_name'),
    'email': lambda x: Validator.validate_email(x, 'email'),
    'phone': lambda x: Validator.validate_phone(x, 'phone'),
    'dob': lambda x: Validator.validate_date(x, 'dob'),
    'ssn': lambda x: Validator.validate_ssn(x, 'ssn')
}

# Patient data to validate
patient_data = {
    'first_name': 'John',
    'last_name': 'Doe',
    'email': 'john.doe@example.com',
    'phone': '555-123-4567',
    'dob': '1980-01-15',
    'ssn': '123-45-6789'
}

# Validate the patient data
errors = Validator.validate_dict(patient_data, patient_validators)

if errors:
    print("Validation errors:")
    for field, error in errors.items():
        print(f"  {field}: {error}")
else:
    print("All patient data is valid")
```

### 4.3 Pydantic Model Validation

```python
from datetime import date
from app.utils.validation_models import PatientBase, Gender, InsuranceType

# Create a patient using the Pydantic model
try:
    patient = PatientBase(
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1980, 1, 15),
        gender=Gender.MALE,
        email="john.doe@example.com",
        phone="555-123-4567",
        address_line1="123 Main St",
        city="Anytown",
        state="CA",
        zip_code="12345",
        ssn="123-45-6789",
        insurance_type=InsuranceType.PRIVATE,
        insurance_member_id="MEM12345",
        insurance_group_id="GRP6789"
    )
    print("Patient data is valid:", patient.dict())
except Exception as e:
    print("Validation error:", e)
```

### 4.4 Input Sanitization

```python
from app.utils.validation import Validator

# Sanitize potentially dangerous input
raw_input = "John <script>alert('XSS');</script> Doe"
sanitized = Validator.sanitize_input(raw_input)
print(f"Raw input: {raw_input}")
print(f"Sanitized: {sanitized}")

# Sanitize SQL injection attempt
sql_injection = "John'; DROP TABLE patients; --"
sanitized = Validator.sanitize_input(sql_injection)
print(f"SQL injection attempt: {sql_injection}")
print(f"Sanitized: {sanitized}")
```

## 5. Best Practices

1. **Validate All Inputs**: Always validate all user inputs before processing or storing them.

2. **Use Strong Types**: Leverage Pydantic models for structured validation with strong typing.

3. **Sanitize Inputs**: Always sanitize inputs to prevent injection attacks.

4. **Validate at Multiple Layers**: Implement validation at both the API and service layers.

5. **Custom Domain Validators**: Create custom validators for domain-specific validation rules.

6. **Consistent Error Messages**: Provide clear, consistent error messages for validation failures.

7. **Avoid Revealing Sensitive Information**: Error messages should not reveal sensitive information.

8. **Regular Expression Performance**: Be mindful of regex performance for validation patterns.

9. **Comprehensive Testing**: Thoroughly test validation logic with both valid and invalid inputs.

10. **Keep Validation Rules Updated**: Regularly review and update validation rules as requirements change.

## 6. HIPAA Compliance Considerations

- **PHI Validation**: Ensure all PHI is properly validated to maintain data integrity.

- **Input Sanitization**: Prevent injection attacks that could compromise PHI.

- **Error Handling**: Implement secure error handling that doesn't reveal PHI.

- **Validation Logging**: Log validation failures without including PHI.

- **Data Quality**: Maintain high data quality through comprehensive validation.

## 7. Integration with FastAPI

The validation utility integrates seamlessly with FastAPI for request validation:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.utils.validation_models import PatientBase

router = APIRouter()

@router.post("/patients/", response_model=PatientResponse)
async def create_patient(patient: PatientBase):
    """
    Create a new patient.
    
    The request body is automatically validated using the PatientBase model.
    If validation fails, FastAPI will return a 422 Unprocessable Entity error
    with details about the validation failures.
    """
    # PatientBase validation is handled automatically by FastAPI
    # If we get here, the patient data is valid
    
    # Process the patient data...
    
    return {"id": new_patient_id, **patient.dict()}
```

## 8. Conclusion

The HIPAA-compliant validation utility is a critical component of the NOVAMIND platform's data integrity and security infrastructure. By implementing comprehensive validation for all user inputs and data processing operations, it helps ensure that patient data remains accurate, consistent, and protected from security vulnerabilities. This utility plays a key role in meeting HIPAA requirements for data quality and security while providing a simple and consistent API for validation operations throughout the application.
