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

from app.domain.entities.patient import Patient
from app.infrastructure.persistence.sqlalchemy.models.patient import PatientModel


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
    
    async def get_by_id(self, id: str) -> Optional[Patient]:
        """
        Get a patient by ID.
        
        Args:
            id: Patient unique identifier
            
        Returns:
            Optional[Patient]: Patient entity or None if not found
        """
        try:
            query = select(PatientModel).where(PatientModel.c.id == id)
            result = await self.session.execute(query)
            patient_data = result.fetchone()
            
            if not patient_data:
                return None
                
            # Convert row to dict
            patient_dict = {column.name: getattr(patient_data, column.name) 
                           for column in PatientModel.columns}
            
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
            return Patient(**patient_dict)
            
        except Exception as e:
            self.logger.error(f"Error retrieving patient with ID {id}: {str(e)}")
            return None
    
    async def get_all(self) -> List[Patient]:
        """
        Get all patients.
        
        Returns:
            List[Patient]: List of all patient entities
        """
        try:
            query = select(PatientModel)
            result = await self.session.execute(query)
            patients_data = result.fetchall()
            
            patients = []
            for patient_data in patients_data:
                # Convert row to dict
                patient_dict = {column.name: getattr(patient_data, column.name) 
                               for column in PatientModel.columns}
                
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
                patients.append(Patient(**patient_dict))
                
            return patients
            
        except Exception as e:
            self.logger.error(f"Error retrieving all patients: {str(e)}")
            return []
    
    async def create(self, patient_data: Dict[str, Any]) -> Patient:
        """
        Create a new patient.
        
        Args:
            patient_data: Dictionary containing patient attributes
            
        Returns:
            Patient: Created patient entity
        """
        try:
            # Prepare JSON fields
            for json_field in ["medical_history", "medications", "allergies", "treatment_notes"]:
                if json_field in patient_data and not isinstance(patient_data[json_field], str):
                    patient_data[json_field] = json.dumps(patient_data[json_field])
            
            # Set timestamps if not provided
            now = datetime.now().isoformat()
            if "created_at" not in patient_data:
                patient_data["created_at"] = now
            if "updated_at" not in patient_data:
                patient_data["updated_at"] = now
            
            # Insert into database
            stmt = insert(PatientModel).values(**patient_data).returning(*PatientModel.columns)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            # Get the inserted data
            patient_data = result.fetchone()
            
            # Convert row to dict
            patient_dict = {column.name: getattr(patient_data, column.name) 
                           for column in PatientModel.columns}
            
            # Parse JSON fields back
            for json_field in ["medical_history", "medications", "allergies", "treatment_notes"]:
                if patient_dict.get(json_field) and isinstance(patient_dict[json_field], str):
                    try:
                        patient_dict[json_field] = json.loads(patient_dict[json_field])
                    except json.JSONDecodeError:
                        patient_dict[json_field] = []
                elif patient_dict.get(json_field) is None:
                    patient_dict[json_field] = []
            
            # Create and return domain entity
            return Patient(**patient_dict)
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error creating patient: {str(e)}")
            raise
    
    async def update(self, id: str, patient_data: Dict[str, Any]) -> Optional[Patient]:
        """
        Update an existing patient.
        
        Args:
            id: Patient unique identifier
            patient_data: Dictionary containing updated patient attributes
            
        Returns:
            Optional[Patient]: Updated patient entity or None if not found
        """
        try:
            # Check if patient exists
            patient = await self.get_by_id(id)
            if not patient:
                return None
            
            # Prepare JSON fields
            for json_field in ["medical_history", "medications", "allergies", "treatment_notes"]:
                if json_field in patient_data and not isinstance(patient_data[json_field], str):
                    patient_data[json_field] = json.dumps(patient_data[json_field])
            
            # Set updated timestamp
            patient_data["updated_at"] = datetime.now().isoformat()
            
            # Update in database
            stmt = update(PatientModel).where(PatientModel.c.id == id).values(**patient_data).returning(*PatientModel.columns)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            # Get the updated data
            updated_data = result.fetchone()
            
            if not updated_data:
                return None
                
            # Convert row to dict
            patient_dict = {column.name: getattr(updated_data, column.name) 
                           for column in PatientModel.columns}
            
            # Parse JSON fields back
            for json_field in ["medical_history", "medications", "allergies", "treatment_notes"]:
                if patient_dict.get(json_field) and isinstance(patient_dict[json_field], str):
                    try:
                        patient_dict[json_field] = json.loads(patient_dict[json_field])
                    except json.JSONDecodeError:
                        patient_dict[json_field] = []
                elif patient_dict.get(json_field) is None:
                    patient_dict[json_field] = []
            
            # Create and return domain entity
            return Patient(**patient_dict)
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating patient with ID {id}: {str(e)}")
            raise
    
    async def delete(self, id: str) -> bool:
        """
        Delete a patient.
        
        Args:
            id: Patient unique identifier
            
        Returns:
            bool: True if patient was deleted, False otherwise
        """
        try:
            # Check if patient exists
            patient = await self.get_by_id(id)
            if not patient:
                return False
            
            # Delete from database
            stmt = delete(PatientModel).where(PatientModel.c.id == id)
            await self.session.execute(stmt)
            await self.session.commit()
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error deleting patient with ID {id}: {str(e)}")
            return False
