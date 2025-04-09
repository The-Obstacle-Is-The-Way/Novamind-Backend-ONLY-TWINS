# NOVAMIND: HIPAA-Compliant Data Transformation Utility - Part 3

## 10. Implementation - Time Series Processing

### 10.1 Time Series Processing Implementation

```python
# Continuing from app/utils/data_transformation.py

def process_time_series(
    self, 
    df: pd.DataFrame,
    time_column: str,
    operations: List[Dict]
) -> pd.DataFrame:
    """
    Process time series data.
    
    Args:
        df: DataFrame with time series data
        time_column: Column containing timestamps
        operations: List of time series operations to perform
        
    Returns:
        Processed DataFrame
    """
    result_df = df.copy()
    
    # Ensure time column is in datetime format
    if time_column not in df.columns:
        logger.warning(f"Time column {time_column} not found in DataFrame")
        return result_df
    
    # Convert time column to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        try:
            result_df[time_column] = pd.to_datetime(df[time_column])
        except Exception as e:
            logger.error(f"Failed to convert {time_column} to datetime: {str(e)}")
            return result_df
    
    # Sort by time column
    result_df = result_df.sort_values(by=time_column)
    
    # Process each operation
    for operation in operations:
        op_type = operation.get('type')
        
        if op_type == 'resample':
            # Resample time series to different frequency
            frequency = operation.get('frequency')
            method = operation.get('method', 'mean')
            
            # Set time column as index
            temp_df = result_df.set_index(time_column)
            
            # Resample
            if method == 'mean':
                resampled = temp_df.resample(frequency).mean()
            elif method == 'sum':
                resampled = temp_df.resample(frequency).sum()
            elif method == 'max':
                resampled = temp_df.resample(frequency).max()
            elif method == 'min':
                resampled = temp_df.resample(frequency).min()
            elif method == 'count':
                resampled = temp_df.resample(frequency).count()
            elif method == 'first':
                resampled = temp_df.resample(frequency).first()
            elif method == 'last':
                resampled = temp_df.resample(frequency).last()
            else:
                logger.warning(f"Unknown resampling method: {method}")
                continue
            
            # Reset index to get time column back
            resampled = resampled.reset_index()
            
            # Replace result_df with resampled data
            result_df = resampled
        
        elif op_type == 'rolling':
            # Calculate rolling statistics
            window = operation.get('window')
            method = operation.get('method', 'mean')
            columns = operation.get('columns', [])
            output_suffix = operation.get('output_suffix', f'_{method}_{window}')
            
            # If no columns specified, use all numeric columns
            if not columns:
                columns = df.select_dtypes(include=['number']).columns.tolist()
                # Remove time column if it's in the list
                if time_column in columns:
                    columns.remove(time_column)
            
            # Calculate rolling statistics for each column
            for column in columns:
                if column not in df.columns:
                    logger.warning(f"Column {column} not found in DataFrame")
                    continue
                
                # Skip non-numeric columns
                if not pd.api.types.is_numeric_dtype(df[column]):
                    logger.warning(f"Column {column} is not numeric, skipping rolling operation")
                    continue
                
                # Calculate rolling statistic
                if method == 'mean':
                    result_df[f"{column}{output_suffix}"] = df[column].rolling(window=window).mean()
                elif method == 'sum':
                    result_df[f"{column}{output_suffix}"] = df[column].rolling(window=window).sum()
                elif method == 'std':
                    result_df[f"{column}{output_suffix}"] = df[column].rolling(window=window).std()
                elif method == 'var':
                    result_df[f"{column}{output_suffix}"] = df[column].rolling(window=window).var()
                elif method == 'min':
                    result_df[f"{column}{output_suffix}"] = df[column].rolling(window=window).min()
                elif method == 'max':
                    result_df[f"{column}{output_suffix}"] = df[column].rolling(window=window).max()
                else:
                    logger.warning(f"Unknown rolling method: {method}")
        
        elif op_type == 'lag':
            # Create lag features
            lag_periods = operation.get('periods', [1])
            columns = operation.get('columns', [])
            
            # If no columns specified, use all numeric columns
            if not columns:
                columns = df.select_dtypes(include=['number']).columns.tolist()
                # Remove time column if it's in the list
                if time_column in columns:
                    columns.remove(time_column)
            
            # Create lag features for each column and period
            for column in columns:
                if column not in df.columns:
                    logger.warning(f"Column {column} not found in DataFrame")
                    continue
                
                for period in lag_periods:
                    result_df[f"{column}_lag_{period}"] = df[column].shift(period)
        
        elif op_type == 'diff':
            # Calculate differences between consecutive observations
            periods = operation.get('periods', 1)
            columns = operation.get('columns', [])
            
            # If no columns specified, use all numeric columns
            if not columns:
                columns = df.select_dtypes(include=['number']).columns.tolist()
                # Remove time column if it's in the list
                if time_column in columns:
                    columns.remove(time_column)
            
            # Calculate differences for each column
            for column in columns:
                if column not in df.columns:
                    logger.warning(f"Column {column} not found in DataFrame")
                    continue
                
                result_df[f"{column}_diff_{periods}"] = df[column].diff(periods)
        
        elif op_type == 'pct_change':
            # Calculate percentage change
            periods = operation.get('periods', 1)
            columns = operation.get('columns', [])
            
            # If no columns specified, use all numeric columns
            if not columns:
                columns = df.select_dtypes(include=['number']).columns.tolist()
                # Remove time column if it's in the list
                if time_column in columns:
                    columns.remove(time_column)
            
            # Calculate percentage change for each column
            for column in columns:
                if column not in df.columns:
                    logger.warning(f"Column {column} not found in DataFrame")
                    continue
                
                result_df[f"{column}_pct_change_{periods}"] = df[column].pct_change(periods)
        
        elif op_type == 'ewm':
            # Exponentially weighted moving average
            alpha = operation.get('alpha', 0.3)
            columns = operation.get('columns', [])
            
            # If no columns specified, use all numeric columns
            if not columns:
                columns = df.select_dtypes(include=['number']).columns.tolist()
                # Remove time column if it's in the list
                if time_column in columns:
                    columns.remove(time_column)
            
            # Calculate EWM for each column
            for column in columns:
                if column not in df.columns:
                    logger.warning(f"Column {column} not found in DataFrame")
                    continue
                
                result_df[f"{column}_ewm_{alpha}"] = df[column].ewm(alpha=alpha).mean()
        
        else:
            logger.warning(f"Unknown time series operation type: {op_type}")
    
    return result_df
```

## 11. Usage Examples - Time Series Processing

### 11.1 Basic Time Series Processing

```python
import pandas as pd
from datetime import datetime, timedelta
from app.utils.data_transformation import DataTransformationService

# Create a data transformation service
data_service = DataTransformationService()

# Create sample time series data (daily mood scores for a patient)
dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(30)]
mood_data = pd.DataFrame({
    "date": dates,
    "patient_id": "P001",
    "mood_score": [7, 6, 6, 5, 4, 3, 4, 5, 6, 7, 7, 6, 5, 4, 3, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 4, 5, 6],
    "anxiety_score": [3, 3, 4, 4, 5, 6, 5, 4, 3, 2, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6, 5, 4, 3],
    "sleep_hours": [7, 7, 6, 6, 5, 5, 6, 7, 8, 8, 7, 7, 6, 5, 5, 4, 5, 6, 7, 8, 8, 7, 7, 6, 6, 5, 5, 6, 7, 8]
})

# Process the time series data
processed_data = data_service.transform_data(
    mood_data,
    transformations=[
        {
            "type": "time_series",
            "time_column": "date",
            "operations": [
                {
                    "type": "rolling",
                    "window": 7,
                    "method": "mean",
                    "columns": ["mood_score", "anxiety_score", "sleep_hours"],
                    "output_suffix": "_7day_avg"
                },
                {
                    "type": "lag",
                    "periods": [1, 7],
                    "columns": ["mood_score", "anxiety_score"]
                },
                {
                    "type": "diff",
                    "periods": 1,
                    "columns": ["mood_score", "anxiety_score", "sleep_hours"]
                }
            ]
        }
    ]
)

print("Original time series data:")
print(mood_data.head())
print("\nProcessed time series data:")
print(processed_data.head())

# Resample the data to weekly frequency
weekly_data = data_service.transform_data(
    mood_data,
    transformations=[
        {
            "type": "time_series",
            "time_column": "date",
            "operations": [
                {
                    "type": "resample",
                    "frequency": "W",  # Weekly
                    "method": "mean"
                }
            ]
        }
    ]
)

print("\nWeekly resampled data:")
print(weekly_data)
```

### 11.2 Advanced Time Series Features for Predictive Models

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.utils.data_transformation import DataTransformationService

# Create a data transformation service
data_service = DataTransformationService()

# Create sample longitudinal patient data
start_date = datetime(2023, 1, 1)
dates = []
patient_ids = []
symptom_scores = []
medication_doses = []
sleep_hours = []
activity_levels = []

# Generate data for 3 patients over 60 days
for patient_id in ["P001", "P002", "P003"]:
    for i in range(60):
        dates.append(start_date + timedelta(days=i))
        patient_ids.append(patient_id)
        
        # Create some patterns in the data
        base_symptom = 5 + 2 * np.sin(i / 10)  # Cyclical pattern
        if patient_id == "P001":
            symptom_scores.append(base_symptom + np.random.normal(0, 0.5))
            medication_doses.append(50 + (i // 10) * 5)  # Increasing dose
            sleep_hours.append(7 + np.random.normal(0, 0.5))
            activity_levels.append(3 + 2 * np.sin(i / 15) + np.random.normal(0, 0.3))
        elif patient_id == "P002":
            symptom_scores.append(base_symptom + 1 + np.random.normal(0, 0.7))
            medication_doses.append(75 - (i // 20) * 5)  # Decreasing dose
            sleep_hours.append(6 + np.random.normal(0, 0.7))
            activity_levels.append(4 + np.random.normal(0, 0.5))
        else:
            symptom_scores.append(base_symptom - 1 + np.random.normal(0, 0.6))
            medication_doses.append(60)  # Constant dose
            sleep_hours.append(8 + np.random.normal(0, 0.4))
            activity_levels.append(5 - 0.02 * i + np.random.normal(0, 0.4))  # Decreasing activity

# Create DataFrame
patient_ts_data = pd.DataFrame({
    "date": dates,
    "patient_id": patient_ids,
    "symptom_score": symptom_scores,
    "medication_dose": medication_doses,
    "sleep_hours": sleep_hours,
    "activity_level": activity_levels
})

# Prepare data for predictive modeling
ml_ready_ts_data = data_service.transform_data(
    patient_ts_data,
    transformations=[
        # Normalize the data
        {
            "type": "normalize",
            "method": "min_max",
            "columns": ["symptom_score", "medication_dose", "sleep_hours", "activity_level"]
        },
        # Generate time series features
        {
            "type": "time_series",
            "time_column": "date",
            "operations": [
                # 7-day rolling averages
                {
                    "type": "rolling",
                    "window": 7,
                    "method": "mean",
                    "columns": ["symptom_score", "sleep_hours", "activity_level"],
                    "output_suffix": "_7day_avg"
                },
                # 7-day rolling standard deviations (volatility)
                {
                    "type": "rolling",
                    "window": 7,
                    "method": "std",
                    "columns": ["symptom_score", "sleep_hours"],
                    "output_suffix": "_7day_std"
                },
                # Lag features (previous day and previous week)
                {
                    "type": "lag",
                    "periods": [1, 7],
                    "columns": ["symptom_score", "medication_dose"]
                },
                # Day-to-day changes
                {
                    "type": "diff",
                    "periods": 1,
                    "columns": ["symptom_score", "sleep_hours", "activity_level"]
                },
                # Exponentially weighted moving averages
                {
                    "type": "ewm",
                    "alpha": 0.3,
                    "columns": ["symptom_score", "sleep_hours", "activity_level"]
                }
            ]
        },
        # Engineer additional features
        {
            "type": "feature_engineering",
            "features": [
                # Medication effectiveness ratio
                {
                    "type": "ratio",
                    "numerator": "symptom_score_diff_1",
                    "denominator": "medication_dose",
                    "output_column": "medication_effectiveness"
                },
                # Sleep-activity interaction
                {
                    "type": "interaction",
                    "columns": ["sleep_hours_7day_avg", "activity_level_7day_avg"],
                    "output_column": "sleep_activity_interaction"
                }
            ]
        }
    ]
)

print("Original patient time series data:")
print(patient_ts_data.head())
print("\nML-ready time series data:")
print(ml_ready_ts_data.head())
```

## 12. Integration with Machine Learning Pipelines

### 12.1 ML Pipeline Integration

```python
# app/utils/ml_pipeline.py
from typing import Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.utils.data_transformation import DataTransformationService
from app.utils.logging import get_logger

logger = get_logger(__name__)

class MLPipelineService:
    """
    Service for integrating data transformation with machine learning pipelines.
    """
    
    def __init__(self, data_transformation_service: Optional[DataTransformationService] = None):
        """
        Initialize the ML pipeline service.
        
        Args:
            data_transformation_service: DataTransformationService instance
        """
        self.data_service = data_transformation_service or DataTransformationService()
    
    def prepare_data_for_training(
        self,
        data: Union[Dict, List, pd.DataFrame],
        transformations: List[Dict],
        target_column: str,
        feature_columns: Optional[List[str]] = None,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare data for training a machine learning model.
        
        Args:
            data: Input data
            transformations: List of transformations to apply
            target_column: Column to use as target variable
            feature_columns: Columns to use as features (if None, use all except target)
            test_size: Proportion of data to use for testing
            random_state: Random seed for train-test split
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        # Transform the data
        transformed_data = self.data_service.transform_data(data, transformations)
        
        # Convert to DataFrame if necessary
        if not isinstance(transformed_data, pd.DataFrame):
            if isinstance(transformed_data, dict):
                transformed_data = pd.DataFrame([transformed_data])
            elif isinstance(transformed_data, list):
                transformed_data = pd.DataFrame(transformed_data)
            else:
                raise ValueError(f"Unsupported data type: {type(transformed_data)}")
        
        # Handle missing values
        transformed_data = transformed_data.dropna()
        
        # Select features and target
        if feature_columns is None:
            feature_columns = [col for col in transformed_data.columns if col != target_column]
        
        X = transformed_data[feature_columns].values
        y = transformed_data[target_column].values
        
        # Split into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        return X_train, X_test, y_train, y_test
    
    def create_pipeline(
        self,
        model_type: str = 'random_forest',
        model_params: Optional[Dict] = None,
        include_scaler: bool = True
    ) -> Pipeline:
        """
        Create a scikit-learn pipeline with preprocessing and model.
        
        Args:
            model_type: Type of model to use
            model_params: Parameters for the model
            include_scaler: Whether to include a StandardScaler in the pipeline
            
        Returns:
            Scikit-learn Pipeline
        """
        steps = []
        
        # Add scaler if requested
        if include_scaler:
            steps.append(('scaler', StandardScaler()))
        
        # Add model
        if model_type == 'random_forest':
            model_params = model_params or {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42
            }
            steps.append(('model', RandomForestRegressor(**model_params)))
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        return Pipeline(steps)
    
    def train_model(
        self,
        data: Union[Dict, List, pd.DataFrame],
        transformations: List[Dict],
        target_column: str,
        feature_columns: Optional[List[str]] = None,
        model_type: str = 'random_forest',
        model_params: Optional[Dict] = None,
        include_scaler: bool = True,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[Pipeline, Dict]:
        """
        Train a machine learning model with the given data and transformations.
        
        Args:
            data: Input data
            transformations: List of transformations to apply
            target_column: Column to use as target variable
            feature_columns: Columns to use as features
            model_type: Type of model to use
            model_params: Parameters for the model
            include_scaler: Whether to include a StandardScaler in the pipeline
            test_size: Proportion of data to use for testing
            random_state: Random seed for train-test split
            
        Returns:
            Tuple of (trained_pipeline, performance_metrics)
        """
        # Prepare data
        X_train, X_test, y_train, y_test = self.prepare_data_for_training(
            data, transformations, target_column, feature_columns, test_size, random_state
        )
        
        # Create pipeline
        pipeline = self.create_pipeline(model_type, model_params, include_scaler)
        
        # Train model
        pipeline.fit(X_train, y_train)
        
        # Evaluate model
        train_score = pipeline.score(X_train, y_train)
        test_score = pipeline.score(X_test, y_test)
        
        # Calculate predictions and errors
        y_pred = pipeline.predict(X_test)
        mse = np.mean((y_test - y_pred) ** 2)
        mae = np.mean(np.abs(y_test - y_pred))
        
        # Compile metrics
        metrics = {
            'train_r2': train_score,
            'test_r2': test_score,
            'mse': mse,
            'mae': mae,
            'n_train': len(X_train),
            'n_test': len(X_test)
        }
        
        logger.info(f"Model trained with metrics: {metrics}")
        
        return pipeline, metrics
    
    def save_pipeline(self, pipeline: Pipeline, filepath: str) -> None:
        """
        Save a trained pipeline to disk.
        
        Args:
            pipeline: Trained scikit-learn Pipeline
            filepath: Path to save the pipeline to
        """
        joblib.dump(pipeline, filepath)
        logger.info(f"Pipeline saved to {filepath}")
    
    def load_pipeline(self, filepath: str) -> Pipeline:
        """
        Load a trained pipeline from disk.
        
        Args:
            filepath: Path to load the pipeline from
            
        Returns:
            Loaded scikit-learn Pipeline
        """
        pipeline = joblib.load(filepath)
        logger.info(f"Pipeline loaded from {filepath}")
        return pipeline
```

## 13. Usage Examples - ML Pipeline Integration

### 13.1 Training a Predictive Model

```python
import pandas as pd
from app.utils.data_transformation import DataTransformationService
from app.utils.ml_pipeline import MLPipelineService

# Create services
data_service = DataTransformationService()
ml_service = MLPipelineService(data_service)

# Load patient data (in a real scenario, this would come from a database)
patient_data = pd.read_csv("patient_longitudinal_data.csv")

# Define transformations for feature engineering
transformations = [
    # Normalize numeric features
    {
        "type": "normalize",
        "method": "min_max",
        "columns": ["age", "baseline_severity", "treatment_duration_weeks"]
    },
    # Generate time series features
    {
        "type": "time_series",
        "time_column": "visit_date",
        "operations": [
            {
                "type": "rolling",
                "window": 3,
                "method": "mean",
                "columns": ["symptom_score", "medication_adherence", "side_effect_severity"]
            },
            {
                "type": "lag",
                "periods": [1],
                "columns": ["symptom_score", "medication_adherence"]
            },
            {
                "type": "diff",
                "periods": 1,
                "columns": ["symptom_score", "side_effect_severity"]
            }
        ]
    },
    # Engineer additional features
    {
        "type": "feature_engineering",
        "features": [
            {
                "type": "ratio",
                "numerator": "symptom_score_diff_1",
                "denominator": "medication_adherence",
                "output_column": "treatment_response_rate"
            },
            {
                "type": "interaction",
                "columns": ["medication_adherence", "side_effect_severity_rolling_3_mean"],
                "output_column": "adherence_side_effect_interaction"
            }
        ]
    },
    # One-hot encode categorical variables
    {
        "type": "feature_engineering",
        "features": [
            {
                "type": "one_hot",
                "column": "diagnosis",
                "output_column": "diagnosis"
            },
            {
                "type": "one_hot",
                "column": "medication_class",
                "output_column": "medication"
            }
        ]
    }
]

# Train a model to predict symptom improvement
pipeline, metrics = ml_service.train_model(
    data=patient_data,
    transformations=transformations,
    target_column="symptom_improvement",
    model_type="random_forest",
    model_params={
        "n_estimators": 200,
        "max_depth": 15,
        "min_samples_leaf": 5,
        "random_state": 42
    }
)

print("Model training metrics:")
for metric, value in metrics.items():
    print(f"  {metric}: {value}")

# Save the trained pipeline
ml_service.save_pipeline(pipeline, "symptom_improvement_predictor.joblib")
```

### 13.2 Using a Trained Model for Predictions

```python
import pandas as pd
from app.utils.data_transformation import DataTransformationService
from app.utils.ml_pipeline import MLPipelineService

# Create services
data_service = DataTransformationService()
ml_service = MLPipelineService(data_service)

# Load the trained pipeline
pipeline = ml_service.load_pipeline("symptom_improvement_predictor.joblib")

# Load new patient data for prediction
new_patient_data = pd.read_csv("new_patient_data.csv")

# Apply the same transformations used during training
transformations = [
    # Same transformations as in the training example
    # ...
]

# Prepare the data for prediction
transformed_data = data_service.transform_data(new_patient_data, transformations)

# Select feature columns (must match those used during training)
feature_columns = [
    "age_normalized", "baseline_severity_normalized", "treatment_duration_weeks_normalized",
    "symptom_score_rolling_3_mean", "medication_adherence_rolling_3_mean",
    "side_effect_severity_rolling_3_mean", "symptom_score_lag_1",
    "medication_adherence_lag_1", "symptom_score_diff_1", "side_effect_severity_diff_1",
    "treatment_response_rate", "adherence_side_effect_interaction",
    "diagnosis_MDD", "diagnosis_GAD", "diagnosis_Bipolar",
    "medication_SSRI", "medication_SNRI", "medication_Atypical"
]

# Make predictions
X_new = transformed_data[feature_columns].values
predictions = pipeline.predict(X_new)

# Add predictions to the original data
new_patient_data["predicted_symptom_improvement"] = predictions

print("Predictions for new patients:")
print(new_patient_data[["patient_id", "visit_date", "predicted_symptom_improvement"]])
```

## 14. Best Practices

1. **Data Privacy**: Always anonymize PHI before using patient data for analytics or ML.

2. **Data Quality**: Implement thorough data validation and cleaning before transformation.

3. **Feature Selection**: Use domain knowledge to select relevant features for ML models.

4. **Cross-Validation**: Use k-fold cross-validation for more robust model evaluation.

5. **Model Interpretability**: Prefer interpretable models for clinical applications.

6. **Regularization**: Apply appropriate regularization to prevent overfitting.

7. **Pipeline Versioning**: Version control your transformation pipelines and ML models.

8. **Documentation**: Document all transformations applied to data for reproducibility.

9. **Monitoring**: Implement monitoring for data drift and model performance degradation.

10. **Validation**: Validate model predictions against clinical expertise.

## 15. HIPAA Compliance Considerations

1. **De-identification**: Ensure all PHI is properly de-identified before using for analytics.

2. **Audit Trails**: Maintain comprehensive logs of all data transformations.

3. **Access Controls**: Restrict access to raw patient data and transformation tools.

4. **Secure Storage**: Store transformed data securely with appropriate encryption.

5. **Minimum Necessary**: Only transform and use the minimum data necessary for the task.

6. **Re-identification Risk**: Regularly assess the risk of re-identification in transformed data.

7. **Data Use Agreements**: Ensure appropriate agreements are in place for data use.

8. **Model Security**: Secure ML models that may have learned patterns from PHI.

## 16. Conclusion

The HIPAA-compliant Data Transformation Utility is a critical component of the NOVAMIND platform's analytics and machine learning infrastructure. By implementing robust techniques for data anonymization, normalization, feature engineering, and time series processing, it enables advanced analytics while maintaining strict compliance with privacy regulations. This utility plays a key role in extracting valuable insights from patient data to improve treatment outcomes while protecting patient privacy.
