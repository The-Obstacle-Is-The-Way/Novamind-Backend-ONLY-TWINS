# NOVAMIND: HIPAA-Compliant Data Transformation Utility - Part 2

## 6. Implementation - Normalization and Standardization

### 6.1 Normalization Implementation

```python
# Continuing from app/utils/data_transformation.py

def normalize_dataframe(
    self, 
    df: pd.DataFrame,
    columns: List[str],
    method: str = 'min_max'
) -> pd.DataFrame:
    """
    Normalize specific columns in a DataFrame.
    
    Args:
        df: DataFrame to normalize
        columns: Columns to normalize
        method: Normalization method ('min_max', 'z_score', 'robust', 'decimal_scaling')
        
    Returns:
        Normalized DataFrame
    """
    result_df = df.copy()
    
    # If no columns specified, use all numeric columns
    if not columns:
        columns = df.select_dtypes(include=['number']).columns.tolist()
    
    for column in columns:
        if column not in df.columns:
            logger.warning(f"Column {column} not found in DataFrame")
            continue
        
        # Skip columns with non-numeric data
        if not pd.api.types.is_numeric_dtype(df[column]):
            logger.warning(f"Column {column} is not numeric, skipping normalization")
            continue
        
        # Handle missing values
        if df[column].isna().any():
            logger.warning(f"Column {column} contains missing values, consider imputation before normalization")
        
        if method == 'min_max':
            # Min-Max scaling to [0, 1] range
            min_val = df[column].min()
            max_val = df[column].max()
            
            if min_val == max_val:
                result_df[column] = 0.5  # If all values are the same
            else:
                result_df[column] = (df[column] - min_val) / (max_val - min_val)
        
        elif method == 'z_score':
            # Z-score standardization (mean=0, std=1)
            mean_val = df[column].mean()
            std_val = df[column].std()
            
            if std_val == 0:
                result_df[column] = 0  # If all values are the same
            else:
                result_df[column] = (df[column] - mean_val) / std_val
        
        elif method == 'robust':
            # Robust scaling using median and IQR
            median_val = df[column].median()
            q1 = df[column].quantile(0.25)
            q3 = df[column].quantile(0.75)
            iqr = q3 - q1
            
            if iqr == 0:
                result_df[column] = 0  # If IQR is zero
            else:
                result_df[column] = (df[column] - median_val) / iqr
        
        elif method == 'decimal_scaling':
            # Decimal scaling
            max_abs_val = df[column].abs().max()
            
            if max_abs_val == 0:
                result_df[column] = 0  # If all values are zero
            else:
                # Calculate the number of digits in the maximum value
                d = len(str(int(max_abs_val)))
                result_df[column] = df[column] / (10 ** d)
        
        else:
            logger.warning(f"Unknown normalization method: {method}")
    
    return result_df

def normalize_value(
    self, 
    value: float,
    min_val: float,
    max_val: float
) -> float:
    """
    Normalize a single value using min-max scaling.
    
    Args:
        value: Value to normalize
        min_val: Minimum value in the range
        max_val: Maximum value in the range
        
    Returns:
        Normalized value
    """
    if min_val == max_val:
        return 0.5
    
    return (value - min_val) / (max_val - min_val)

def standardize_value(
    self, 
    value: float,
    mean: float,
    std: float
) -> float:
    """
    Standardize a single value using z-score.
    
    Args:
        value: Value to standardize
        mean: Mean of the distribution
        std: Standard deviation of the distribution
        
    Returns:
        Standardized value
    """
    if std == 0:
        return 0
    
    return (value - mean) / std
```

### 6.2 Missing Value Imputation Implementation

```python
# Continuing from app/utils/data_transformation.py

def impute_missing_values(
    self, 
    df: pd.DataFrame,
    columns: List[str],
    method: str = 'mean'
) -> pd.DataFrame:
    """
    Impute missing values in specific columns of a DataFrame.
    
    Args:
        df: DataFrame with missing values
        columns: Columns to impute
        method: Imputation method ('mean', 'median', 'mode', 'constant', 'knn', 'time_series')
        
    Returns:
        DataFrame with imputed values
    """
    result_df = df.copy()
    
    # If no columns specified, use all columns with missing values
    if not columns:
        columns = [col for col in df.columns if df[col].isna().any()]
    
    for column in columns:
        if column not in df.columns:
            logger.warning(f"Column {column} not found in DataFrame")
            continue
        
        # Skip columns with no missing values
        if not df[column].isna().any():
            continue
        
        # For numeric columns
        if pd.api.types.is_numeric_dtype(df[column]):
            if method == 'mean':
                result_df[column] = df[column].fillna(df[column].mean())
            
            elif method == 'median':
                result_df[column] = df[column].fillna(df[column].median())
            
            elif method == 'mode':
                result_df[column] = df[column].fillna(df[column].mode()[0])
            
            elif method == 'constant':
                result_df[column] = df[column].fillna(0)
            
            elif method == 'knn':
                # For KNN imputation, we need to consider multiple columns
                # This is a simplified version
                from sklearn.impute import KNNImputer
                
                # Select numeric columns only
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if column in numeric_cols:
                    imputer = KNNImputer(n_neighbors=5)
                    imputed_array = imputer.fit_transform(df[numeric_cols])
                    imputed_df = pd.DataFrame(imputed_array, columns=numeric_cols, index=df.index)
                    result_df[column] = imputed_df[column]
            
            elif method == 'time_series':
                # For time series imputation, we need a time index
                # This is a simplified version using forward and backward fill
                result_df[column] = df[column].interpolate(method='time').bfill().ffill()
            
            else:
                logger.warning(f"Unknown imputation method for numeric data: {method}")
        
        # For categorical/string columns
        else:
            if method == 'mode':
                result_df[column] = df[column].fillna(df[column].mode()[0] if not df[column].mode().empty else "Unknown")
            
            elif method == 'constant':
                result_df[column] = df[column].fillna("Unknown")
            
            elif method == 'knn':
                # KNN imputation for categorical data requires encoding
                # This is a simplified approach
                logger.warning("KNN imputation for categorical data is not fully implemented")
                result_df[column] = df[column].fillna(df[column].mode()[0] if not df[column].mode().empty else "Unknown")
            
            else:
                # Default to mode imputation for categorical data
                result_df[column] = df[column].fillna(df[column].mode()[0] if not df[column].mode().empty else "Unknown")
    
    return result_df

def impute_time_series(
    self,
    series: pd.Series,
    method: str = 'linear'
) -> pd.Series:
    """
    Impute missing values in a time series.
    
    Args:
        series: Time series with missing values
        method: Imputation method ('linear', 'spline', 'polynomial', 'ffill', 'bfill')
        
    Returns:
        Time series with imputed values
    """
    if method == 'linear':
        return series.interpolate(method='linear')
    
    elif method == 'spline':
        return series.interpolate(method='spline', order=3)
    
    elif method == 'polynomial':
        return series.interpolate(method='polynomial', order=2)
    
    elif method == 'ffill':
        return series.ffill()
    
    elif method == 'bfill':
        return series.bfill()
    
    else:
        logger.warning(f"Unknown time series imputation method: {method}")
        return series.interpolate(method='linear')
```

## 7. Usage Examples - Normalization and Imputation

### 7.1 Data Normalization

```python
import pandas as pd
from app.utils.data_transformation import DataTransformationService

# Create a data transformation service
data_service = DataTransformationService()

# Sample patient symptom data
symptom_data = pd.DataFrame([
    {"patient_id": "P001", "anxiety_score": 7, "depression_score": 5, "sleep_quality": 3},
    {"patient_id": "P002", "anxiety_score": 3, "depression_score": 8, "sleep_quality": 2},
    {"patient_id": "P003", "anxiety_score": 5, "depression_score": 4, "sleep_quality": 6},
    {"patient_id": "P004", "anxiety_score": 9, "depression_score": 7, "sleep_quality": 1},
    {"patient_id": "P005", "anxiety_score": 2, "depression_score": 3, "sleep_quality": 7}
])

# Normalize the symptom scores using min-max scaling
normalized_data = data_service.transform_data(
    symptom_data,
    transformations=[
        {
            "type": "normalize",
            "method": "min_max",
            "columns": ["anxiety_score", "depression_score", "sleep_quality"]
        }
    ]
)

print("Original symptom data:")
print(symptom_data)
print("\nNormalized symptom data (min-max):")
print(normalized_data)

# Standardize the symptom scores using z-score
standardized_data = data_service.transform_data(
    symptom_data,
    transformations=[
        {
            "type": "normalize",
            "method": "z_score",
            "columns": ["anxiety_score", "depression_score", "sleep_quality"]
        }
    ]
)

print("\nStandardized symptom data (z-score):")
print(standardized_data)
```

### 7.2 Missing Value Imputation

```python
import pandas as pd
import numpy as np
from app.utils.data_transformation import DataTransformationService

# Create a data transformation service
data_service = DataTransformationService()

# Sample patient data with missing values
patient_data = pd.DataFrame([
    {"patient_id": "P001", "age": 42, "anxiety_score": 7, "depression_score": 5, "medication_adherence": 0.9},
    {"patient_id": "P002", "age": 35, "anxiety_score": np.nan, "depression_score": 8, "medication_adherence": 0.7},
    {"patient_id": "P003", "age": 67, "anxiety_score": 5, "depression_score": np.nan, "medication_adherence": np.nan},
    {"patient_id": "P004", "age": 29, "anxiety_score": 9, "depression_score": 7, "medication_adherence": 0.8},
    {"patient_id": "P005", "age": np.nan, "anxiety_score": 2, "depression_score": 3, "medication_adherence": 0.95}
])

# Impute missing values using mean imputation
imputed_data_mean = data_service.transform_data(
    patient_data,
    transformations=[
        {
            "type": "impute",
            "method": "mean",
            "columns": ["age", "anxiety_score", "depression_score", "medication_adherence"]
        }
    ]
)

print("Original patient data with missing values:")
print(patient_data)
print("\nImputed patient data (mean):")
print(imputed_data_mean)

# Impute missing values using median imputation
imputed_data_median = data_service.transform_data(
    patient_data,
    transformations=[
        {
            "type": "impute",
            "method": "median",
            "columns": ["age", "anxiety_score", "depression_score", "medication_adherence"]
        }
    ]
)

print("\nImputed patient data (median):")
print(imputed_data_median)

# Impute missing values using KNN imputation
imputed_data_knn = data_service.transform_data(
    patient_data,
    transformations=[
        {
            "type": "impute",
            "method": "knn",
            "columns": ["age", "anxiety_score", "depression_score", "medication_adherence"]
        }
    ]
)

print("\nImputed patient data (KNN):")
print(imputed_data_knn)
```

## 8. Implementation - Feature Engineering

### 8.1 Feature Engineering Implementation

```python
# Continuing from app/utils/data_transformation.py

def engineer_features(
    self, 
    df: pd.DataFrame,
    features: List[Dict]
) -> pd.DataFrame:
    """
    Engineer new features from existing columns.
    
    Args:
        df: DataFrame to process
        features: List of feature specifications
        
    Returns:
        DataFrame with engineered features
    """
    result_df = df.copy()
    
    for feature_spec in features:
        feature_type = feature_spec.get('type')
        output_column = feature_spec.get('output_column')
        
        if not output_column:
            logger.warning("No output column specified for feature engineering")
            continue
        
        if feature_type == 'ratio':
            # Create ratio between two columns
            numerator = feature_spec.get('numerator')
            denominator = feature_spec.get('denominator')
            
            if numerator not in df.columns or denominator not in df.columns:
                logger.warning(f"Columns for ratio not found: {numerator}, {denominator}")
                continue
            
            result_df[output_column] = df[numerator] / df[denominator].replace(0, np.nan)
        
        elif feature_type == 'difference':
            # Create difference between two columns
            column1 = feature_spec.get('column1')
            column2 = feature_spec.get('column2')
            
            if column1 not in df.columns or column2 not in df.columns:
                logger.warning(f"Columns for difference not found: {column1}, {column2}")
                continue
            
            result_df[output_column] = df[column1] - df[column2]
        
        elif feature_type == 'polynomial':
            # Create polynomial features
            column = feature_spec.get('column')
            degree = feature_spec.get('degree', 2)
            
            if column not in df.columns:
                logger.warning(f"Column for polynomial not found: {column}")
                continue
            
            result_df[output_column] = df[column] ** degree
        
        elif feature_type == 'interaction':
            # Create interaction term between columns
            columns = feature_spec.get('columns', [])
            
            if not all(col in df.columns for col in columns):
                logger.warning(f"Not all columns for interaction found: {columns}")
                continue
            
            result_df[output_column] = 1
            for col in columns:
                result_df[output_column] *= df[col]
        
        elif feature_type == 'bin':
            # Bin continuous variable into categories
            column = feature_spec.get('column')
            bins = feature_spec.get('bins', 3)
            labels = feature_spec.get('labels')
            
            if column not in df.columns:
                logger.warning(f"Column for binning not found: {column}")
                continue
            
            result_df[output_column] = pd.cut(df[column], bins=bins, labels=labels)
        
        elif feature_type == 'log':
            # Create log transformation
            column = feature_spec.get('column')
            base = feature_spec.get('base', 'natural')
            
            if column not in df.columns:
                logger.warning(f"Column for log transformation not found: {column}")
                continue
            
            # Handle zero or negative values
            min_val = df[column].min()
            if min_val <= 0:
                offset = abs(min_val) + 1
                logger.warning(f"Adding offset {offset} to {column} for log transformation")
                if base == 'natural':
                    result_df[output_column] = np.log(df[column] + offset)
                elif base == 10:
                    result_df[output_column] = np.log10(df[column] + offset)
                else:
                    result_df[output_column] = np.log(df[column] + offset) / np.log(base)
            else:
                if base == 'natural':
                    result_df[output_column] = np.log(df[column])
                elif base == 10:
                    result_df[output_column] = np.log10(df[column])
                else:
                    result_df[output_column] = np.log(df[column]) / np.log(base)
        
        elif feature_type == 'one_hot':
            # One-hot encode categorical variable
            column = feature_spec.get('column')
            
            if column not in df.columns:
                logger.warning(f"Column for one-hot encoding not found: {column}")
                continue
            
            # Create dummy variables
            dummies = pd.get_dummies(df[column], prefix=output_column)
            result_df = pd.concat([result_df, dummies], axis=1)
        
        elif feature_type == 'aggregate':
            # Aggregate multiple columns
            columns = feature_spec.get('columns', [])
            method = feature_spec.get('method', 'sum')
            
            if not all(col in df.columns for col in columns):
                logger.warning(f"Not all columns for aggregation found: {columns}")
                continue
            
            if method == 'sum':
                result_df[output_column] = df[columns].sum(axis=1)
            elif method == 'mean':
                result_df[output_column] = df[columns].mean(axis=1)
            elif method == 'max':
                result_df[output_column] = df[columns].max(axis=1)
            elif method == 'min':
                result_df[output_column] = df[columns].min(axis=1)
            else:
                logger.warning(f"Unknown aggregation method: {method}")
        
        else:
            logger.warning(f"Unknown feature engineering type: {feature_type}")
    
    return result_df
```

## 9. Usage Examples - Feature Engineering

### 9.1 Basic Feature Engineering

```python
import pandas as pd
from app.utils.data_transformation import DataTransformationService

# Create a data transformation service
data_service = DataTransformationService()

# Sample patient symptom and treatment data
patient_data = pd.DataFrame([
    {
        "patient_id": "P001",
        "anxiety_score": 7,
        "depression_score": 5,
        "medication_dose": 50,
        "weight_kg": 75,
        "treatment_weeks": 12,
        "initial_severity": 8,
        "current_severity": 5
    },
    {
        "patient_id": "P002",
        "anxiety_score": 3,
        "depression_score": 8,
        "medication_dose": 75,
        "weight_kg": 82,
        "treatment_weeks": 8,
        "initial_severity": 9,
        "current_severity": 7
    },
    {
        "patient_id": "P003",
        "anxiety_score": 5,
        "depression_score": 4,
        "medication_dose": 100,
        "weight_kg": 68,
        "treatment_weeks": 16,
        "initial_severity": 7,
        "current_severity": 3
    }
])

# Engineer new features
engineered_data = data_service.transform_data(
    patient_data,
    transformations=[
        {
            "type": "feature_engineering",
            "features": [
                {
                    "type": "ratio",
                    "numerator": "medication_dose",
                    "denominator": "weight_kg",
                    "output_column": "dose_per_kg"
                },
                {
                    "type": "difference",
                    "column1": "initial_severity",
                    "column2": "current_severity",
                    "output_column": "improvement"
                },
                {
                    "type": "ratio",
                    "numerator": "improvement",
                    "denominator": "treatment_weeks",
                    "output_column": "improvement_rate"
                },
                {
                    "type": "aggregate",
                    "columns": ["anxiety_score", "depression_score"],
                    "method": "sum",
                    "output_column": "total_symptom_score"
                }
            ]
        }
    ]
)

print("Original patient data:")
print(patient_data)
print("\nEngineered patient data:")
print(engineered_data)
```

### 9.2 Advanced Feature Engineering for ML

```python
import pandas as pd
from app.utils.data_transformation import DataTransformationService

# Create a data transformation service
data_service = DataTransformationService()

# Sample patient data for ML model
ml_data = pd.DataFrame([
    {
        "patient_id": "P001",
        "age": 42,
        "gender": "Male",
        "diagnosis": "Major Depressive Disorder",
        "symptom_score": 7,
        "treatment_duration_weeks": 12,
        "medication_adherence": 0.85,
        "therapy_sessions": 8
    },
    {
        "patient_id": "P002",
        "age": 35,
        "gender": "Female",
        "diagnosis": "Generalized Anxiety Disorder",
        "symptom_score": 5,
        "treatment_duration_weeks": 8,
        "medication_adherence": 0.7,
        "therapy_sessions": 6
    },
    {
        "patient_id": "P003",
        "age": 67,
        "gender": "Male",
        "diagnosis": "Bipolar Disorder",
        "symptom_score": 4,
        "treatment_duration_weeks": 16,
        "medication_adherence": 0.9,
        "therapy_sessions": 12
    },
    {
        "patient_id": "P004",
        "age": 29,
        "gender": "Female",
        "diagnosis": "Major Depressive Disorder",
        "symptom_score": 8,
        "treatment_duration_weeks": 10,
        "medication_adherence": 0.6,
        "therapy_sessions": 5
    }
])

# Apply comprehensive feature engineering for ML
ml_ready_data = data_service.transform_data(
    ml_data,
    transformations=[
        # Anonymize patient ID
        {
            "type": "anonymize",
            "method": "hash",
            "columns": ["patient_id"]
        },
        # Normalize numeric features
        {
            "type": "normalize",
            "method": "min_max",
            "columns": ["age", "symptom_score", "treatment_duration_weeks", "medication_adherence", "therapy_sessions"]
        },
        # One-hot encode categorical features
        {
            "type": "feature_engineering",
            "features": [
                {
                    "type": "one_hot",
                    "column": "gender",
                    "output_column": "gender"
                },
                {
                    "type": "one_hot",
                    "column": "diagnosis",
                    "output_column": "diagnosis"
                }
            ]
        },
        # Create derived features
        {
            "type": "feature_engineering",
            "features": [
                {
                    "type": "bin",
                    "column": "age",
                    "bins": [0, 30, 50, 100],
                    "labels": ["young", "middle", "senior"],
                    "output_column": "age_group"
                },
                {
                    "type": "ratio",
                    "numerator": "therapy_sessions",
                    "denominator": "treatment_duration_weeks",
                    "output_column": "therapy_frequency"
                },
                {
                    "type": "interaction",
                    "columns": ["symptom_score", "medication_adherence"],
                    "output_column": "symptom_adherence_interaction"
                },
                {
                    "type": "polynomial",
                    "column": "symptom_score",
                    "degree": 2,
                    "output_column": "symptom_score_squared"
                }
            ]
        }
    ]
)

print("Original data:")
print(ml_data)
print("\nML-ready data:")
print(ml_ready_data)
```

In the next part, we'll cover time series processing and integration with machine learning pipelines in the Data Transformation Utility.
