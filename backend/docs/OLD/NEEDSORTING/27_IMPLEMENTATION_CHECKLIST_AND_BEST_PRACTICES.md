# IMPLEMENTATION CHECKLIST AND BEST PRACTICES

## Overview

This document provides a comprehensive checklist and best practices for implementing features in the NOVAMIND platform. It serves as a guide for developers to ensure they follow the established patterns and practices.

## 1. Implementation Checklist

### 1.1. Domain Layer

- [ ] Define domain entities with proper validation
- [ ] Create value objects for complex attributes
- [ ] Define repository interfaces
- [ ] Implement domain services for complex business logic
- [ ] Define domain events for important state changes
- [ ] Create domain exceptions for error handling
- [ ] Ensure no external dependencies in the domain layer
- [ ] Add comprehensive unit tests for domain logic

### 1.2. Application Layer

- [ ] Create use cases for specific business operations
- [ ] Implement application services to orchestrate use cases
- [ ] Define DTOs for input/output data
- [ ] Add validation for input data
- [ ] Implement proper error handling
- [ ] Ensure use cases depend only on domain interfaces
- [ ] Add unit tests for use cases and services

### 1.3. Infrastructure Layer

- [ ] Implement repository interfaces from the domain layer
- [ ] Create ORM models for database entities
- [ ] Implement external service adapters
- [ ] Configure dependency injection
- [ ] Implement logging and monitoring
- [ ] Add security features (authentication, authorization)
- [ ] Add integration tests for repositories and external services

### 1.4. Presentation Layer

- [ ] Define API endpoints
- [ ] Create Pydantic schemas for request/response validation
- [ ] Implement controllers/handlers for endpoints
- [ ] Add authentication and authorization middleware
- [ ] Implement error handling middleware
- [ ] Add API documentation
- [ ] Add end-to-end tests for API endpoints

## 2. Best Practices

### 2.1. Clean Architecture

#### 2.1.1. Layer Separation

- Keep layers separate with clear boundaries
- Domain layer should have no dependencies on other layers
- Application layer should only depend on the domain layer
- Infrastructure layer should implement interfaces from the domain layer
- Presentation layer should only depend on the application layer

#### 2.1.2. Dependency Flow

- Dependencies should flow inward (from outer layers to inner layers)
- Use dependency injection to provide dependencies to inner layers
- Use interfaces to decouple implementations from abstractions

#### 2.1.3. Domain-Driven Design

- Use ubiquitous language throughout the codebase
- Model the domain accurately with entities, value objects, and aggregates
- Use domain events to communicate between aggregates
- Implement domain services for operations that don't naturally fit within an entity

### 2.2. SOLID Principles

#### 2.2.1. Single Responsibility Principle

- Each class should have only one reason to change
- Keep classes focused on a single responsibility
- Extract complex logic into separate classes or methods

```python
# Good
class PatientRepository:
    """Repository for patient data access"""
    
    def create(self, patient: Patient) -> Patient:
        """Create a new patient"""
        pass
    
    def get_by_id(self, patient_id: UUID) -> Optional[Patient]:
        """Get a patient by ID"""
        pass

# Bad
class PatientService:
    """Service for patient operations"""
    
    def create_patient(self, patient_data: dict) -> Patient:
        """Create a new patient"""
        # This method does too much: validation, creation, notification
        self._validate_patient_data(patient_data)
        patient = Patient(**patient_data)
        self._save_patient(patient)
        self._send_welcome_email(patient)
        return patient
```

#### 2.2.2. Open/Closed Principle

- Classes should be open for extension but closed for modification
- Use inheritance and composition to extend behavior
- Use strategy pattern for interchangeable algorithms

```python
# Good
class NotificationStrategy(ABC):
    """Interface for notification strategies"""
    
    @abstractmethod
    def send_notification(self, recipient: str, message: str) -> None:
        """Send a notification"""
        pass

class EmailNotificationStrategy(NotificationStrategy):
    """Email notification strategy"""
    
    def send_notification(self, recipient: str, message: str) -> None:
        """Send an email notification"""
        # Implementation
        pass

class SMSNotificationStrategy(NotificationStrategy):
    """SMS notification strategy"""
    
    def send_notification(self, recipient: str, message: str) -> None:
        """Send an SMS notification"""
        # Implementation
        pass

class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self, strategy: NotificationStrategy):
        """Initialize with a notification strategy"""
        self._strategy = strategy
    
    def notify(self, recipient: str, message: str) -> None:
        """Send a notification using the configured strategy"""
        self._strategy.send_notification(recipient, message)
```

#### 2.2.3. Liskov Substitution Principle

- Subtypes should be substitutable for their base types
- Override methods should respect the contract of the base class
- Don't throw exceptions that the base class doesn't throw

```python
# Good
class Repository(Generic[T]):
    """Base repository interface"""
    
    @abstractmethod
    def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get an entity by ID"""
        pass

class PatientRepository(Repository[Patient]):
    """Patient repository implementation"""
    
    def get_by_id(self, entity_id: UUID) -> Optional[Patient]:
        """Get a patient by ID"""
        # Implementation
        pass
```

#### 2.2.4. Interface Segregation Principle

- Clients should not be forced to depend on interfaces they don't use
- Keep interfaces focused and cohesive
- Split large interfaces into smaller, more specific ones

```python
# Good
class ReadRepository(Generic[T]):
    """Repository interface for read operations"""
    
    @abstractmethod
    def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get an entity by ID"""
        pass
    
    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List all entities"""
        pass

class WriteRepository(Generic[T]):
    """Repository interface for write operations"""
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity"""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: UUID) -> bool:
        """Delete an entity"""
        pass

class PatientRepository(ReadRepository[Patient], WriteRepository[Patient]):
    """Patient repository implementation"""
    # Implementation
    pass
```

#### 2.2.5. Dependency Inversion Principle

- High-level modules should not depend on low-level modules
- Both should depend on abstractions
- Abstractions should not depend on details
- Details should depend on abstractions

```python
# Good
class PatientService:
    """Service for patient operations"""
    
    def __init__(self, patient_repository: PatientRepository):
        """Initialize with a patient repository"""
        self._patient_repository = patient_repository
    
    def get_patient(self, patient_id: UUID) -> Optional[Patient]:
        """Get a patient by ID"""
        return self._patient_repository.get_by_id(patient_id)
```

### 2.3. Code Quality

#### 2.3.1. Function Size

- Keep functions small (≤15 lines)
- Each function should do one thing well
- Extract complex logic into helper functions

```python
# Good
def register_patient(self, patient_data: dict) -> Patient:
    """Register a new patient"""
    validated_data = self._validate_patient_data(patient_data)
    patient = self._create_patient(validated_data)
    self._send_welcome_email(patient)
    return patient

def _validate_patient_data(self, patient_data: dict) -> dict:
    """Validate patient data"""
    # Validation logic
    return validated_data

def _create_patient(self, validated_data: dict) -> Patient:
    """Create a new patient"""
    patient = Patient(**validated_data)
    return self._patient_repository.create(patient)

def _send_welcome_email(self, patient: Patient) -> None:
    """Send a welcome email to the patient"""
    # Email sending logic
    pass
```

#### 2.3.2. Early Returns

- Use early returns to simplify logic
- Avoid deep nesting of conditionals
- Handle edge cases first

```python
# Good
def get_patient_by_id(self, patient_id: UUID) -> Optional[Patient]:
    """Get a patient by ID"""
    if not patient_id:
        return None
    
    patient = self._patient_repository.get_by_id(patient_id)
    if not patient:
        return None
    
    if not patient.active:
        return None
    
    return patient

# Bad
def get_patient_by_id(self, patient_id: UUID) -> Optional[Patient]:
    """Get a patient by ID"""
    if patient_id:
        patient = self._patient_repository.get_by_id(patient_id)
        if patient:
            if patient.active:
                return patient
    return None
```

#### 2.3.3. Descriptive Names

- Use descriptive names for classes, methods, and variables
- Avoid abbreviations and acronyms
- Use consistent naming conventions

```python
# Good
def calculate_medication_dosage(patient_weight: float, medication_concentration: float) -> float:
    """Calculate the medication dosage based on patient weight and medication concentration"""
    return patient_weight * medication_concentration * 0.1

# Bad
def calc_med_dose(pw: float, mc: float) -> float:
    """Calculate dosage"""
    return pw * mc * 0.1
```

#### 2.3.4. Comments and Documentation

- Add docstrings to all classes and methods
- Document parameters, return values, and exceptions
- Add inline comments for complex logic

```python
def calculate_medication_dosage(
    patient_weight: float,
    medication_concentration: float,
    patient_age: int
) -> float:
    """
    Calculate the medication dosage based on patient weight, medication concentration, and age.
    
    Args:
        patient_weight: The patient's weight in kilograms
        medication_concentration: The medication concentration in mg/ml
        patient_age: The patient's age in years
        
    Returns:
        The calculated dosage in milliliters
        
    Raises:
        ValueError: If patient_weight or medication_concentration is negative
    """
    if patient_weight <= 0 or medication_concentration <= 0:
        raise ValueError("Patient weight and medication concentration must be positive")
    
    # Base dosage calculation
    base_dosage = patient_weight * medication_concentration * 0.1
    
    # Age adjustment factor
    age_factor = 1.0
    if patient_age < 12:
        # Children receive a reduced dosage
        age_factor = 0.8
    elif patient_age > 65:
        # Elderly patients receive a reduced dosage
        age_factor = 0.9
    
    return base_dosage * age_factor
```

### 2.4. Error Handling

#### 2.4.1. Domain Exceptions

- Create specific exception classes for domain errors
- Use descriptive names for exception classes
- Include relevant information in exception messages

```python
class AppointmentConflictError(Exception):
    """Raised when an appointment conflicts with an existing appointment"""
    
    def __init__(self, appointment_date: datetime, provider_id: UUID):
        """Initialize with appointment details"""
        self.appointment_date = appointment_date
        self.provider_id = provider_id
        message = f"Appointment conflict on {appointment_date} for provider {provider_id}"
        super().__init__(message)
```

#### 2.4.2. Error Translation

- Translate domain exceptions to appropriate HTTP status codes
- Include relevant information in error responses
- Don't expose sensitive information in error messages

```python
@router.post("/appointments")
async def create_appointment(
    appointment_data: AppointmentCreate,
    use_case: CreateAppointmentUseCase = Depends(get_create_appointment_use_case)
):
    """Create a new appointment"""
    try:
        appointment = await use_case.execute(appointment_data.dict())
        return AppointmentResponse.from_entity(appointment)
    except AppointmentConflictError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Appointment conflict on {e.appointment_date}"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # Log the error
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the appointment"
        )
```

### 2.5. Testing

#### 2.5.1. Unit Testing

- Test each unit of code in isolation
- Mock external dependencies
- Test both success and failure cases
- Use descriptive test names

```python
@pytest.mark.asyncio
async def test_create_patient_with_valid_data_returns_patient():
    """Test creating a patient with valid data"""
    # Arrange
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
        "contact_info": {
            "email": "john.doe@example.com",
            "phone": "555-1234"
        }
    }
    mock_repository = Mock(spec=PatientRepository)
    mock_repository.create.return_value = Patient(
        id=uuid4(),
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1980, 1, 1),
        contact_info=ContactInfo(
            email="john.doe@example.com",
            phone="555-1234"
        )
    )
    use_case = CreatePatientUseCase(patient_repository=mock_repository)
    
    # Act
    patient = await use_case.execute(patient_data)
    
    # Assert
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"
    mock_repository.create.assert_called_once()
```

#### 2.5.2. Integration Testing

- Test the interaction between components
- Use a test database
- Test the complete flow from API to database
- Clean up test data after each test

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_patient_api_endpoint(client, test_database):
    """Test the create patient API endpoint"""
    # Arrange
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
        "contact_info": {
            "email": "john.doe@example.com",
            "phone": "555-1234"
        }
    }
    
    # Act
    response = await client.post("/api/v1/patients", json=patient_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["first_name"] == "John"
    assert response.json()["last_name"] == "Doe"
    
    # Verify the patient was created in the database
    patient_repository = SQLAlchemyPatientRepository(database=test_database)
    patient = await patient_repository.get_by_email("john.doe@example.com")
    assert patient is not None
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"
```

### 2.6. Security

#### 2.6.1. Authentication

- Use JWT tokens for authentication
- Implement token refresh
- Use secure cookie settings
- Implement multi-factor authentication

```python
def get_current_user(
    token: str = Depends(oauth2_scheme),
    token_handler: TokenHandler = Depends(get_token_handler)
) -> dict:
    """Get the current user from the JWT token"""
    try:
        payload = token_handler.decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"id": user_id, "roles": payload.get("roles", [])}
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

#### 2.6.2. Authorization

- Implement role-based access control
- Check permissions for each operation
- Use middleware for authorization

```python
def require_role(role: str):
    """Require a specific role for the current user"""
    def _require_role(user: dict = Depends(get_current_user)) -> dict:
        if role not in user["roles"]:
            raise HTTPException(
                status_code=403,
                detail=f"User does not have the required role: {role}"
            )
        return user
    return _require_role

@router.get("/patients/{patient_id}")
async def get_patient(
    patient_id: UUID,
    service: PatientService = Depends(get_patient_service),
    user: dict = Depends(require_role("admin"))
):
    """Get a patient by ID"""
    patient = await service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.from_entity(patient)
```

#### 2.6.3. Data Protection

- Encrypt sensitive data at rest
- Use HTTPS for all communications
- Implement proper logging (no PHI in logs)
- Implement data access auditing

```python
class EncryptedField:
    """Field that encrypts data at rest"""
    
    def __init__(self, encryption_service: EncryptionService):
        """Initialize with an encryption service"""
        self._encryption_service = encryption_service
    
    def __get__(self, instance, owner):
        """Get the decrypted value"""
        if instance is None:
            return self
        encrypted_value = instance.__dict__.get(self.name)
        if encrypted_value is None:
            return None
        return self._encryption_service.decrypt(encrypted_value)
    
    def __set__(self, instance, value):
        """Set the encrypted value"""
        if value is None:
            instance.__dict__[self.name] = None
        else:
            instance.__dict__[self.name] = self._encryption_service.encrypt(value)
    
    def __set_name__(self, owner, name):
        """Set the descriptor name"""
        self.name = name
```

## 3. Implementation Examples

### 3.1. Domain Entity

```python
@dataclass
class Patient:
    """
    Patient entity representing a patient in the concierge psychiatry practice.
    
    This is a rich domain entity containing business logic related to patient management.
    It follows DDD principles and is framework-independent.
    """
    first_name: str
    last_name: str
    date_of_birth: date
    contact_info: ContactInfo
    id: UUID = field(default_factory=uuid4)
    gender: Optional[str] = None
    insurance_info: Optional[InsuranceInfo] = None
    emergency_contacts: List[EmergencyContact] = field(default_factory=list)
    assessments: List[PsychiatricAssessment] = field(default_factory=list)
    medical_history: Dict[str, str] = field(default_factory=dict)
    medication_allergies: List[str] = field(default_factory=list)
    active: bool = True
    
    @property
    def full_name(self) -> str:
        """Get the patient's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        """Calculate the patient's age based on date of birth"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def add_assessment(self, assessment: PsychiatricAssessment) -> None:
        """Add a psychiatric assessment to the patient's record"""
        self.assessments.append(assessment)
    
    def get_latest_assessment(self) -> Optional[PsychiatricAssessment]:
        """Get the patient's most recent psychiatric assessment"""
        if not self.assessments:
            return None
        
        return max(self.assessments, key=lambda a: a.assessment_date)
```

### 3.2. Repository Interface

```python
class PatientRepository(ABC):
    """
    Repository interface for Patient entity operations.
    
    This abstract class defines the contract that any patient repository
    implementation must fulfill, ensuring the domain layer remains
    independent of data access technologies.
    """
    
    @abstractmethod
    async def create(self, patient: Patient) -> Patient:
        """
        Create a new patient record
        
        Args:
            patient: The patient entity to create
            
        Returns:
            The created patient with any system-generated fields populated
            
        Raises:
            RepositoryError: If there's an error during creation
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, patient_id: UUID) -> Optional[Patient]:
        """
        Retrieve a patient by ID
        
        Args:
            patient_id: The UUID of the patient to retrieve
            
        Returns:
            The patient entity if found, None otherwise
            
        Raises:
            RepositoryError: If there's an error during retrieval
        """
        pass
```

### 3.3. Use Case

```python
class CreatePatientUseCase:
    """Use case for creating a new patient in the system"""
    
    def __init__(self, patient_repository: PatientRepository):
        """Initialize with required repositories"""
        self.patient_repository = patient_repository
    
    async def execute(self, patient_data: dict) -> Patient:
        """
        Execute the use case to create a new patient
        
        Args:
            patient_data: Dictionary containing patient information
            
        Returns:
            The created Patient entity
            
        Raises:
            ValueError: If patient data is invalid
        """
        # Validate patient data
        self._validate_patient_data(patient_data)
        
        # Create contact info
        contact_info = ContactInfo(**patient_data["contact_info"])
        
        # Create patient entity
        patient = Patient(
            first_name=patient_data["first_name"],
            last_name=patient_data["last_name"],
            date_of_birth=date.fromisoformat(patient_data["date_of_birth"]),
            contact_info=contact_info,
            gender=patient_data.get("gender"),
            insurance_info=InsuranceInfo(**patient_data["insurance_info"]) if "insurance_info" in patient_data else None
        )
        
        # Add emergency contacts
        for contact_data in patient_data.get("emergency_contacts", []):
            patient.add_emergency_contact(EmergencyContact(**contact_data))
        
        # Add medication allergies
        for medication in patient_data.get("medication_allergies", []):
            patient.add_medication_allergy(medication)
        
        # Save patient
        return await self.patient_repository.create(patient)
    
    def _validate_patient_data(self, patient_data: dict) -> None:
        """
        Validate patient data
        
        Args:
            patient_data: Dictionary containing patient information
            
        Raises:
            ValueError: If patient data is invalid
        """
        required_fields = ["first_name", "last_name", "date_of_birth", "contact_info"]
        for field in required_fields:
            if field not in patient_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate date of birth
        try:
            dob = date.fromisoformat(patient_data["date_of_birth"])
            today = date.today()
            if dob > today:
                raise ValueError("Date of birth cannot be in the future")
        except ValueError as e:
            raise ValueError(f"Invalid date of birth: {str(e)}")
        
        # Validate contact info
        if not isinstance(patient_data["contact_info"], dict):
            raise ValueError("Contact info must be a dictionary")
        
        required_contact_fields = ["email", "phone"]
        for field in required_contact_fields:
            if field not in patient_data["contact_info"]:
                raise ValueError(f"Missing required contact field: {field}")
```

### 3.4. API Endpoint

```python
@router.post("/patients", response_model=PatientResponse, status_code=201)
async def create_patient(
    patient_data: PatientCreate,
    use_case: CreatePatientUseCase = Depends(get_create_patient_use_case),
    current_user: dict = Depends(require_role("admin"))
):
    """
    Create a new patient
    
    Args:
        patient_data: Patient data from request body
        use_case: CreatePatientUseCase instance
        current_user: Current authenticated user with admin role
        
    Returns:
        The created patient
        
    Raises:
        HTTPException: If there's an error during patient creation
    """
    try:
        patient = await use_case.execute(patient_data.dict())
        return PatientResponse.from_entity(patient)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the error
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while creating the patient")
```

## Conclusion

This implementation checklist and best practices guide provides a comprehensive approach to implementing features in the NOVAMIND platform. By following these guidelines, you can ensure that your code is clean, maintainable, and follows the established patterns and practices.