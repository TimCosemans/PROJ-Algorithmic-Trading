from unittest.mock import MagicMock
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.train_model.train_model import train_test_split


@pytest.fixture
def mock_data():
    # Create mock data
    data = pd.DataFrame(
        {
            "Date": pd.date_range(start="2020-01-01", periods=100),
            "ticker": np.random.choice(["AAPL", "GOOG", "AMZN"], 100),
            "close_growth": np.random.rand(100),
            "close_growth_lag_1": np.random.rand(100),
        }
    )
    return data


def test_train_test_split(mock_data):
    with patch("pandas.read_pickle", return_value=mock_data):
        train_ratio = 0.8
        X_train, X_test, y_train, y_test = train_test_split(
            "fake_data.pkl", train_ratio
        )

    # Perform assertions to check the behavior of the function
    assert isinstance(X_train, pd.DataFrame)
    assert isinstance(X_test, pd.DataFrame)
    assert isinstance(y_train, pd.DataFrame)
    assert isinstance(y_test, pd.DataFrame)

    assert len(X_train) == 80
    assert len(X_test) == 20
    assert len(y_train) == 80
    assert len(y_test) == 20
