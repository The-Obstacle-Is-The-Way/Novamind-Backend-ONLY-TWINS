# API Design Guidelines

This document provides comprehensive guidelines for designing RESTful APIs within the Novamind Digital Twin Platform. It serves as the canonical reference for all API development, ensuring consistency, security, and adherence to best practices across the platform.

## Table of Contents

1. [Overview](#overview)
2. [RESTful Design Principles](#restful-design-principles)
   - [Resource-Oriented Design](#resource-oriented-design)
   - [HTTP Methods](#http-methods)
   - [URL Structure](#url-structure)
   - [Query Parameters](#query-parameters)
3. [Request and Response Formats](#request-and-response-formats)
   - [JSON Schema](#json-schema)
   - [Data Types](#data-types)
   - [Response Structure](#response-structure)
   - [Error Handling](#error-handling)
4. [API Versioning](#api-versioning)
   - [Version Strategy](#version-strategy)
   - [Version Compatibility](#version-compatibility)
   - [Deprecation Process](#deprecation-process)
5. [API Security](#api-security)
   - [Authentication](#authentication)
   - [Authorization](#authorization)
   - [Input Validation](#input-validation)
   - [Output Sanitization](#output-sanitization)
6. [Performance Considerations](#performance-considerations)
   - [Pagination](#pagination)
   - [Filtering](#filtering)
   - [Rate Limiting](#rate-limiting)
   - [Caching](#caching)
7. [Documentation](#documentation)
   - [OpenAPI Specification](#openapi-specification)
   - [Code Examples](#code-examples)
   - [Reference Documentation](#reference-documentation)
8. [Implementation Guidelines](#implementation-guidelines)
   - [FastAPI Implementation](#fastapi-implementation)
   - [Middleware](#middleware)
   - [Dependency Injection](#dependency-injection)
   - [Testing](#testing)

## Overview

The Novamind Digital Twin Platform exposes its functionality through a comprehensive set of RESTful APIs that enable secure, efficient interaction with the platform's capabilities. These APIs serve various client applications, integrations with external systems, and provide programmatic access to the Digital Twin platform.

This guide establishes the standards and best practices for designing, implementing, and maintaining these APIs. Following these guidelines ensures that all APIs across the platform are:

1. **Consistent**: Following standardized patterns and conventions
2. **Secure**: Implementing robust security measures for sensitive PHI
3. **Maintainable**: Well-structured and documented for long-term sustainability
4. **Performant**: Optimized for efficiency and scalability
5. **Usable**: Developer-friendly and intuitive to consume

All API designs must adhere to these guidelines and undergo a formal review process to ensure compliance.

## RESTful Design Principles

### Resource-Oriented Design

APIs should be designed around resources that represent domain entities:

1. **Resource Identification**
   - Resources should be nouns representing domain entities (e.g., patients, clinicians, treatments)
   - Avoid verb-based endpoints except for special actions that cannot be modeled as resource operations
   - Resources should be hierarchically structured with clear relationships

2. **Resource Granularity**
   - Resources should have appropriate granularity based on usage patterns
   - Avoid overly fine-grained resources that require multiple requests for common operations
   - Avoid excessively coarse-grained resources that return unnecessary data

3. **Resource Relationships**
   - Model relationships through nested resources where appropriate
   - Use consistent patterns for relationship representation
   - Consider HATEOAS principles for navigating relationships

4. **Collection and Singleton Resources**
   - Collections represented as plural nouns (e.g., `/patients`)
   - Singleton resources represented as singular nouns (e.g., `/patients/{id}`)
   - Special singleton resources may use descriptive names (e.g., `/patients/{id}/medical-history`)

### HTTP Methods

Use HTTP methods in a standardized way:

| Method | Use Case | Examples |
|--------|----------|----------|
| GET | Retrieve resources without side effects | `GET /patients`, `GET /patients/{id}` |
| POST | Create new resources or execute operations | `POST /patients`, `POST /patients/{id}/treatments` |
| PUT | Replace a resource entirely | `PUT /patients/{id}` |
| PATCH | Update a resource partially | `PATCH /patients/{id}` |
| DELETE | Remove a resource | `DELETE /patients/{id}` |

**Guidelines for HTTP Method Usage:**

1. **GET**
   - Must be idempotent and have no side effects
   - Must never be used for operations that modify state
   - Should support filtering, sorting, and pagination
   - May support projections to request specific fields

2. **POST**
   - Used for resource creation when the identifier is server-assigned
   - Used for complex operations that cannot be modeled as other HTTP methods
   - Non-idempotent by default (each request creates a new resource)
   - May return 201 Created with a Location header or the created resource

3. **PUT**
   - Must be idempotent (same effect regardless of how many times applied)
   - Replaces the entire resource (client provides all attributes)
   - Used when the client provides the resource identifier
   - Returns 200 OK with the updated resource or 204 No Content

4. **PATCH**
   - Updates partial attributes of a resource
   - Should use a consistent format for expressing changes (e.g., JSON Patch or custom format)
   - May not be idempotent depending on the patch semantics
   - Returns 200 OK with the updated resource or 204 No Content

5. **DELETE**
   - Removes the specified resource
   - Should be idempotent (same effect even if resource already deleted)
   - Returns 204 No Content or 200 OK with metadata about the deletion

### URL Structure

URLs should follow a consistent structure:

1. **Base URL**
   - Production: `https://api.novamind.com/v{version}`
   - Staging: `https://api.staging.novamind.com/v{version}`
   - Development: `https://api.dev.novamind.com/v{version}`

2. **Path Structure**
   - Use kebab-case for multi-word resource names (e.g., `/medical-records`)
   - Use plural nouns for collection resources (e.g., `/patients`)
   - Nest sub-resources under their parent (e.g., `/patients/{id}/treatments`)
   - Limit nesting depth to 2-3 levels maximum

3. **Path Parameters**
   - Use UUIDs for resource identifiers (e.g., `/patients/{id}`)
   - Provide descriptive parameter names in documentation
   - Validate path parameters strictly

4. **URL Length Limits**
   - Keep URLs under 2,000 characters to accommodate all browsers and servers
   - For complex queries, consider using request bodies with POST

### Query Parameters

Use query parameters consistently:

1. **Common Parameters**
   - Pagination: `page`, `limit` or `offset`, `limit`
   - Sorting: `sort=field:direction` (e.g., `sort=lastName:asc,createdAt:desc`)
   - Filtering: `filter[field]=value` or `field=value`
   - Field selection: `fields=field1,field2,field3`
   - Including related resources: `include=relation1,relation2`

2. **Parameter Naming**
   - Use camelCase for parameter names
   - Use descriptive names that reflect their purpose
   - Maintain consistency across similar parameters

3. **Parameter Encoding**
   - All parameters must be properly URL-encoded
   - Arrays can be specified with repeated parameters or comma-separated values
   - Complex parameters should use a consistent, documented format

4. **HIPAA Considerations**
   - Never include PHI in query parameters
   - Use POST with request bodies for queries containing PHI
   - Consider using reference tokens instead of direct identifiers

## Request and Response Formats

### JSON Schema

All API requests and responses must use JSON:

1. **Content Type**
   - All requests with bodies must set `Content-Type: application/json`
   - All responses must set `Content-Type: application/json`

2. **Schema Definition**
   - Define schemas using JSON Schema or OpenAPI specification
   - Maintain schemas in a central repository
   - Version schemas along with the API

3. **Schema Validation**
   - Validate all request bodies against their schema
   - Return appropriate error responses for schema violations
   - Document schema constraints clearly

4. **Field Naming Conventions**
   - Use camelCase for all property names
   - Use descriptive names that reflect domain terminology
   - Maintain consistent naming patterns across resources

### Data Types

Use consistent data types across the API:

1. **Primitive Types**
   - Strings: Use for text data, enums, and simple identifiers
   - Numbers: Use for numeric values, with appropriate precision
   - Booleans: Use for binary states
   - Null: Use to indicate absence of a value

2. **Complex Types**
   - Objects: Use for nested structures
   - Arrays: Use for collections of items
   - Use appropriate nesting based on domain relationships

3. **Special Types**
   - Dates and Times: Use ISO 8601 format with UTC timezone (e.g., `2023-04-01T14:30:00Z`)
   - Durations: Use ISO 8601 duration format (e.g., `P1Y2M3DT4H5M6S`)
   - Identifiers: Use UUIDs in string format with standard UUID formatting
   - Enumerations: Document all possible values

4. **Type Documentation**
   - Document type constraints (min/max, patterns, etc.)
   - Provide examples of valid values
   - Note any special handling requirements

### Response Structure

Standardize response formats:

1. **Success Responses**
   - Return the resource or collection directly as the response body
   - Use HTTP status codes appropriately (200, 201, 204)
   - Include metadata for collections (pagination info, total count)

   ```json
   // Single resource response
   {
     "id": "550e8400-e29b-41d4-a716-446655440000",
     "firstName": "John",
     "lastName": "Smith",
     "dateOfBirth": "1980-01-15",
     "createdAt": "2023-01-01T12:00:00Z",
     "updatedAt": "2023-02-15T09:30:00Z"
   }

   // Collection response
   {
     "data": [
       {
         "id": "550e8400-e29b-41d4-a716-446655440000",
         "firstName": "John",
         "lastName": "Smith"
       },
       {
         "id": "7df78614-0c14-4d6b-8b91-3e0a5e179cd2",
         "firstName": "Jane",
         "lastName": "Doe"
       }
     ],
     "meta": {
       "totalCount": 253,
       "page": 1,
       "limit": 25,
       "hasMore": true
     },
     "links": {
       "self": "/patients?page=1&limit=25",
       "next": "/patients?page=2&limit=25",
       "prev": null
     }
   }
   ```

2. **Error Responses**
   - Provide consistent error response format
   - Use appropriate HTTP status codes
   - Include error code, message, and details
   - Avoid exposing sensitive information in error messages

   ```json
   {
     "error": {
       "code": "VALIDATION_ERROR",
       "message": "The request contains invalid parameters",
       "details": [
         {
           "field": "dateOfBirth",
           "message": "Date of birth must be a valid date"
         },
         {
           "field": "email",
           "message": "Email must be a valid email address"
         }
       ]
     },
     "requestId": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
     "timestamp": "2023-04-01T14:30:00Z"
   }
   ```

3. **Hypermedia Links (HATEOAS)**
   - Consider including links to related resources
   - Use consistent link relation names
   - Include pagination links in collection responses

4. **Response Envelopes**
   - Only use response envelopes when metadata is needed
   - For collections, use a `data` property for the items
   - For single resources, avoid unnecessary nesting

### Error Handling

Implement comprehensive error handling:

1. **HTTP Status Codes**
   - 400 Bad Request: Client error (validation, malformed request)
   - 401 Unauthorized: Authentication required
   - 403 Forbidden: Authentication succeeded, but not authorized
   - 404 Not Found: Resource does not exist
   - 409 Conflict: Request conflicts with current state
   - 422 Unprocessable Entity: Validation errors
   - 429 Too Many Requests: Rate limit exceeded
   - 500 Internal Server Error: Unexpected server error
   - 503 Service Unavailable: Service temporarily unavailable

2. **Error Codes**
   - Define application-specific error codes
   - Use a consistent format (e.g., UPPERCASE_WITH_UNDERSCORES)
   - Group related errors under common prefixes
   - Document all error codes and their meanings

3. **Error Messages**
   - Provide human-readable error messages
   - Be specific about the error cause
   - Avoid technical jargon in user-facing messages
   - NEVER include PHI in error messages

4. **Validation Errors**
   - Return detailed validation errors with field references
   - Explain why the validation failed
   - Provide guidance on how to fix the error when possible

## API Versioning

### Version Strategy

Implement a structured versioning approach:

1. **Version Scheme**
   - Use semantic versioning (MAJOR.MINOR.PATCH)
   - Increment MAJOR for breaking changes
   - Increment MINOR for backward-compatible feature additions
   - Increment PATCH for backward-compatible bug fixes

2. **Version Representation**
   - Include major version in the URL path: `/v1/patients`
   - Document full API version in response headers: `X-API-Version: 1.2.3`
   - Support explicit version requests via Accept header: `Accept: application/json; version=1.2`

3. **Version Lifecycle**
   - Clearly document the support period for each major version
   - Maintain at least one previous major version after a new major release
   - Provide migration guides between versions

4. **Internal Versioning**
   - Use version control for API source code
   - Tag releases in the repository
   - Maintain version changelogs

### Version Compatibility

Ensure smooth transitions between versions:

1. **Backward Compatibility**
   - Maintain backward compatibility within a major version
   - Add new fields and endpoints without breaking existing ones
   - Support old fields with new implementations

2. **Forward Compatibility**
   - Design for extensibility
   - Clients should ignore unknown fields
   - Use versioned media types for content negotiation

3. **Compatibility Testing**
   - Test new versions against old client behavior
   - Ensure old clients work with new server versions
   - Automate compatibility testing in CI/CD pipeline

4. **Feature Toggles**
   - Use feature toggles for gradual rollout
   - Allow opting into new features
   - Enable A/B testing of API changes

### Deprecation Process

Follow a structured deprecation process:

1. **Deprecation Announcement**
   - Document deprecation in API documentation
   - Add deprecation headers: `Deprecation: true` and `Sunset: Sat, 31 Dec 2023 23:59:59 GMT`
   - Provide migration path to alternatives

2. **Deprecation Period**
   - Allow sufficient time before removal (minimum 6 months)
   - Monitor usage of deprecated features
   - Actively notify clients using deprecated features

3. **Communication Channels**
   - Update API documentation
   - Send deprecation notices to registered developers
   - Provide migration examples and support

4. **Removal Process**
   - Remove only after the announced sunset date
   - Ensure proper error responses after removal
   - Maintain documentation of removed features for historical reference

## API Security

### Authentication

Implement robust authentication:

1. **Authentication Methods**
   - OAuth 2.0 with OpenID Connect for user authentication
   - JWT tokens for session management
   - API keys for service-to-service authentication
   - MFA requirement for sensitive operations

2. **Token Management**
   - Short-lived access tokens (15-60 minutes)
   - Refresh token rotation
   - Secure token storage guidelines for clients
   - Token revocation endpoints

3. **Authentication Headers**
   - Use `Authorization: Bearer <token>` for JWT authentication
   - Use `X-API-Key: <key>` for API key authentication
   - Document required headers clearly

4. **Security Considerations**
   - HTTPS for all endpoints (no HTTP support)
   - Secure cookie settings for web clients
   - Protection against token stealing (fingerprinting, etc.)
   - Rate limiting on authentication endpoints

### Authorization

Implement fine-grained authorization:

1. **Permission Model**
   - Role-based access control (RBAC) as the foundation
   - Attribute-based access control (ABAC) for fine-grained permissions
   - Resource ownership and sharing model
   - Clinical relationship-based access control

2. **Authorization Checks**
   - Verify permissions for all operations
   - Check at both resource and field levels
   - Apply consistent authorization patterns
   - Document required permissions for each endpoint

3. **Scope-Based Access**
   - Define API scopes for different access levels
   - Validate token scopes against endpoint requirements
   - Restrict scope issuance based on user role
   - Document required scopes for each endpoint

4. **HIPAA Authorization**
   - Implement required HIPAA authorization checks
   - Verify clinical relationships for PHI access
   - Maintain authorization audit trails
   - Support Break Glass procedures for emergency access

### Input Validation

Implement thorough input validation:

1. **Validation Approaches**
   - Schema-based validation for all requests
   - Type checking and conversion
   - Business rule validation
   - Cross-field validation

2. **Validation Implementation**
   - Use Pydantic models for request validation
   - Define reusable validation components
   - Implement custom validators for complex rules
   - Provide clear validation error messages

3. **Security Validations**
   - Input sanitization against injection attacks
   - Length and size limits for all inputs
   - Pattern matching for structured data
   - Content type validation

4. **Validation Context**
   - Context-specific validation (create vs. update)
   - Role-specific validation rules
   - Environment-specific validation (dev vs. prod)
   - Validation rule documentation

### Output Sanitization

Secure response data:

1. **PHI Protection**
   - Review all responses to prevent PHI leakage
   - Implement field-level access control in responses
   - Sanitize error messages to remove PHI
   - Document PHI handling for each endpoint

2. **Data Minimization**
   - Return only necessary fields by default
   - Support field selection for customized responses
   - Filter sensitive data based on authorization
   - Document field sensitivity levels

3. **Output Encoding**
   - Properly encode all output to prevent XSS
   - Set appropriate content security headers
   - Validate nested object safety
   - Secure serialization process

4. **Response Filtering**
   - Implement response post-processing pipeline
   - Apply role-based field filtering
   - Redact sensitive information based on context
   - Log sanitization actions for auditing

## Performance Considerations

### Pagination

Implement efficient pagination:

1. **Pagination Methods**
   - Offset-based: `?offset=100&limit=25`
   - Cursor-based: `?cursor=eyJpZCI6IjEwMCJ9&limit=25`
   - Page-based: `?page=5&limit=25`
   - Choose based on dataset size and access patterns

2. **Pagination Response**
   - Include metadata about pagination state
   - Provide links for next, previous, first, and last pages
   - Include total count when feasible
   - Document pagination behavior

3. **Performance Optimization**
   - Use cursor-based pagination for large datasets
   - Apply database indexes to support efficient pagination
   - Set reasonable default and maximum page sizes
   - Optimize counting mechanisms

4. **Edge Cases**
   - Handle empty result sets gracefully
   - Manage invalid pagination parameters
   - Account for data changes between pages
   - Document pagination limitations

### Filtering

Support flexible result filtering:

1. **Filter Parameters**
   - Use consistent parameter format: `filter[field]=value`
   - Support multiple filters: `filter[field1]=value1&filter[field2]=value2`
   - Allow operator selection: `filter[field][operator]=value`
   - Support complex logical operations (AND, OR, NOT)

2. **Filter Operators**
   - Equality: `filter[status]=active`
   - Comparison: `filter[age][gt]=18`
   - Range: `filter[created][between]=2023-01-01,2023-12-31`
   - Pattern matching: `filter[name][contains]=smith`

3. **Security Considerations**
   - Restrict filterable fields based on authorization
   - Validate filter values and operators
   - Prevent injection attacks in filter parameters
   - Set execution limits for complex filters

4. **Performance Optimization**
   - Apply database indexes for filtered fields
   - Transform filters to efficient database queries
   - Limit complexity of allowed filters
   - Document performance implications of filters

### Rate Limiting

Implement appropriate rate limiting:

1. **Rate Limit Design**
   - Define limits based on endpoint sensitivity and load
   - Apply different limits based on authentication level
   - Consider both short-term and long-term limits
   - Document rate limits clearly

2. **Rate Limit Headers**
   - `X-RateLimit-Limit`: Maximum requests allowed in period
   - `X-RateLimit-Remaining`: Requests remaining in current period
   - `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)
   - `Retry-After`: Seconds to wait when rate limited

3. **Rate Limit Response**
   - Return 429 Too Many Requests when limit exceeded
   - Provide clear error message
   - Include retry guidance
   - Maintain consistent rate limit behavior

4. **Rate Limit Implementation**
   - Distributed rate limiting with Redis
   - Token bucket or leaky bucket algorithm
   - Graceful degradation during overload
   - Monitoring and alerting for rate limit issues

### Caching

Implement effective caching strategies:

1. **Cache Headers**
   - `Cache-Control`: Primary caching directive
   - `ETag`: Entity tag for conditional requests
   - `Last-Modified`: Resource last modification time
   - `Vary`: Headers that affect response content

2. **Caching Policy**
   - Define cacheable resources and duration
   - Public vs. private caching directives
   - Versioned resource URLs for cache busting
   - No caching for PHI or sensitive data

3. **Conditional Requests**
   - Support If-Modified-Since for time-based validation
   - Support If-None-Match for ETag validation
   - Return 304 Not Modified when appropriate
   - Document conditional request support

4. **Cache Invalidation**
   - Cache invalidation on resource updates
   - Cache purging mechanisms
   - Versioned API responses
   - Event-based cache updates

## Documentation

### OpenAPI Specification

Use OpenAPI for API documentation:

1. **Specification Approach**
   - Maintain OpenAPI 3.0+ specification
   - Generate specification from code annotations
   - Include complete request/response examples
   - Document all parameters and response fields

2. **Specification Organization**
   - Group endpoints by resource or domain area
   - Use tags for logical grouping
   - Include operation summaries and descriptions
   - Document security requirements

3. **Schema Documentation**
   - Define reusable components
   - Document all properties with descriptions
   - Include constraints and validation rules
   - Provide example values

4. **Documentation Generation**
   - Generate interactive documentation (Swagger UI)
   - Create PDF/HTML static documentation
   - Maintain versioned documentation
   - Automate documentation updates

### Code Examples

Provide comprehensive code examples:

1. **Example Coverage**
   - Include examples for all common operations
   - Cover success and error scenarios
   - Demonstrate authentication and authorization
   - Show complex query parameter usage

2. **Language Support**
   - Provide examples in multiple languages (Python, JavaScript, etc.)
   - Include both raw HTTP and library-based examples
   - Show both request and response examples
   - Keep examples up to date with API changes

3. **Example Formats**
   - Command-line examples (curl, httpie)
   - SDKs and client libraries
   - Interactive examples in documentation
   - Postman collection or similar

4. **Tutorials and Guides**
   - Step-by-step implementation guides
   - Common usage scenarios
   - Best practices for using the API
   - Performance optimization tips

### Reference Documentation

Maintain comprehensive reference documentation:

1. **Endpoint Documentation**
   - Complete description of each endpoint
   - Parameter details and constraints
   - Response format and status codes
   - Authorization requirements

2. **Object Documentation**
   - Field-level descriptions
   - Data types and formats
   - Validation rules
   - Relationships to other objects

3. **Error Documentation**
   - List of possible error codes
   - Error response format
   - Troubleshooting guidance
   - Resolution strategies

4. **Background Information**
   - Concepts and domain terminology
   - Architecture overview
   - Integration patterns
   - Migration guides

## Implementation Guidelines

### FastAPI Implementation

Implementation guidelines for FastAPI:

1. **Project Structure**
   - Organize routes by domain area
   - Separate routers for different resource types
   - Group related functionality
   - Maintain clean imports

   ```
   /app
     /api
       /v1
         /patients
           router.py           # Patient endpoints
           schemas.py          # Request/response models
           dependencies.py     # Endpoint dependencies
         /treatments
           router.py
           schemas.py
           dependencies.py
       /dependencies          # Shared API dependencies
       /schemas              # Shared schema models
     /core                   # Core application code
     /domain                 # Domain models and logic
     /services               # Application services
     /infrastructure         # External interfaces
   ```

2. **Route Definition**
   - Use appropriate HTTP methods
   - Implement consistent URL patterns
   - Group related endpoints under routers
   - Apply common dependencies at router level

   ```python
   from fastapi import APIRouter, Depends, HTTPException, status
   from typing import List, Optional
   
   from app.api.dependencies.auth import get_current_user
   from app.api.dependencies.db import get_db
   from app.domain.models import User
   from app.services.patient import PatientService
   from .schemas import PatientCreate, PatientResponse, PatientUpdate
   
   router = APIRouter(prefix="/patients", tags=["Patients"])
   
   @router.get("/", response_model=List[PatientResponse])
   async def get_patients(
       skip: int = 0,
       limit: int = 100,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db),
       patient_service: PatientService = Depends()
   ):
       """
       Get a list of patients the current user has access to.
       """
       return await patient_service.get_patients(
           user_id=current_user.id,
           skip=skip,
           limit=limit
       )
   
   @router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
   async def create_patient(
       patient: PatientCreate,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db),
       patient_service: PatientService = Depends()
   ):
       """
       Create a new patient record.
       """
       return await patient_service.create_patient(
           patient=patient,
           created_by=current_user.id
       )
   ```

3. **Schema Definition**
   - Use Pydantic models for request/response schemas
   - Apply validation rules declaratively
   - Implement schema inheritance for common patterns
   - Document schemas with clear field descriptions

   ```python
   from pydantic import BaseModel, Field, validator
   from datetime import date
   from typing import Optional
   from uuid import UUID
   
   class PatientBase(BaseModel):
       first_name: str = Field(..., description="Patient's first name")
       last_name: str = Field(..., description="Patient's last name")
       date_of_birth: date = Field(..., description="Patient's date of birth")
       gender: str = Field(..., description="Patient's gender identity")
       
       @validator("gender")
       def validate_gender(cls, v):
           allowed_values = ["male", "female", "non-binary", "other", "prefer_not_to_say"]
           if v.lower() not in allowed_values:
               raise ValueError(f"Gender must be one of: {', '.join(allowed_values)}")
           return v
   
   class PatientCreate(PatientBase):
       # Fields required for creation
       medical_record_number: Optional[str] = Field(None, description="External medical record number")
   
   class PatientUpdate(BaseModel):
       # All fields optional for updates
       first_name: Optional[str] = Field(None, description="Patient's first name")
       last_name: Optional[str] = Field(None, description="Patient's last name")
       date_of_birth: Optional[date] = Field(None, description="Patient's date of birth")
       gender: Optional[str] = Field(None, description="Patient's gender identity")
       
       @validator("gender")
       def validate_gender(cls, v):
           if v is None:
               return v
           allowed_values = ["male", "female", "non-binary", "other", "prefer_not_to_say"]
           if v.lower() not in allowed_values:
               raise ValueError(f"Gender must be one of: {', '.join(allowed_values)}")
           return v
   
   class PatientResponse(PatientBase):
       id: UUID = Field(..., description="Patient's unique identifier")
       created_at: datetime = Field(..., description="When the record was created")
       updated_at: datetime = Field(..., description="When the record was last updated")
       
       class Config:
           orm_mode = True
   ```

4. **Service Layer**
   - Implement business logic in service layer
   - Inject service dependencies
   - Apply authorization in service methods
   - Handle exceptions and error cases

   ```python
   from fastapi import Depends, HTTPException, status
   from sqlalchemy.orm import Session
   from typing import List, Optional
   from uuid import UUID
   
   from app.core.db.session import get_db
   from app.core.security import get_authorization_service
   from app.domain.models import Patient
   from app.domain.repositories import PatientRepository
   
   class PatientService:
       def __init__(
           self,
           db: Session = Depends(get_db),
           patient_repository: PatientRepository = Depends(),
           authorization_service: AuthorizationService = Depends(get_authorization_service)
       ):
           self.db = db
           self.patient_repository = patient_repository
           self.authorization_service = authorization_service
       
       async def get_patients(
           self,
           user_id: UUID,
           skip: int = 0,
           limit: int = 100
       ) -> List[Patient]:
           """Get patients the user has access to."""
           # Check if user can list patients
           if not self.authorization_service.can_list_patients(user_id):
               raise HTTPException(
                   status_code=status.HTTP_403_FORBIDDEN,
                   detail="Not authorized to list patients"
               )
               
           # Get patients with filtering based on user's access
           return await self.patient_repository.get_patients_for_user(
               user_id=user_id,
               skip=skip,
               limit=limit
           )
       
       async def create_patient(
           self,
           patient: PatientCreate,
           created_by: UUID
       ) -> Patient:
           """Create a new patient."""
           # Check if user can create patients
           if not self.authorization_service.can_create_patient(created_by):
               raise HTTPException(
                   status_code=status.HTTP_403_FORBIDDEN,
                   detail="Not authorized to create patients"
               )
               
           # Create patient
           return await self.patient_repository.create_patient(
               patient=patient,
               created_by=created_by
           )
   ```

### Middleware

Implement middleware for cross-cutting concerns:

1. **Authentication Middleware**
   - Token validation and verification
   - User information extraction
   - Authentication failure handling
   - Session management

2. **Audit Logging Middleware**
   - Request/response logging
   - PHI access logging
   - Performance metrics collection
   - Correlation ID tracking

3. **Error Handling Middleware**
   - Global exception handling
   - Consistent error formatting
   - Error categorization
   - PHI sanitization in errors

4. **Security Middleware**
   - CORS configuration
   - Content security policies
   - Rate limiting
   - Request validation

### Dependency Injection

Use dependency injection effectively:

1. **Common Dependencies**
   - Database sessions
   - Authentication services
   - Repositories
   - Service instances

2. **Dependency Scopes**
   - Request-scoped dependencies
   - Singleton dependencies
   - Custom dependency scopes
   - Dependency caching

3. **Dependency Hierarchy**
   - Layer dependencies appropriately
   - Avoid circular dependencies
   - Use factory patterns for complex dependencies
   - Document dependency relationships

4. **Testing Dependencies**
   - Override dependencies in tests
   - Mock external dependencies
   - Stub database dependencies
   - Test-specific dependency providers

### Testing

Comprehensive API testing approach:

1. **Unit Testing**
   - Test individual components
   - Mock dependencies
   - Test edge cases
   - Measure code coverage

2. **Integration Testing**
   - Test API endpoints
   - Test database interactions
   - Test service integration
   - Use test databases

3. **End-to-End Testing**
   - Test complete flows
   - Test authentication and authorization
   - Test error handling
   - Test performance under load

4. **Security Testing**
   - Test input validation
   - Test authorization enforcement
   - Test rate limiting
   - Test against OWASP Top 10

## Conclusion

This API design guide establishes the standards and best practices for developing RESTful APIs within the Novamind Digital Twin Platform. By following these guidelines, we ensure that our APIs are consistent, secure, maintainable, performant, and usable.

All API designs must adhere to these guidelines and undergo a formal review process before implementation. The guidelines will be periodically reviewed and updated to incorporate new best practices and lessons learned.

For specific implementation examples or detailed guidance on particular aspects of API design, refer to the code samples and tutorials in the developer documentation.   - Rate limiting on authentication endpoints

### Authorization

Implement fine-grained authorization:

1. **Permission Model**
   - Role-based access control (RBAC) as the foundation
   - Attribute-based access control (ABAC) for fine-grained permissions
   - Resource ownership and sharing model
   - Clinical relationship-based access control

2. **Authorization Checks**
   - Verify permissions for all operations
   - Check at both resource and field levels
   - Apply consistent authorization patterns
   - Document required permissions for each endpoint

3. **Scope-Based Access**
   - Define API scopes for different access levels
   - Validate token scopes against endpoint requirements
   - Restrict scope issuance based on user role
   - Document required scopes for each endpoint

4. **HIPAA Authorization**
   - Implement required HIPAA authorization checks
   - Verify clinical relationships for PHI access
   - Maintain authorization audit trails
   - Support Break Glass procedures for emergency access

### Input Validation

Implement thorough input validation:

1. **Validation Approaches**
   - Schema-based validation for all requests
   - Type checking and conversion
   - Business rule validation
   - Cross-field validation

2. **Validation Implementation**
   - Use Pydantic models for request validation
   - Define reusable validation components
   - Implement custom validators for complex rules
   - Provide clear validation error messages

3. **Security Validations**
   - Input sanitization against injection attacks
   - Length and size limits for all inputs
   - Pattern matching for structured data
   - Content type validation

4. **Validation Context**
   - Context-specific validation (create vs. update)
   - Role-specific validation rules
   - Environment-specific validation (dev vs. prod)
   - Validation rule documentation

### Output Sanitization

Secure response data:

1. **PHI Protection**
   - Review all responses to prevent PHI leakage
   - Implement field-level access control in responses
   - Sanitize error messages to remove PHI
   - Document PHI handling for each endpoint

2. **Data Minimization**
   - Return only necessary fields by default
   - Support field selection for customized responses
   - Filter sensitive data based on authorization
   - Document field sensitivity levels

3. **Output Encoding**
   - Properly encode all output to prevent XSS
   - Set appropriate content security headers
   - Validate nested object safety
   - Secure serialization process

4. **Response Filtering**
   - Implement response post-processing pipeline
   - Apply role-based field filtering
   - Redact sensitive information based on context
   - Log sanitization actions for auditing

## Performance Considerations

### Pagination

Implement efficient pagination:

1. **Pagination Methods**
   - Offset-based: `?offset=100&limit=25`
   - Cursor-based: `?cursor=eyJpZCI6IjEwMCJ9&limit=25`
   - Page-based: `?page=5&limit=25`
   - Choose based on dataset size and access patterns

2. **Pagination Response**
   - Include metadata about pagination state
   - Provide links for next, previous, first, and last pages
   - Include total count when feasible
   - Document pagination behavior

3. **Performance Optimization**
   - Use cursor-based pagination for large datasets
   - Apply database indexes to support efficient pagination
   - Set reasonable default and maximum page sizes
   - Optimize counting mechanisms

4. **Edge Cases**
   - Handle empty result sets gracefully
   - Manage invalid pagination parameters
   - Account for data changes between pages
   - Document pagination limitations

### Filtering

Support flexible result filtering:

1. **Filter Parameters**
   - Use consistent parameter format: `filter[field]=value`
   - Support multiple filters: `filter[field1]=value1&filter[field2]=value2`
   - Allow operator selection: `filter[field][operator]=value`
   - Support complex logical operations (AND, OR, NOT)

2. **Filter Operators**
   - Equality: `filter[status]=active`
   - Comparison: `filter[age][gt]=18`
   - Range: `filter[created][between]=2023-01-01,2023-12-31`
   - Pattern matching: `filter[name][contains]=smith`

3. **Security Considerations**
   - Restrict filterable fields based on authorization
   - Validate filter values and operators
   - Prevent injection attacks in filter parameters
   - Set execution limits for complex filters

4. **Performance Optimization**
   - Apply database indexes for filtered fields
   - Transform filters to efficient database queries
   - Limit complexity of allowed filters
   - Document performance implications of filters

### Rate Limiting

Implement appropriate rate limiting:

1. **Rate Limit Design**
   - Define limits based on endpoint sensitivity and load
   - Apply different limits based on authentication level
   - Consider both short-term and long-term limits
   - Document rate limits clearly

2. **Rate Limit Headers**
   - `X-RateLimit-Limit`: Maximum requests allowed in period
   - `X-RateLimit-Remaining`: Requests remaining in current period
   - `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)
   - `Retry-After`: Seconds to wait when rate limited

3. **Rate Limit Response**
   - Return 429 Too Many Requests when limit exceeded
   - Provide clear error message
   - Include retry guidance
   - Maintain consistent rate limit behavior

4. **Rate Limit Implementation**
   - Distributed rate limiting with Redis
   - Token bucket or leaky bucket algorithm
   - Graceful degradation during overload
   - Monitoring and alerting for rate limit issues

### Caching

Implement effective caching strategies:

1. **Cache Headers**
   - `Cache-Control`: Primary caching directive
   - `ETag`: Entity tag for conditional requests
   - `Last-Modified`: Resource last modification time
   - `Vary`: Headers that affect response content

2. **Caching Policy**
   - Define cacheable resources and duration
   - Public vs. private caching directives
   - Versioned resource URLs for cache busting
   - No caching for PHI or sensitive data

3. **Conditional Requests**
   - Support If-Modified-Since for time-based validation
   - Support If-None-Match for ETag validation
   - Return 304 Not Modified when appropriate
   - Document conditional request support

4. **Cache Invalidation**
   - Cache invalidation on resource updates
   - Cache purging mechanisms
   - Versioned API responses
   - Event-based cache updates

## Documentation

### OpenAPI Specification

Use OpenAPI for API documentation:

1. **Specification Approach**
   - Maintain OpenAPI 3.0+ specification
   - Generate specification from code annotations
   - Include complete request/response examples
   - Document all parameters and response fields

2. **Specification Organization**
   - Group endpoints by resource or domain area
   - Use tags for logical grouping
   - Include operation summaries and descriptions
   - Document security requirements

3. **Schema Documentation**
   - Define reusable components
   - Document all properties with descriptions
   - Include constraints and validation rules
   - Provide example values

4. **Documentation Generation**
   - Generate interactive documentation (Swagger UI)
   - Create PDF/HTML static documentation
   - Maintain versioned documentation
   - Automate documentation updates

### Code Examples

Provide comprehensive code examples:

1. **Example Coverage**
   - Include examples for all common operations
   - Cover success and error scenarios
   - Demonstrate authentication and authorization
   - Show complex query parameter usage

2. **Language Support**
   - Provide examples in multiple languages (Python, JavaScript, etc.)
   - Include both raw HTTP and library-based examples
   - Show both request and response examples
   - Keep examples up to date with API changes

3. **Example Formats**
   - Command-line examples (curl, httpie)
   - SDKs and client libraries
   - Interactive examples in documentation
   - Postman collection or similar

4. **Tutorials and Guides**
   - Step-by-step implementation guides
   - Common usage scenarios
   - Best practices for using the API
   - Performance optimization tips

### Reference Documentation

Maintain comprehensive reference documentation:

1. **Endpoint Documentation**
   - Complete description of each endpoint
   - Parameter details and constraints
   - Response format and status codes
   - Authorization requirements

2. **Object Documentation**
   - Field-level descriptions
   - Data types and formats
   - Validation rules
   - Relationships to other objects

3. **Error Documentation**
   - List of possible error codes
   - Error response format
   - Troubleshooting guidance
   - Resolution strategies

4. **Background Information**
   - Concepts and domain terminology
   - Architecture overview
   - Integration patterns
   - Migration guides

## Implementation Guidelines

### FastAPI Implementation

Implementation guidelines for FastAPI:

1. **Project Structure**
   - Organize routes by domain area
   - Separate routers for different resource types
   - Group related functionality
   - Maintain clean imports

   ```
   /app
     /api
       /v1
         /patients
           router.py           # Patient endpoints
           schemas.py          # Request/response models
           dependencies.py     # Endpoint dependencies
         /treatments
           router.py
           schemas.py
           dependencies.py
       /dependencies          # Shared API dependencies
       /schemas              # Shared schema models
     /core                   # Core application code
     /domain                 # Domain models and logic
     /services               # Application services
     /infrastructure         # External interfaces
   ```

2. **Route Definition**
   - Use appropriate HTTP methods
   - Implement consistent URL patterns
   - Group related endpoints under routers
   - Apply common dependencies at router level

   ```python
   from fastapi import APIRouter, Depends, HTTPException, status
   from typing import List, Optional
   
   from app.api.dependencies.auth import get_current_user
   from app.api.dependencies.db import get_db
   from app.domain.models import User
   from app.services.patient import PatientService
   from .schemas import PatientCreate, PatientResponse, PatientUpdate
   
   router = APIRouter(prefix="/patients", tags=["Patients"])
   
   @router.get("/", response_model=List[PatientResponse])
   async def get_patients(
       skip: int = 0,
       limit: int = 100,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db),
       patient_service: PatientService = Depends()
   ):
       """
       Get a list of patients the current user has access to.
       """
       return await patient_service.get_patients(
           user_id=current_user.id,
           skip=skip,
           limit=limit
       )
   
   @router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
   async def create_patient(
       patient: PatientCreate,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db),
       patient_service: PatientService = Depends()
   ):
       """
       Create a new patient record.
       """
       return await patient_service.create_patient(
           patient=patient,
           created_by=current_user.id
       )
   ```

3. **Schema Definition**
   - Use Pydantic models for request/response schemas
   - Apply validation rules declaratively
   - Implement schema inheritance for common patterns
   - Document schemas with clear field descriptions

   ```python
   from pydantic import BaseModel, Field, validator
   from datetime import date
   from typing import Optional
   from uuid import UUID
   
   class PatientBase(BaseModel):
       first_name: str = Field(..., description="Patient's first name")
       last_name: str = Field(..., description="Patient's last name")
       date_of_birth: date = Field(..., description="Patient's date of birth")
       gender: str = Field(..., description="Patient's gender identity")
       
       @validator("gender")
       def validate_gender(cls, v):
           allowed_values = ["male", "female", "non-binary", "other", "prefer_not_to_say"]
           if v.lower() not in allowed_values:
               raise ValueError(f"Gender must be one of: {', '.join(allowed_values)}")
           return v
   
   class PatientCreate(PatientBase):
       # Fields required for creation
       medical_record_number: Optional[str] = Field(None, description="External medical record number")
   
   class PatientUpdate(BaseModel):
       # All fields optional for updates
       first_name: Optional[str] = Field(None, description="Patient's first name")
       last_name: Optional[str] = Field(None, description="Patient's last name")
       date_of_birth: Optional[date] = Field(None, description="Patient's date of birth")
       gender: Optional[str] = Field(None, description="Patient's gender identity")
       
       @validator("gender")
       def validate_gender(cls, v):
           if v is None:
               return v
           allowed_values = ["male", "female", "non-binary", "other", "prefer_not_to_say"]
           if v.lower() not in allowed_values:
               raise ValueError(f"Gender must be one of: {', '.join(allowed_values)}")
           return v
   
   class PatientResponse(PatientBase):
       id: UUID = Field(..., description="Patient's unique identifier")
       created_at: datetime = Field(..., description="When the record was created")
       updated_at: datetime = Field(..., description="When the record was last updated")
       
       class Config:
           orm_mode = True
   ```

4. **Service Layer**
   - Implement business logic in service layer
   - Inject service dependencies
   - Apply authorization in service methods
   - Handle exceptions and error cases

   ```python
   from fastapi import Depends, HTTPException, status
   from sqlalchemy.orm import Session
   from typing import List, Optional
   from uuid import UUID
   
   from app.core.db.session import get_db
   from app.core.security import get_authorization_service
   from app.domain.models import Patient
   from app.domain.repositories import PatientRepository
   
   class PatientService:
       def __init__(
           self,
           db: Session = Depends(get_db),
           patient_repository: PatientRepository = Depends(),
           authorization_service: AuthorizationService = Depends(get_authorization_service)
       ):
           self.db = db
           self.patient_repository = patient_repository
           self.authorization_service = authorization_service
       
       async def get_patients(
           self,
           user_id: UUID,
           skip: int = 0,
           limit: int = 100
       ) -> List[Patient]:
           """Get patients the user has access to."""
           # Check if user can list patients
           if not self.authorization_service.can_list_patients(user_id):
               raise HTTPException(
                   status_code=status.HTTP_403_FORBIDDEN,
                   detail="Not authorized to list patients"
               )
               
           # Get patients with filtering based on user's access
           return await self.patient_repository.get_patients_for_user(
               user_id=user_id,
               skip=skip,
               limit=limit
           )
       
       async def create_patient(
           self,
           patient: PatientCreate,
           created_by: UUID
       ) -> Patient:
           """Create a new patient."""
           # Check if user can create patients
           if not self.authorization_service.can_create_patient(created_by):
               raise HTTPException(
                   status_code=status.HTTP_403_FORBIDDEN,
                   detail="Not authorized to create patients"
               )
               
           # Create patient
           return await self.patient_repository.create_patient(
               patient=patient,
               created_by=created_by
           )
   ```

### Middleware

Implement middleware for cross-cutting concerns:

1. **Authentication Middleware**
   - Token validation and verification
   - User information extraction
   - Authentication failure handling
   - Session management

2. **Audit Logging Middleware**
   - Request/response logging
   - PHI access logging
   - Performance metrics collection
   - Correlation ID tracking

3. **Error Handling Middleware**
   - Global exception handling
   - Consistent error formatting
   - Error categorization
   - PHI sanitization in errors

4. **Security Middleware**
   - CORS configuration
   - Content security policies
   - Rate limiting
   - Request validation

### Dependency Injection

Use dependency injection effectively:

1. **Common Dependencies**
   - Database sessions
   - Authentication services
   - Repositories
   - Service instances

2. **Dependency Scopes**
   - Request-scoped dependencies
   - Singleton dependencies
   - Custom dependency scopes
   - Dependency caching

3. **Dependency Hierarchy**
   - Layer dependencies appropriately
   - Avoid circular dependencies
   - Use factory patterns for complex dependencies
   - Document dependency relationships

4. **Testing Dependencies**
   - Override dependencies in tests
   - Mock external dependencies
   - Stub database dependencies
   - Test-specific dependency providers

### Testing

Comprehensive API testing approach:

1. **Unit Testing**
   - Test individual components
   - Mock dependencies
   - Test edge cases
   - Measure code coverage

2. **Integration Testing**
   - Test API endpoints
   - Test database interactions
   - Test service integration
   - Use test databases

3. **End-to-End Testing**
   - Test complete flows
   - Test authentication and authorization
   - Test error handling
   - Test performance under load

4. **Security Testing**
   - Test input validation
   - Test authorization enforcement
   - Test rate limiting
   - Test against OWASP Top 10

## Conclusion

This API design guide establishes the standards and best practices for developing RESTful APIs within the Novamind Digital Twin Platform. By following these guidelines, we ensure that our APIs are consistent, secure, maintainable, performant, and usable.

All API designs must adhere to these guidelines and undergo a formal review process before implementation. The guidelines will be periodically reviewed and updated to incorporate new best practices and lessons learned.

For specific implementation examples or detailed guidance on particular aspects of API design, refer to the code samples and tutorials in the developer documentation.
