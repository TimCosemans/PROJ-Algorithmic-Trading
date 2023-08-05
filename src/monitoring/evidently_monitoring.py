
import pandas as pd 
from dotenv import load_dotenv
import os
import numpy as np
import uuid

import mlflow
from datetime import date

from evidently.metrics import DatasetDriftMetric, DataDriftTable, ColumnDriftMetric, RegressionQualityMetric
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset, DataQualityPreset, RegressionPreset
from evidently.report import Report
from evidently.ui.dashboards import CounterAgg, DashboardPanelCounter, DashboardPanelPlot, PanelValue, PlotType, ReportFilter
from evidently.ui.workspace import Workspace, WorkspaceBase


def get_workspace_name(env_path: str = ".env") -> str:
    """Get the name of the workspace.   

    Parameters
    ----------
    env_path : str, optional
        Path to the .env file, by default ".env"
    
    Returns
    -------
    str
        Name of the workspace.
    """

    # get environment variables
    load_dotenv(dotenv_path=env_path)
    EVIDENTLY_WORKSPACE = os.getenv("EVIDENTLY_WORKSPACE")

    return EVIDENTLY_WORKSPACE

def get_reference_data(data_path: str) -> str:
    """Get the reference data.

    Parameters
    ----------
    data_path : str
        Path to the data folder.
    
    Returns
    -------
    str
        Path to the reference dataset.
    """

    # Load reference data
    reference_path = f"{data_path}/BEL_20_reference.pkl" # Path to the reference dataset

    if not os.path.exists(reference_path): # If the reference dataset does not exist
        ref_data = pd.read_pickle(f"{data_path}/BEL_20.pkl") # Load data
        ref_data.to_pickle(reference_path) # Save data as reference dataset
    
    return reference_path

def prepare_data(data_name: str, ref_data_name: str, tracking_uri: str, experiment_name: str, model_name: str, preprocessor_name: str, stage: str = "Production") -> tuple:
    """Prepare data for Evidently.

    Parameters
    ----------
    data_name : str
        Path to the data file.
    ref_data_name : str
        Path to the reference data file.
    tracking_uri : str
        Tracking uri of MLFlow.
    experiment_name : str
        Name of the experiment.
    model_name : str
        Name of the model.
    preprocessor_name : str
        Name of the preprocessor.
    stage : str, optional
        Stage of the model, by default "Production"
    
    Returns
    -------
    tuple with the reference data and the current data
    """    

    # Load reference data
    ref_data = pd.read_pickle(ref_data_name) 

    # Load latest model
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    preprocessor = mlflow.sklearn.load_model(model_uri=f"models:/{preprocessor_name}/{stage}")
    model = mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{stage}")

    # Load latest data
    data = pd.read_pickle(data_name)

    # Make target and prediction column for Evidently to work
    ref_data["target"] = ref_data["close_growth"]
    ref_data.dropna(inplace=True) # Drop rows with missing values
    ref_data["prediction"] = model.predict(preprocessor.transform(ref_data)) # Apply both model and preprocessor to reference data

    data["target"] = data["close_growth"]
    data.dropna(inplace=True) # Drop rows with missing values
    data["prediction"] = model.predict(preprocessor.transform(data)) # Apply both model and preprocessor to reference data

    return ref_data, data

def open_workspace_project(workspace_name: str, project_name: str = "Algorhythmic Trading") -> tuple:
    """Open the workspace and project in Evidently.

    Parameters
    ----------
    workspace_name : str
        Name of the workspace.
    project_name : str, optional
        Name of the project, by default "Algorhythmic Trading"
    
    Returns
    -------
    tuple with the project id and the workspace
    """

    # Open workspace

    if os.path.exists(workspace_name):
        ws = Workspace(workspace_name)
        project = ws.get_project(ws.list_projects()[0].id) # If workspace exists, open workspace and project
    else:
        ws = Workspace.create(workspace_name)
        project = ws.create_project(project_name) # If workspace does not exist, create workspace and project

        project.dashboard.add_panel(
            DashboardPanelCounter(
                filter=ReportFilter(metadata_values={}, tag_values=[]),
                agg=CounterAgg.NONE,
                title="Stock Price Growth Rate Prediction",
            )
        )

        project.dashboard.add_panel(
            DashboardPanelPlot(
                title="Dataset Drift",
                filter=ReportFilter(metadata_values={}, tag_values=[]),
                values=[
                    PanelValue(metric_id="DatasetDriftMetric", field_path=DataDriftTable.fields.share_of_drifted_columns, legend="Drift Share")
                ], 
                plot_type=PlotType.LINE
            )
        )

        project.dashboard.add_panel(
            DashboardPanelPlot(
                title="Target Drift",
                filter=ReportFilter(metadata_values={}, tag_values=[]),
                values=[
                    PanelValue(metric_id="ColumnDriftMetric", field_path=ColumnDriftMetric.fields.drift_score, legend="Drift Score")
                ], 
                plot_type=PlotType.LINE
            )
        )

        project.dashboard.add_panel(
        DashboardPanelPlot(
            title="MAPE",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            values=[
            PanelValue(
                metric_id="RegressionQualityMetric",
                field_path=RegressionQualityMetric.fields.current.mean_abs_perc_error,
                legend="MAPE",
            ),
        ],
        plot_type=PlotType.LINE,
        size=2,
        )
    )
  
        project.save()

    return project.id, ws 

def add_report(workspace: WorkspaceBase, project_id: uuid.UUID, ref_data: pd.DataFrame, data: pd.DataFrame) -> None: 
    """Add report to project.

    Parameters
    ----------
    workspace : WorkspaceBase
        Workspace.
    project_id : uuid.UUID
        Project id.
    ref_data : pd.DataFrame
        Reference data.
    data : pd.DataFrame
        Current data.
    
    Returns
    -------
    None, but adds report to project
    """

    # Add report to project
    report = Report(
            metrics=[
                DataDriftPreset(),
                DataQualityPreset(),
                TargetDriftPreset(),
                RegressionPreset()
            ]
        )

    report.run(reference_data=ref_data.reset_index(drop=True), current_data=data.reset_index(drop=True))

    workspace.add_report(project_id, report)

    return None