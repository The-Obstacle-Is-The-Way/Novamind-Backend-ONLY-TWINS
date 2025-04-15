"""
SQLAlchemy implementation of Patient repository for the Novamind Digital Twin platform.

This module provides a concrete implementation of the patient repository
interface using SQLAlchemy for database operations.
"""
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.patient import Patient as PatientEntity
from app.infrastructure.persistence.sqlalchemy.models.patient import Patient as PatientModel


class PatientRepository:
    """
    SQLAlchemy implementation of the patient repository interface.
    
    This class is responsible for translating between domain entities
    and database models, and for performing database operations.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    async def get_by_id(self, id: str) -> Optional[PatientEntity]:
        """
        Get a patient by ID.
        
        Args:
            id: Patient unique identifier
            
        Returns:
            Optional[PatientEntity]: Patient entity or None if not found
        """
        try:
            query = select(PatientModel).where(PatientModel.id == id)
            result = await self.session.execute(query)
            patient_model = result.scalar_one_or_none()
            
            if not patient_model:
                return None
                
            # Convert model to dict
            patient_dict = {c.name: getattr(patient_model, c.name) for c in PatientModel.__table__.columns}
            
            # Parse JSON fields
            for json_field in ["medical_history", "medications", "allergies", "treatment_notes"]:
                if patient_dict.get(json_field) and isinstance(patient_dict[json_field], str):
                    try:
                        patient_dict[json_field] = json.loads(patient_dict[json_field])
                    except json.JSONDecodeError:
                        patient_dict[json_field] = []
                elif patient_dict.get(json_field) is None:
                    patient_dict[json_field] = []
            
            # Create domain entity
            return PatientEntity(**patient_dict)
            
        except Exception as e:
            self.logger.error(f"Error retrieving patient with ID {id}: {str(e)}")
            return None
    
    async def get_all(self) -> List[PatientEntity]:
        """
        Get all patients.
        
        Returns:
            List[PatientEntity]: List of all patient entities
        """
        try:
            query = select(PatientModel)
            result = await self.session.execute(query)
            patient_models = result.scalars().all()
            
            patients = []
            for patient_model in patient_models:
                # Convert model to dict
                patient_dict = {c.name: getattr(patient_model, c.name) for c in PatientModel.__table__.columns}
                
                # Parse JSON fields
                for json_field in ["medical_history", "medications", "allergies", "treatment_notes"]:
                    if patient_dict.get(json_field) and isinstance(patient_dict[json_field], str):
                        try:
                            patient_dict[json_field] = json.loads(patient_dict[json_field])
                        except json.JSONDecodeError:
                            patient_dict[json_field] = []
                    elif patient_dict.get(json_field) is None:
                        patient_dict[json_field] = []
                
                # Create domain entity
                try:
                    patients.append(PatientEntity(**patient_dict))
                except Exception as entity_creation_error:
                    self.logger.error(f"Failed to create PatientEntity for model ID {patient_model.id}: {entity_creation_error}")
                    # Decide how to handle: skip this patient, raise error, etc.
                
            return patients
            
        except Exception as e:
            self.logger.error(f"Error retrieving all patients: {str(e)}")
            return []
    
    async def create(self, patient_entity: PatientEntity) -> PatientEntity:
        """
        Create a new patient.
        
        Args:
            patient_entity: Patient domain entity to create
            
        Returns:
            PatientEntity: Created patient entity with potentially updated fields (like id, created_at)
        """
        try:
            # Convert entity to dictionary suitable for the model
            patient_data = patient_entity.dict()

            # Remove fields not present in the model or handled automatically (like id if generated by DB)
            model_columns = {c.name for c in PatientModel.__table__.columns}
            model_data = {k: v for k, v in patient_data.items() if k in model_columns}

            # Encrypt fields and store them in the model's '_field' columns
            # Example (needs proper encryption service):
            # model_data['_first_name'] = encrypt(patient_entity.first_name)
            # ... encrypt other fields ...
            # Remove original non-underscored fields if they exist in model_data and are not actual columns
            # e.g., del model_data['first_name'] if '_first_name' is the actual column used

            # Handle JSON serialization for relevant fields if stored as Text
            # for json_field_entity in ["medical_history", "medications", "allergies", "treatment_notes", "extra_data"]:
            #     model_field = f"_{json_field_entity}"
            #     if model_field in model_columns and hasattr(patient_entity, json_field_entity):
            #         value = getattr(patient_entity, json_field_entity)
            #         # Encrypt the JSON string if necessary
            #         model_data[model_field] = json.dumps(value) if value is not None else None

            # Ensure timestamps are set (SQLAlchemy default might handle this too)
            now = datetime.utcnow()
            model_data.setdefault('created_at', now)
            model_data.setdefault('updated_at', now)
            
            # Use ORM instance for creation
            new_patient_model = PatientModel(**model_data)
            self.session.add(new_patient_model)
            await self.session.flush() # Assigns ID and other db-generated values
            await self.session.refresh(new_patient_model)
            await self.session.commit()
            
            # Convert the persisted model back to an entity to return
            # This ensures the returned entity includes DB-generated values (ID, timestamps)
            persisted_dict = {c.name: getattr(new_patient_model, c.name) for c in PatientModel.__table__.columns}
            # ... decrypt/parse fields ...
            return PatientEntity(**persisted_dict)
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error creating patient: {str(e)}", exc_info=True)
            raise # Re-raise the exception for the service layer to handle
    
    async def update(self, patient_entity: PatientEntity) -> Optional[PatientEntity]:
        """
        Update an existing patient.
        
        Args:
            patient_entity: Patient domain entity with updated data
            
        Returns:
            Optional[PatientEntity]: Updated patient entity or None if not found
        """
        if not patient_entity.id:
             self.logger.error("Cannot update patient without an ID.")
             return None # Or raise ValueError

        try:
            # Fetch the existing model
            existing_model = await self.session.get(PatientModel, patient_entity.id)
            
            if not existing_model:
                self.logger.warning(f"Patient with ID {patient_entity.id} not found for update.")
                return None

            # Convert entity update data to dictionary suitable for the model
            update_data = patient_entity.dict(exclude_unset=True) # Only include fields explicitly set in the entity
            
            # Prepare data for model update (handle encryption, JSON)
            model_columns = {c.name for c in PatientModel.__table__.columns}
            model_update_data = {}
            for key, value in update_data.items():
                 if key == 'id': # Don't update primary key
                     continue
                 # Map entity field to potentially encrypted model field (e.g., 'first_name' -> '_first_name')
                 # This requires knowledge of the mapping and encryption needs
                 model_key = key # Replace with actual mapping logic (e.g., f"_{key}" if encrypted)
                 if model_key in model_columns:
                     # Encrypt value if needed
                     # Serialize to JSON if needed
                     model_update_data[model_key] = value # Replace with processed value


            # Encrypt/Serialize specific fields as needed (similar to create method)
            # ... encryption/serialization logic ...

            # Set updated timestamp
            model_update_data['updated_at'] = datetime.utcnow()
            
            # Update the model instance fields
            for key, value in model_update_data.items():
                setattr(existing_model, key, value)

            await self.session.flush()
            await self.session.refresh(existing_model)
            await self.session.commit()
            
            # Convert updated model back to entity
            updated_dict = {c.name: getattr(existing_model, c.name) for c in PatientModel.__table__.columns}
            # ... decryption/parsing logic ...
            return PatientEntity(**updated_dict)
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating patient with ID {patient_entity.id}: {str(e)}", exc_info=True)
            raise # Re-raise

    async def delete(self, id: str) -> bool:
        """
        Delete a patient by ID.
        
        Args:
            id: Patient unique identifier
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Use ORM delete
            patient_model = await self.session.get(PatientModel, id)
            if patient_model:
                await self.session.delete(patient_model)
                await self.session.commit()
                self.logger.info(f"Successfully deleted patient with ID {id}")
                return True
            else:
                self.logger.warning(f"Patient with ID {id} not found for deletion.")
                return False
                
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error deleting patient with ID {id}: {str(e)}")
            return False # Or raise

# Potentially add methods like get_by_email, find_by_criteria, etc.
# Ensure consistency in handling encryption/decryption and entity/model translation.
