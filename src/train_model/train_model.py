import pandas as pd 
from dotenv import load_dotenv
import os

import mlflow
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient

from datetime import date

from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_percentage_error
from scipy.sparse import issparse

from hyperopt import hp, fmin, tpe, Trials
import numpy as np

def get_tracking_uri(env_path: str = ".env") -> str:
    """Get the tracking uri from the .env file.
    
    Parameters
    ----------
    env_path : str, optional
        Path to the .env file, by default ".env"
        
    Returns
    -------
    str
        Tracking uri.
    """

    # get environment variables
    load_dotenv(dotenv_path=env_path)
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")

    return MLFLOW_TRACKING_URI


def train_test_split(data_name: str, train_ratio: float = 0.8) -> tuple:
    """ Split data into train and test set.

    Parameters
    ----------
    data_name : str
        Path to the data file.
    train_ratio : float, optional
        Ratio of the data to be used for training, by default 0.8
    
    Returns
    -------
    tuple
        Tuple containing the train and test sets.
    """

    data = pd.read_pickle(data_name).sort_values("Date") # Load data

    # Assuming the dataset is sorted by date, you can split by index
    train_size = int(train_ratio * len(data))  
    train_data = data.iloc[:train_size]
    test_data = data.iloc[train_size:]

    # Create features and target
    y_train = train_data.sort_values(["ticker", "Date"]).filter(items=["close_growth"]).reset_index(drop=True)
    complete_train = y_train.notna().to_numpy().flatten()
    y_train = y_train[complete_train]
    X_train = train_data.sort_values(["ticker", "Date"]).filter(regex="close_growth_lag|ticker").reset_index(drop=True)[complete_train]

    y_test = test_data.sort_values(["ticker", "Date"]).filter(items=["close_growth"]).reset_index(drop=True)
    complete_test = y_test.notna().to_numpy().flatten()
    y_test = y_test[complete_test] # Remove NaNs from target 
    X_test = test_data.sort_values(["ticker", "Date"]).filter(regex="close_growth_lag|ticker").reset_index(drop=True)[complete_test] # Remove corresponding NaNs from features

    return X_train, X_test, y_train, y_test

def train_model(tracking_uri: str, experiment_name: str, X_train: pd.DataFrame, X_test: pd.DataFrame, y_train: pd.DataFrame, y_test: pd.DataFrame, max_lags_used: int = 10) -> None:
    """Train the model and log results of optimisation in MLFlow.

    Parameters
    ----------
    tracking_uri : str
        Tracking uri.
    experiment_name : str
        Name of the experiment.
    X_train : pd.DataFrame
        Training set of features.
    X_test : pd.DataFrame
        Test set of features.
    y_train : pd.DataFrame
        Training set of target.
    y_test : pd.DataFrame
        Test set of target.
    max_lags_used : int
        Max number of lags used in the model.

    Returns
    -------
    None, but logs results of optimisation in MLFlow.
    """

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    def objective_function(params):
        """Objective function for hyperparameter optimization.
        """

        n_lags_used = params["n_lags_used"]
        print(f"n_lags_used: {n_lags_used}")

        with mlflow.start_run() as run: 

            # Make dummies for categorical features
            cat_features = ["ticker"]
            cat_transformer = Pipeline(steps=[("create_dummies", OneHotEncoder(handle_unknown="ignore"))])

            num_features = [f"close_growth_lag_{i}" for i in range(1, n_lags_used + 1)]

            preprocessor = ColumnTransformer(transformers=[("cat", cat_transformer, cat_features), 
                                                        ('num', 'passthrough', num_features)], remainder="drop")

            
            X_train_reduced = preprocessor.fit_transform(X_train)

            # Convert to DataFrame (handle both dense and sparse data)
            if issparse(X_train_reduced):
                X_train_reduced = pd.DataFrame.sparse.from_spmatrix(X_train_reduced, columns=preprocessor.get_feature_names_out(input_features=X_train.columns))
            else:
                X_train_reduced = pd.DataFrame(X_train_reduced, columns=preprocessor.get_feature_names_out(input_features=X_train.columns))

            # Delete rows with missing values
            X_train_reduced = X_train_reduced.dropna()
            y_train_reduced = y_train.iloc[X_train_reduced.index, :]
        
            # Log parameters
            mlflow.log_param("model", "linear_regression")
            mlflow.log_param("features", f"close growth ({n_lags_used} lags) + ticker dummy")
            mlflow.log_param("target", "close growth")
            mlflow.log_param("n", len(X_train_reduced))
            mlflow.log_param("n_lags_used", n_lags_used)

            # Fit model
            model = LinearRegression()
            model.fit(X_train_reduced, y_train_reduced)

            # Log model and preprocessor
            mlflow.sklearn.log_model(preprocessor, "preprocessor")
            mlflow.sklearn.log_model(model, "model")

            # Make predictions
            X_test_reduced = preprocessor.transform(X_test)
            y_pred = model.predict(X_test_reduced)

            # Evaluate model
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            mape = mean_absolute_percentage_error(y_test, y_pred)

            # Log metrics
            mlflow.log_metric("mse", mse)
            mlflow.log_metric("r2", r2)
            mlflow.log_metric("mape", mape)
        
        return mape
    
    # Define the search space
    space = {
        'n_lags_used': hp.choice('n_lags_used', np.arange(1, max_lags_used + 1, dtype=int)),
    }

    # Hyperparameter optimization and registration of experiments
    num_evals = 5
    trials = Trials()
    fmin(fn=objective_function, space=space, algo=tpe.suggest, max_evals=num_evals, trials=trials, rstate=np.random.default_rng(42))

    return None

def register_best_model(tracking_uri: str, experiment_name: str, model_name: str, preprocessor_name: str) -> None: 
    """Register the best model and preprocessor in MLFlow.

    Parameters
    ----------
    tracking_uri : str
        Tracking uri.
    experiment_name : str
        Name of the experiment.
    model_name : str
        Name of the model.
    preprocessor_name : str
        Name of the preprocessor.
    
    Returns
    -------
    None, but registers the best model and preprocessor in MLFlow.
    """
    
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)


    # Search for the best model in terms of MAPE
    run = mlflow.search_runs(
        experiment_names=[experiment_name],
        filter_string="",
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=1,
        order_by=["metrics.mape ASC"],
    )

    # Get run ID and model/preprocessor URIs
    run_id = run.run_id[0]
    model_uri = f"runs:/{run_id}/model"
    preprocessor_uri = f"runs:/{run_id}/preprocessor"

    # Register the model and preprocessor
    model_details = mlflow.register_model(model_uri=model_uri, name=model_name)
    preprocessor_details = mlflow.register_model(model_uri=preprocessor_uri, name=preprocessor_name)

    client = MlflowClient(tracking_uri=tracking_uri)

    # Transition to production stage
    client.transition_model_version_stage(
        name=model_details.name,
        version=model_details.version,
        stage="Production", 
        archive_existing_versions=True
    )

    client.transition_model_version_stage(
        name=preprocessor_details.name,
        version=preprocessor_details.version,
        stage="Production", 
        archive_existing_versions=True
)
 
    return None
