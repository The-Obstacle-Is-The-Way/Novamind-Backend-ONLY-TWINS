import pytest
"""
Sample venv_only test that demonstrates using third-party packages without external services.

This test uses pandas for data processing but doesn't connect to any external services.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


@pytest.mark.venv_only
def test_pandas_processing():
    """Test that pandas can be used for data processing in venv_only tests."""
    # Create a sample DataFrame
    dates = pd.date_range(datetime.now() - timedelta(days=10), periods=10, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'value': np.random.randn(10)
    })
    
    # Perform some operations
    df['rolling_mean'] = df['value'].rolling(window=3).mean()
    df['cumulative_sum'] = df['value'].cumsum()
    
    # Verify results
    assert len(df) == 10
    assert 'rolling_mean' in df.columns
    assert 'cumulative_sum' in df.columns
    assert pd.isna(df['rolling_mean'].iloc[0])
    assert pd.isna(df['rolling_mean'].iloc[1])
    assert not pd.isna(df['rolling_mean'].iloc[2])
