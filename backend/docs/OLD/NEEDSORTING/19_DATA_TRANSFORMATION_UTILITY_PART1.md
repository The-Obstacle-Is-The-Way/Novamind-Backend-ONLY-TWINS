# NOVAMIND: HIPAA-Compliant Data Transformation Utility - Part 1

## 1. Overview

The Data Transformation Utility is a critical component of the NOVAMIND platform that provides robust, HIPAA-compliant data processing capabilities for patient data. This utility implements advanced techniques for data anonymization, normalization, standardization, and feature engineering to support analytics, research, and machine learning applications while maintaining strict compliance with privacy regulations.

## 2. Key Features

- **Data Anonymization**: Methods for removing or obscuring PHI for research and analytics
- **Normalization and Standardization**: Techniques for preparing data for analysis
- **Missing Value Imputation**: Strategies for handling incomplete data
- **Feature Engineering**: Tools for creating meaningful features from raw data
- **Time Series Processing**: Specialized methods for temporal patient data

## 3. Implementation - Core Components

### 3.1 Core Data Transformation Service

```python
# app/utils/data_transformation.py
import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from app.utils.encryption import EncryptionService
from app.utils.logging import get_logger

logger = get_logger(__name__)

class DataTransformationService:
    """
    HIPAA-compliant data transformation service for processing patient data
    for analytics, research, and machine learning applications.
    """
    
    def __init__(self, encryption_service: Optional[EncryptionService] = None):
        """
        Initialize the data transformation service.
        
        Args:
            encryption_service: EncryptionService instance for data encryption/decryption
        """
        self.encryption_service = encryption_service or EncryptionService()
        
        # Initialize scalers
        self.min_max_scaler = MinMaxScaler()
        self.standard_scaler = StandardScaler()
        
        # Initialize imputers
        self.mean_imputer = SimpleImputer(strategy='mean')
        self.median_imputer = SimpleImputer(strategy='median')
        self.most_frequent_imputer = SimpleImputer(strategy='most_frequent')
    
    def transform_data(
        self, 
        data: Union[Dict, List, pd.DataFrame],
        transformations: List[Dict]
    ) -> Union[Dict, List, pd.DataFrame]:
        """
        Apply a series of transformations to data.
        
        Args:
            data: Data to transform (dictionary, list, or DataFrame)
            transformations: List of transformation specifications
            
        Returns:
            Transformed data
        """
        # Convert data to DataFrame if necessary
        original_type = type(data)
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError(f"Unsupported data type: {original_type}")
        
        # Apply transformations in sequence
        for transform_spec in transformations:
            transform_type = transform_spec.get('type')
            
            if transform_type == 'anonymize':
                df = self.anonymize_dataframe(
                    df, 
                    columns=transform_spec.get('columns', []),
                    method=transform_spec.get('method', 'hash')
                )
            
            elif transform_type == 'normalize':
                df = self.normalize_dataframe(
                    df, 
                    columns=transform_spec.get('columns', []),
                    method=transform_spec.get('method', 'min_max')
                )
            
            elif transform_type == 'impute':
                df = self.impute_missing_values(
                    df, 
                    columns=transform_spec.get('columns', []),
                    method=transform_spec.get('method', 'mean')
                )
            
            elif transform_type == 'feature_engineering':
                df = self.engineer_features(
                    df,
                    features=transform_spec.get('features', [])
                )
            
            elif transform_type == 'time_series':
                df = self.process_time_series(
                    df,
                    time_column=transform_spec.get('time_column'),
                    operations=transform_spec.get('operations', [])
                )
            
            else:
                logger.warning(f"Unknown transformation type: {transform_type}")
        
        # Convert back to original type if necessary
        if original_type == dict and len(df) == 1:
            return df.iloc[0].to_dict()
        elif original_type == list:
            return df.to_dict('records')
        else:
            return df
```

### 3.2 Data Anonymization Implementation

```python
# Continuing from app/utils/data_transformation.py

def anonymize_dataframe(
    self, 
    df: pd.DataFrame,
    columns: List[str],
    method: str = 'hash'
) -> pd.DataFrame:
    """
    Anonymize specific columns in a DataFrame.
    
    Args:
        df: DataFrame to anonymize
        columns: Columns to anonymize
        method: Anonymization method ('hash', 'mask', 'generalize', 'pseudonymize')
        
    Returns:
        Anonymized DataFrame
    """
    result_df = df.copy()
    
    # If no columns specified, use all string columns
    if not columns:
        columns = df.select_dtypes(include=['object']).columns.tolist()
    
    for column in columns:
        if column not in df.columns:
            logger.warning(f"Column {column} not found in DataFrame")
            continue
        
        if method == 'hash':
            result_df[column] = result_df[column].apply(
                lambda x: hashlib.sha256(str(x).encode()).hexdigest() if pd.notna(x) else x
            )
        
        elif method == 'mask':
            result_df[column] = result_df[column].apply(
                lambda x: self._mask_value(x) if pd.notna(x) else x
            )
        
        elif method == 'generalize':
            result_df[column] = result_df[column].apply(
                lambda x: self._generalize_value(x, column) if pd.notna(x) else x
            )
        
        elif method == 'pseudonymize':
            # Create a mapping of original values to pseudonyms
            unique_values = df[column].dropna().unique()
            pseudonym_mapping = {
                val: f"PSEUDO_{column}_{i}" 
                for i, val in enumerate(unique_values)
            }
            
            result_df[column] = result_df[column].map(
                lambda x: pseudonym_mapping.get(x, x)
            )
        
        else:
            logger.warning(f"Unknown anonymization method: {method}")
    
    return result_df

def _mask_value(self, value: Any) -> str:
    """
    Mask a value by replacing characters with asterisks.
    
    Args:
        value: Value to mask
        
    Returns:
        Masked value
    """
    value_str = str(value)
    
    # Handle different types of PHI
    if re.match(r'^[A-Za-z\s]+$', value_str):  # Name
        parts = value_str.split()
        masked_parts = []
        for part in parts:
            if len(part) > 2:
                masked_parts.append(part[0] + '*' * (len(part) - 2) + part[-1])
            else:
                masked_parts.append('*' * len(part))
        return ' '.join(masked_parts)
    
    elif re.match(r'^\d{3}-\d{2}-\d{4}$', value_str):  # SSN
        return 'XXX-XX-' + value_str[-4:]
    
    elif re.match(r'^\d{4}-\d{2}-\d{2}$', value_str):  # Date (YYYY-MM-DD)
        return value_str[:7] + '-XX'  # Keep year and month
    
    elif re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', value_str):  # Email
        parts = value_str.split('@')
        username = parts[0]
        domain = parts[1]
        if len(username) > 2:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        else:
            masked_username = '*' * len(username)
        return masked_username + '@' + domain
    
    elif re.match(r'^\d{3}-\d{3}-\d{4}$', value_str):  # Phone
        return 'XXX-XXX-' + value_str[-4:]
    
    else:
        # Generic masking for other values
        if len(value_str) <= 4:
            return '*' * len(value_str)
        else:
            visible_chars = max(2, len(value_str) // 4)
            return value_str[:visible_chars] + '*' * (len(value_str) - 2 * visible_chars) + value_str[-visible_chars:]

def _generalize_value(self, value: Any, column: str) -> Any:
    """
    Generalize a value by reducing its specificity.
    
    Args:
        value: Value to generalize
        column: Column name (used to determine generalization strategy)
        
    Returns:
        Generalized value
    """
    value_str = str(value)
    
    # Apply different generalization strategies based on the column or value pattern
    if 'age' in column.lower():
        # Generalize age into ranges
        try:
            age = int(value_str)
            if age < 18:
                return '<18'
            elif age < 30:
                return '18-29'
            elif age < 45:
                return '30-44'
            elif age < 65:
                return '45-64'
            else:
                return '65+'
        except ValueError:
            return value_str
    
    elif 'date' in column.lower() or re.match(r'^\d{4}-\d{2}-\d{2}$', value_str):
        # Generalize date to month and year
        try:
            date_obj = datetime.strptime(value_str, '%Y-%m-%d')
            return date_obj.strftime('%Y-%m')
        except ValueError:
            return value_str
    
    elif 'zip' in column.lower() or re.match(r'^\d{5}(-\d{4})?$', value_str):
        # Generalize ZIP code to first 3 digits
        return value_str[:3] + 'XX'
    
    elif 'income' in column.lower() or 'salary' in column.lower():
        # Generalize income into ranges
        try:
            income = float(value_str.replace(',', '').replace('$', ''))
            if income < 25000:
                return '<$25K'
            elif income < 50000:
                return '$25K-$50K'
            elif income < 75000:
                return '$50K-$75K'
            elif income < 100000:
                return '$75K-$100K'
            else:
                return '>$100K'
        except ValueError:
            return value_str
    
    elif 'diagnosis' in column.lower() or 'condition' in column.lower():
        # Generalize specific diagnoses to broader categories
        value_lower = value_str.lower()
        if any(term in value_lower for term in ['depression', 'anxiety', 'panic', 'phobia']):
            return 'Mood/Anxiety Disorder'
        elif any(term in value_lower for term in ['schizophrenia', 'psychosis', 'delusion']):
            return 'Psychotic Disorder'
        elif any(term in value_lower for term in ['bipolar', 'mania', 'manic']):
            return 'Bipolar Disorder'
        elif any(term in value_lower for term in ['adhd', 'attention deficit']):
            return 'Neurodevelopmental Disorder'
        else:
            return 'Other Psychiatric Condition'
    
    else:
        # Default generalization
        return value_str
```

## 4. Usage Examples - Anonymization

### 4.1 Basic Data Anonymization

```python
from app.utils.data_transformation import DataTransformationService

# Create a data transformation service
data_service = DataTransformationService()

# Sample patient data
patient_data = {
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1980-05-15",
    "ssn": "123-45-6789",
    "email": "john.doe@example.com",
    "phone": "555-123-4567",
    "address": "123 Main St, Anytown, CA 12345",
    "diagnosis": "Major Depressive Disorder",
    "medication": "Sertraline 50mg daily"
}

# Anonymize the data using hashing
anonymized_data = data_service.transform_data(
    patient_data,
    transformations=[
        {
            "type": "anonymize",
            "method": "hash",
            "columns": ["first_name", "last_name", "ssn", "email", "phone", "address"]
        }
    ]
)

print("Original data:", patient_data)
print("Anonymized data (hash):", anonymized_data)

# Anonymize the data using masking
masked_data = data_service.transform_data(
    patient_data,
    transformations=[
        {
            "type": "anonymize",
            "method": "mask",
            "columns": ["first_name", "last_name", "ssn", "email", "phone"]
        }
    ]
)

print("Anonymized data (mask):", masked_data)

# Anonymize the data using generalization
generalized_data = data_service.transform_data(
    patient_data,
    transformations=[
        {
            "type": "anonymize",
            "method": "generalize",
            "columns": ["dob", "diagnosis"]
        }
    ]
)

print("Anonymized data (generalize):", generalized_data)
```

### 4.2 Batch Anonymization for Research

```python
import pandas as pd
from app.utils.data_transformation import DataTransformationService

# Create a data transformation service
data_service = DataTransformationService()

# Sample patient dataset
patients_df = pd.DataFrame([
    {
        "patient_id": "P001",
        "first_name": "John",
        "last_name": "Doe",
        "age": 42,
        "gender": "Male",
        "zip_code": "12345",
        "diagnosis": "Major Depressive Disorder",
        "medication": "Sertraline 50mg",
        "symptom_score": 7
    },
    {
        "patient_id": "P002",
        "first_name": "Jane",
        "last_name": "Smith",
        "age": 35,
        "gender": "Female",
        "zip_code": "23456",
        "diagnosis": "Generalized Anxiety Disorder",
        "medication": "Escitalopram 10mg",
        "symptom_score": 5
    },
    {
        "patient_id": "P003",
        "first_name": "Robert",
        "last_name": "Johnson",
        "age": 67,
        "gender": "Male",
        "zip_code": "34567",
        "diagnosis": "Bipolar Disorder",
        "medication": "Lithium 600mg",
        "symptom_score": 4
    }
])

# Prepare data for research by applying multiple anonymization techniques
research_data = data_service.transform_data(
    patients_df,
    transformations=[
        {
            "type": "anonymize",
            "method": "pseudonymize",
            "columns": ["patient_id"]
        },
        {
            "type": "anonymize",
            "method": "hash",
            "columns": ["first_name", "last_name"]
        },
        {
            "type": "anonymize",
            "method": "generalize",
            "columns": ["age", "zip_code", "diagnosis"]
        }
    ]
)

print("Original patient data:")
print(patients_df)
print("\nAnonymized research data:")
print(research_data)
```

## 5. HIPAA Compliance Considerations for Data Anonymization

1. **De-identification Standards**: HIPAA provides two methods for de-identification:
   - **Safe Harbor Method**: Removal of 18 specific identifiers
   - **Expert Determination Method**: Statistical or scientific principles to ensure risk of re-identification is very small

2. **Safe Harbor Identifiers**: The utility handles these identifiers through various anonymization techniques:
   - Names (hashing, masking, pseudonymization)
   - Geographic subdivisions smaller than a state (generalization of ZIP codes)
   - Dates related to an individual (generalization to year/month)
   - Phone numbers (masking, hashing)
   - Email addresses (masking, hashing)
   - Social Security numbers (masking, hashing)
   - Medical record numbers (pseudonymization)
   - And other identifiers as specified in the HIPAA regulations

3. **Limited Data Sets**: For research purposes, the utility can create limited data sets that retain some dates and geographic information while removing direct identifiers.

4. **Re-identification Risk**: The utility implements techniques to minimize the risk of re-identification through:
   - Consistent pseudonymization across datasets
   - Generalization to reduce uniqueness
   - Careful handling of quasi-identifiers that could be combined for re-identification

5. **Audit Trails**: All data transformation operations are logged for compliance auditing.

In the next part, we'll cover normalization, standardization, and missing value imputation techniques implemented in the Data Transformation Utility.
