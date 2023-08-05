from src.data.get_data import load_datapath, get_BEL20_composition, get_data
from src.train_model.train_model import get_tracking_uri, train_test_split, train_model, register_best_model
from src.predict.advice import modify_data, make_predictions
from src.monitoring.evidently_monitoring import get_workspace_name, get_reference_data, prepare_data, open_workspace_project, add_report

from datetime import date
import pandas as pd

from prefect import flow, task

@task(retries=2, retry_delay_seconds=5)
def get_data_task(env_path: str = ".env", length_of_data: str = "60d", n_lags: int = 10) -> str:
    """ Get data from Yahoo Finance API.
    """
    data_path = load_datapath(env_path=env_path)
    tickers = get_BEL20_composition(data_path=data_path)

    data_name = get_data(tickers=tickers, data_path=data_path, length_of_data=length_of_data, n_lags=n_lags)

    return data_name

@task
def train_test_split_task(data_name: str, train_ratio: float = 0.8) -> tuple:
    """ Split data into train and test set.
    """
    X_train, X_test, y_train, y_test = train_test_split(data_name=data_name, train_ratio=train_ratio)

    return X_train, X_test, y_train, y_test

@task
def train_model_task(X_train: pd.DataFrame, X_test: pd.DataFrame, y_train: pd.DataFrame, y_test: pd.DataFrame, max_lags_used: int = 10, env_path: str = ".env") -> str:
    """ Train model and log it in MLFlow.
    """
    tracking_uri = get_tracking_uri(env_path=env_path)
    experiment_name = f"stock-prediction-BEL-20-{date.today()}"
    train_model(tracking_uri=tracking_uri, experiment_name=experiment_name, X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test, max_lags_used=max_lags_used)

    return experiment_name

@task
def register_best_model_task(experiment_name: str, env_path: str = ".env") -> None:
    """ Register best model and preprocessor in MLFlow.
    """
    tracking_uri = get_tracking_uri(env_path=env_path)

    model_name = f"best-model-{date.today()}"
    preprocessor_name = f"preprocessor-{date.today()}"
    register_best_model(tracking_uri=tracking_uri, experiment_name=experiment_name, model_name=model_name, preprocessor_name=preprocessor_name)
    
    return model_name, preprocessor_name

@task
def make_predictions_task(data_name: str, model_name: str, preprocessor_name: str, experiment_name: str, env_path: str = ".env") -> None:
    """ Make predictions with the best model for the next day.
    """
    
    data = modify_data(data_name=data_name)

    data_path = load_datapath(env_path=env_path)
    tracking_uri = get_tracking_uri(env_path=env_path)

    make_predictions(data=data, preprocessor_name=preprocessor_name, model_name=model_name, data_path=data_path, tracking_uri=tracking_uri, experiment_name=experiment_name, stage="Production")

    return None

@task
def model_monitoring(data_name: str, model_name: str, preprocessor_name: str, experiment_name: str, env_path: str = ".env") -> None:
    """ Monitor model performance with Evidently.
    """
    
    workspace_name = get_workspace_name() # Get workspace name from .env file
    project_id, workspace = open_workspace_project(workspace_name=workspace_name) # Open workspace and project in Evidently

    data_path = load_datapath(env_path=env_path)
    tracking_uri = get_tracking_uri(env_path=env_path)

    ref_data_name = get_reference_data(data_path=data_path) # Get reference data
    ref_data, data = prepare_data(data_name=data_name, ref_data_name=ref_data_name, tracking_uri=tracking_uri, experiment_name=experiment_name, model_name=model_name, preprocessor_name=preprocessor_name, stage="Production") # Prepare data for Evidently

    add_report(project_id=project_id, workspace=workspace, ref_data=ref_data, data=data) # Add report to project
 
@flow
def main_flow() -> None: 
    """ Main flow of the project.
    """

    data_name = get_data_task()

    print(f"Data saved in {data_name}")

    X_train, X_test, y_train, y_test = train_test_split_task(data_name=data_name)
    experiment_name = train_model_task(X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test)

    print(f"Model trained and logged in {experiment_name}")

    model_name, preprocessor_name = register_best_model_task(experiment_name=experiment_name)

    print(f"Best model and preprocessor registered in {experiment_name}")

    make_predictions_task(data_name=data_name, model_name=model_name, preprocessor_name=preprocessor_name, experiment_name=experiment_name)

    print("Predictions made and saved in data folder")

    model_monitoring(data_name=data_name, model_name=model_name, preprocessor_name=preprocessor_name, experiment_name=experiment_name)

    print("Model performance monitored with Evidently")




if __name__ == "__main__":
    main_flow()