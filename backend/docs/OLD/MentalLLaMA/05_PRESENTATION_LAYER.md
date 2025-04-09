# PRESENTATION_LAYER

## Overview

The Presentation Layer is responsible for handling HTTP requests, user authentication, and presenting data to clients. It implements API endpoints, middleware, and user interfaces following RESTful principles and HIPAA compliance requirements.

## API Endpoints

### Authentication Endpoints

```python
# app/presentation/api/routes/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.application.services.auth_service import AuthService
from app.application.dtos.auth_dto import (
    TokenResponseDTO,
    UserCreateDTO,
    UserResponseDTO
)
from app.core.security import get_current_active_user
from app.core.config import settings
from app.core.utils.logging import log_operation

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/token", response_model=TokenResponseDTO)
@log_operation("Login user")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return {
        "access_token": auth_service.create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "user_id": str(user.id),
        "role": user.role
    }

@router.post("/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
@log_operation("Register user")
async def register_user(
    user_data: UserCreateDTO,
    auth_service: AuthService = Depends()
):
    """
    Register a new user.
    """
    return await auth_service.create_user(user_data)

@router.get("/me", response_model=UserResponseDTO)
@log_operation("Get current user")
async def read_users_me(
    current_user: UserResponseDTO = Depends(get_current_active_user)
):
    """
    Get current user information.
    """
    return current_user
```

### Patient Endpoints

```python
# app/presentation/api/routes/patients.py
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.services.patient_service import PatientService
from app.application.dtos.patient_dto import (
    PatientCreateDTO,
    PatientResponseDTO,
    PatientUpdateDTO
)
from app.core.security import get_current_active_user, RoleChecker
from app.core.utils.logging import log_operation
from app.core.exceptions import EntityNotFoundError, ValidationError

router = APIRouter(prefix="/patients", tags=["patients"])

# Role-based access control
require_provider = RoleChecker(["provider", "admin"])
require_admin = RoleChecker(["admin"])

@router.get("/", response_model=List[PatientResponseDTO])
@log_operation("List patients")
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    patient_service: PatientService = Depends(),
    _: dict = Depends(require_provider)
):
    """
    List patients with pagination.
    """
    if active_only:
        return await patient_service.get_active_patients(skip, limit)
    else:
        return await patient_service.list_patients(skip, limit)

@router.get("/search", response_model=List[PatientResponseDTO])
@log_operation("Search patients")
async def search_patients(
    name: Optional[str] = None,
    email: Optional[str] = None,
    patient_service: PatientService = Depends(),
    _: dict = Depends(require_provider)
):
    """
    Search patients by name or email.
    """
    try:
        if name:
            return await patient_service.get_patients_by_name(name)
        elif email:
            patient = await patient_service.get_patient_by_email(email)
            return [patient] if patient else []
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either name or email parameter is required"
            )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.get("/{patient_id}", response_model=PatientResponseDTO)
@log_operation("Get patient")
async def get_patient(
    patient_id: UUID,
    patient_service: PatientService = Depends(),
    _: dict = Depends(require_provider)
):
    """
    Get a specific patient by ID.
    """
    try:
        return await patient_service.get_patient_by_id(patient_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

@router.post("/", response_model=PatientResponseDTO, status_code=status.HTTP_201_CREATED)
@log_operation("Create patient")
async def create_patient(
    patient_data: PatientCreateDTO,
    patient_service: PatientService = Depends(),
    _: dict = Depends(require_provider)
):
    """
    Create a new patient.
    """
    try:
        return await patient_service.create_patient(patient_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.put("/{patient_id}", response_model=PatientResponseDTO)
@log_operation("Update patient")
async def update_patient(
    patient_id: UUID,
    patient_data: PatientUpdateDTO,
    patient_service: PatientService = Depends(),
    _: dict = Depends(require_provider)
):
    """
    Update an existing patient.
    """
    try:
        return await patient_service.update_patient(patient_id, patient_data)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_operation("Deactivate patient")
async def deactivate_patient(
    patient_id: UUID,
    patient_service: PatientService = Depends(),
    _: dict = Depends(require_admin)
):
    """
    Deactivate a patient (soft delete).
    """
    try:
        await patient_service.deactivate_patient(patient_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
```

### Digital Twin Endpoints

```python
# app/presentation/api/routes/digital_twins.py
from typing import Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.application.services.digital_twin_service import DigitalTwinService
from app.application.dtos.digital_twin_dto import (
    DigitalTwinResponseDTO,
    DigitalTwinUpdateDTO
)
from app.core.security import get_current_active_user, RoleChecker
from app.core.utils.logging import log_operation
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/digital-twins", tags=["digital-twins"])

# Role-based access control
require_provider = RoleChecker(["provider", "admin"])

@router.get("/{patient_id}", response_model=DigitalTwinResponseDTO)
@log_operation("Get digital twin")
async def get_digital_twin(
    patient_id: UUID,
    digital_twin_service: DigitalTwinService = Depends(),
    _: dict = Depends(require_provider)
):
    """
    Get a patient's digital twin.
    """
    try:
        return await digital_twin_service.get_digital_twin(patient_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

@router.put("/{patient_id}", response_model=DigitalTwinResponseDTO)
@log_operation("Update digital twin")
async def update_digital_twin(
    patient_id: UUID,
    update_data: DigitalTwinUpdateDTO,
    digital_twin_service: DigitalTwinService = Depends(),
    _: dict = Depends(require_provider)
):
    """
    Update a patient's digital twin.
    """
    try:
        return await digital_twin_service.update_digital_twin(patient_id, update_data)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

@router.post("/{patient_id}/forecast", response_model=Dict)
@log_operation("Generate symptom forecast")
async def generate_symptom_forecast(
    patient_id: UUID,
    digital_twin_service: DigitalTwinService = Depends(),
    _: dict = Depends(require_provider)
):
    """
    Generate a symptom forecast for a patient.
    """
    try:
        return await digital_twin_service.generate_symptom_forecast(patient_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
```

## API Configuration

```python
# app/presentation/api/api.py
from fastapi import APIRouter

from app.presentation.api.routes import (
    auth,
    patients,
    appointments,
    digital_twins,
    users
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router)
api_router.include_router(patients.router)
api_router.include_router(appointments.router)
api_router.include_router(digital_twins.router)
api_router.include_router(users.router)
```

## Main Application

```python
# app/main.py
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html

from app.core.config import settings
from app.core.exceptions import NovamindException
from app.presentation.api.api import api_router
from app.core.utils.logging import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Custom exception handler
@app.exception_handler(NovamindException)
async def novamind_exception_handler(request: Request, exc: NovamindException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "errors": exc.details},
    )

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Mount static files
app.mount("/static", StaticFiles(directory="app/presentation/web/static"), name="static")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Custom docs endpoint with authentication
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        oauth2_redirect_url=f"{settings.API_V1_STR}/oauth2-redirect",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Security

```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import List, Optional, Union

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.application.services.user_service import UserService
from app.application.dtos.user_dto import UserResponseDTO
from app.core.config import settings
from app.core.utils.logging import logger

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token"
)

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
) -> UserResponseDTO:
    """
    Validate access token and return current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
    except (JWTError, ValidationError):
        logger.error("JWT validation error", exc_info=True)
        raise credentials_exception
        
    user = await user_service.get_user_by_email(email)
    
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user: UserResponseDTO = Depends(get_current_user)
) -> UserResponseDTO:
    """
    Check if current user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
        
    return current_user

class RoleChecker:
    """
    Role-based access control.
    """
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
        
    async def __call__(
        self, 
        current_user: UserResponseDTO = Security(get_current_active_user)
    ) -> dict:
        """
        Check if current user has required role.
        """
        if current_user.role not in self.allowed_roles:
            logger.warning(
                f"User {current_user.email} with role {current_user.role} "
                f"attempted to access endpoint requiring roles {self.allowed_roles}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
            
        return {"user_id": current_user.id, "role": current_user.role}
```

## OpenAPI Documentation

```yaml
# app/presentation/api/docs/openapi.yaml
openapi: 3.1.0
info:
  title: NOVAMIND API
  description: |
    API for the NOVAMIND psychiatric platform.
    
    This API provides endpoints for managing patients, appointments, and digital twins.
  version: 1.0.0
  contact:
    name: NOVAMIND Support
    email: support@novamind.example.com
  license:
    name: Proprietary
servers:
  - url: /api/v1
    description: Development server
paths:
  /auth/token:
    post:
      summary: Login for access token
      operationId: login_for_access_token
      tags:
        - authentication
      requestBody:
        required: true
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              properties:
                username:
                  type: string
                  description: User email
                password:
                  type: string
                  description: User password
              required:
                - username
                - password
      responses:
        '200':
          description: Successful login
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
        '401':
          description: Incorrect email or password
  /patients:
    get:
      summary: List patients
      operationId: list_patients
      tags:
        - patients
      parameters:
        - name: skip
          in: query
          schema:
            type: integer
            default: 0
          description: Number of patients to skip
        - name: limit
          in: query
          schema:
            type: integer
            default: 100
          description: Maximum number of patients to return
        - name: active_only
          in: query
          schema:
            type: boolean
            default: true
          description: Only return active patients
      security:
        - BearerAuth: []
      responses:
        '200':
          description: List of patients
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/PatientResponse'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
    post:
      summary: Create a new patient
      operationId: create_patient
      tags:
        - patients
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatientCreate'
      security:
        - BearerAuth: []
      responses:
        '201':
          description: Patient created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatientResponse'
        '400':
          description: Validation error
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
components:
  schemas:
    TokenResponse:
      type: object
      properties:
        access_token:
          type: string
          description: JWT access token
        token_type:
          type: string
          description: Token type
          example: bearer
        user_id:
          type: string
          format: uuid
          description: User ID
        role:
          type: string
          description: User role
          example: provider
      required:
        - access_token
        - token_type
    PatientCreate:
      type: object
      properties:
        first_name:
          type: string
          minLength: 1
          maxLength: 100
        last_name:
          type: string
          minLength: 1
          maxLength: 100
        date_of_birth:
          type: string
          format: date
        email:
          type: string
          format: email
        phone:
          type: string
          minLength: 10
          maxLength: 20
        address:
          type: object
          nullable: true
        insurance:
          type: object
          nullable: true
        emergency_contact:
          type: object
          nullable: true
      required:
        - first_name
        - last_name
        - date_of_birth
        - email
        - phone
    PatientResponse:
      allOf:
        - $ref: '#/components/schemas/PatientCreate'
        - type: object
          properties:
            id:
              type: string
              format: uuid
            active:
              type: boolean
          required:
            - id
            - active
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

## Web Templates

### Base Template

```html
<!-- app/presentation/web/templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}NOVAMIND{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', path='/css/main.css') }}">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <header>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">NOVAMIND</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav ms-auto">
                        {% if current_user %}
                            <li class="nav-item">
                                <a class="nav-link" href="/dashboard">Dashboard</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/patients">Patients</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/appointments">Appointments</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/logout">Logout</a>
                            </li>
                        {% else %}
                            <li class="nav-item">
                                <a class="nav-link" href="/login">Login</a>
                            </li>
                        {% endif %}
                    </ul>
                </div>
            </div>
        </nav>
    </header>
    
    <main class="container my-4">
        {% block content %}{% endblock %}
    </main>
    
    <footer class="bg-light py-3 mt-5">
        <div class="container text-center">
            <p>&copy; {% now 'Y' %} NOVAMIND. All rights reserved.</p>
            <p>HIPAA Compliant | Secure | Confidential</p>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', path='/js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Dashboard Template

```html
<!-- app/presentation/web/templates/dashboard.html -->
{% extends "base.html" %}

{% block title %}Dashboard | NOVAMIND{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12 mb-4">
        <h1>Welcome, {{ current_user.first_name }}</h1>
        <p class="lead">Your concierge psychiatric dashboard</p>
    </div>
    
    <div class="col-md-6">
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="card-title mb-0">Today's Appointments</h5>
            </div>
            <div class="card-body">
                {% if today_appointments %}
                    <ul class="list-group">
                        {% for appointment in today_appointments %}
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{{ appointment.patient.full_name }}</strong>
                                    <br>
                                    <small>{{ appointment.start_time|time }} - {{ appointment.end_time|time }}</small>
                                </div>
                                <span class="badge bg-primary rounded-pill">{{ appointment.appointment_type }}</span>
                            </li>
                        {% endfor %}
                    </ul>
                {% else %}
                    <p class="text-muted">No appointments scheduled for today.</p>
                {% endif %}
            </div>
            <div class="card-footer">
                <a href="/appointments" class="btn btn-sm btn-outline-primary">View All Appointments</a>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="card-title mb-0">Recent Patients</h5>
            </div>
            <div class="card-body">
                {% if recent_patients %}
                    <ul class="list-group">
                        {% for patient in recent_patients %}
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{{ patient.full_name }}</strong>
                                    <br>
                                    <small>{{ patient.email }}</small>
                                </div>
                                <a href="/patients/{{ patient.id }}" class="btn btn-sm btn-outline-secondary">View</a>
                            </li>
                        {% endfor %}
                    </ul>
                {% else %}
                    <p class="text-muted">No recent patients.</p>
                {% endif %}
            </div>
            <div class="card-footer">
                <a href="/patients" class="btn btn-sm btn-outline-primary">View All Patients</a>
            </div>
        </div>
    </div>
    
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">Digital Twin Insights</h5>
            </div>
            <div class="card-body">
                <div class="alert alert-info">
                    <h6 class="alert-heading">AI-Powered Insights</h6>
                    <p>Our Digital Twin technology provides personalized insights for each patient.</p>
                </div>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="card text-white bg-primary mb-3">
                            <div class="card-header">Symptom Forecasting</div>
                            <div class="card-body">
                                <h5 class="card-title">TimeGPT-1</h5>
                                <p class="card-text">Predict symptom trajectories with our advanced time-series model.</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card text-white bg-success mb-3">
                            <div class="card-header">Biometric Correlation</div>
                            <div class="card-body">
                                <h5 class="card-title">MindGPT-Bio</h5>
                                <p class="card-text">Correlate biometric data with mental health indicators.</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card text-white bg-info mb-3">
                            <div class="card-header">Medication Modeling</div>
                            <div class="card-body">
                                <h5 class="card-title">PharmacoTransformer</h5>
                                <p class="card-text">Personalized medication response prediction.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## Implementation Guidelines

1. **API Design**: Follow RESTful principles with proper HTTP methods and status codes
2. **Authentication**: Use JWT tokens for authentication with proper expiration and refresh mechanisms
3. **Authorization**: Implement role-based access control for all endpoints
4. **Input Validation**: Validate all input data using Pydantic models and path/query parameters
5. **Error Handling**: Use custom exception handlers for consistent error responses
6. **Documentation**: Maintain OpenAPI documentation for all endpoints
7. **Security Headers**: Implement security headers for all responses
8. **CORS**: Configure CORS policies for allowed origins
9. **Logging**: Log all API requests and responses with PHI redaction
10. **Rate Limiting**: Implement rate limiting for public endpoints