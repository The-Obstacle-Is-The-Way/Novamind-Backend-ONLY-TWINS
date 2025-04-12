"""
Digital twin service implementation.

This module provides service layer functionality for working with digital twins,
handling the business logic between domain entities and the infrastructure layer.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from app.domain.entities.biometric_twin_enhanced import (
    BiometricTwin,
    BiometricDataPoint,
    BiometricType,
    BiometricSource,
    BiometricTimeseriesData
)
from app.domain.value_objects.physiological_ranges import PhysiologicalRange


logger = logging.getLogger(__name__)


class DigitalTwinService:
    """
    Service for Digital Twin operations.
    
    This service provides the business logic for creating, querying, and
    analyzing digital twins. It acts as an abstraction between the domain
    entities and the infrastructure layer.
    """
    
    def __init__(self, repository):
        """
        Initialize the digital twin service.
        
        Args:
            repository: Repository for digital twin persistence
        """
        self.repository = repository
    
    async def get_digital_twin(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a patient's digital twin.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Digital twin data or None if not found
        """
        try:
            twin = await self.repository.get_by_patient_id(patient_id)
            if not twin:
                return None
            
            return twin.to_dict()
        except Exception as e:
            logger.error(f"Error retrieving digital twin for patient {patient_id}: {e}")
            return None
    
    async def create_digital_twin(self, patient_id: str) -> Dict[str, Any]:
        """
        Create a new digital twin for a patient.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Created digital twin data
        """
        try:
            twin_id = str(uuid.uuid4())
            now = datetime.now()
            
            twin = BiometricTwin(
                id=twin_id,
                patient_id=patient_id,
                timeseries_data={},
                created_at=now,
                updated_at=now
            )
            
            await self.repository.create(twin)
            return twin.to_dict()
        except Exception as e:
            logger.error(f"Error creating digital twin for patient {patient_id}: {e}")
            raise
    
    async def update_digital_twin(
        self, patient_id: str, twin_data: Dict[str, Any]
    ) -> bool:
        """
        Update a patient's digital twin.
        
        Args:
            patient_id: ID of the patient
            twin_data: Updated digital twin data
            
        Returns:
            True on success, False on failure
        """
        try:
            # Ensure patient_id matches
            if twin_data.get("patient_id") != patient_id:
                logger.error(f"Patient ID mismatch: {patient_id} vs {twin_data.get('patient_id')}")
                return False
            
            # Get existing twin to ensure it exists
            existing_twin = await self.repository.get_by_patient_id(patient_id)
            if not existing_twin:
                logger.error(f"Digital twin not found for patient {patient_id}")
                return False
            
            # Convert data to domain entity
            twin = BiometricTwin.from_dict(twin_data)
            
            # Update in repository
            await self.repository.update(twin)
            return True
        except Exception as e:
            logger.error(f"Error updating digital twin for patient {patient_id}: {e}")
            return False
    
    async def add_biometric_data(
        self,
        patient_id: str,
        biometric_type: str,
        value: Any,
        source: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add biometric data to a patient's digital twin.
        
        Args:
            patient_id: ID of the patient
            biometric_type: Type of biometric data
            value: Measurement value
            source: Source of the data
            timestamp: Measurement timestamp (default: now)
            metadata: Additional information
            
        Returns:
            True on success, False on failure
        """
        try:
            # Convert string inputs to appropriate enums
            try:
                biometric_type_enum = BiometricType(biometric_type)
            except ValueError:
                logger.warning(f"Unknown biometric type: {biometric_type}")
                biometric_type_enum = biometric_type
            
            try:
                source_enum = BiometricSource(source)
            except ValueError:
                logger.warning(f"Unknown biometric source: {source}")
                source_enum = source
            
            # Set default timestamp if not provided
            if timestamp is None:
                timestamp = datetime.now()
            elif isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            # Create data point
            data_point = BiometricDataPoint(
                timestamp=timestamp,
                value=value,
                source=source_enum,
                metadata=metadata or {}
            )
            
            # Get existing twin
            twin = await self.repository.get_by_patient_id(patient_id)
            if not twin:
                # Create new twin if not exists
                twin_id = str(uuid.uuid4())
                now = datetime.now()
                
                twin = BiometricTwin(
                    id=twin_id,
                    patient_id=patient_id,
                    timeseries_data={},
                    created_at=now,
                    updated_at=now
                )
            
            # Add data point
            unit = self._get_unit_for_biometric_type(biometric_type)
            twin.add_data_point(
                biometric_type=biometric_type_enum,
                data_point=data_point,
                unit=unit
            )
            
            # Save to repository
            if await self.repository.get_by_patient_id(patient_id):
                await self.repository.update(twin)
            else:
                await self.repository.create(twin)
            
            return True
        except Exception as e:
            logger.error(f"Error adding biometric data for patient {patient_id}: {e}")
            return False
    
    async def get_biometric_history(
        self,
        patient_id: str,
        biometric_type: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get history of biometric measurements.
        
        Args:
            patient_id: ID of the patient
            biometric_type: Type of biometric data
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of biometric data points or None if not found
        """
        try:
            # Convert string inputs to appropriate enums
            try:
                biometric_type_enum = BiometricType(biometric_type)
            except ValueError:
                logger.warning(f"Unknown biometric type: {biometric_type}")
                biometric_type_enum = biometric_type
            
            # Get patient's digital twin
            twin = await self.repository.get_by_patient_id(patient_id)
            if not twin:
                logger.error(f"Digital twin not found for patient {patient_id}")
                return None
            
            # Get timeseries for the requested biometric type
            timeseries = twin.get_biometric_data(biometric_type_enum)
            if not timeseries:
                logger.info(f"No {biometric_type} data found for patient {patient_id}")
                return []
            
            # Filter by time range if provided
            if start_time or end_time:
                start_datetime = datetime.fromisoformat(start_time) if start_time else datetime.min
                end_datetime = datetime.fromisoformat(end_time) if end_time else datetime.max
                
                data_points = timeseries.get_values_in_range(start_datetime, end_datetime)
            else:
                data_points = timeseries.data_points
            
            # Convert to dictionaries
            return [dp.to_dict() for dp in data_points]
        except Exception as e:
            logger.error(f"Error retrieving biometric history for patient {patient_id}: {e}")
            return None
    
    async def get_latest_biometrics(self, patient_id: str) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Get latest values for all biometric types.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Dictionary of biometric types to latest values
        """
        try:
            # Get patient's digital twin
            twin = await self.repository.get_by_patient_id(patient_id)
            if not twin:
                logger.error(f"Digital twin not found for patient {patient_id}")
                return None
            
            # Get latest values
            latest_values = twin.get_latest_values()
            
            # Convert to dictionaries
            result = {}
            for biometric_type, data_point in latest_values.items():
                type_key = biometric_type.value if isinstance(biometric_type, BiometricType) else str(biometric_type)
                result[type_key] = data_point.to_dict()
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving latest biometrics for patient {patient_id}: {e}")
            return None
    
    async def detect_abnormal_values(self, patient_id: str) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Detect abnormal biometric values.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Dictionary of biometric types to abnormal values
        """
        try:
            # Get patient's digital twin
            twin = await self.repository.get_by_patient_id(patient_id)
            if not twin:
                logger.error(f"Digital twin not found for patient {patient_id}")
                return None
            
            # Get abnormal values
            abnormal_values = twin.detect_abnormal_values()
            
            # Convert to dictionaries
            result = {}
            for biometric_type, data_points in abnormal_values.items():
                type_key = biometric_type.value if isinstance(biometric_type, BiometricType) else str(biometric_type)
                result[type_key] = [dp.to_dict() for dp in data_points]
            
            return result
        except Exception as e:
            logger.error(f"Error detecting abnormal values for patient {patient_id}: {e}")
            return None
    
    async def detect_critical_values(self, patient_id: str) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Detect critical biometric values.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Dictionary of biometric types to critical values
        """
        try:
            # Get patient's digital twin
            twin = await self.repository.get_by_patient_id(patient_id)
            if not twin:
                logger.error(f"Digital twin not found for patient {patient_id}")
                return None
            
            # Get critical values
            critical_values = twin.detect_critical_values()
            
            # Convert to dictionaries
            result = {}
            for biometric_type, data_points in critical_values.items():
                type_key = biometric_type.value if isinstance(biometric_type, BiometricType) else str(biometric_type)
                result[type_key] = [dp.to_dict() for dp in data_points]
            
            return result
        except Exception as e:
            logger.error(f"Error detecting critical values for patient {patient_id}: {e}")
            return None
    
    def _get_unit_for_biometric_type(self, biometric_type: Union[BiometricType, str]) -> str:
        """
        Get the unit for a biometric type.
        
        Args:
            biometric_type: Type of biometric data
            
        Returns:
            Unit string
        """
        if isinstance(biometric_type, BiometricType):
            type_str = biometric_type.value
        else:
            type_str = biometric_type
        
        units = {
            "heart_rate": "bpm",
            "blood_pressure": "mmHg",
            "temperature": "°C",
            "respiratory_rate": "breaths/min",
            "blood_glucose": "mg/dL",
            "oxygen_saturation": "%",
            "sleep": "hours",
            "activity": "steps",
            "weight": "kg",
            "stress": "score",
            "hrv": "ms",
            "eeg": "μV",
            "emg": "μV",
            "cortisol": "μg/dL"
        }
        
        return units.get(type_str, "units")
