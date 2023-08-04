import pandas as pd 
from dotenv import load_dotenv
import os
import numpy as np

import mlflow
from datetime import date

def modify_data(data_name: str) -> pd.DataFrame:
    """ Modify data to be used for training.

    Parameters
    ----------
    data_name : str
        Path to the data file.
    
    Returns
    -------
    pd.DataFrame
        Modified data.
    """

    data = pd.read_pickle(data_name).sort_values("Date") # Load data

    # Find the maximum date in the DataFrame
    max_date = data.index.max()

    # Filter the DataFrame to get only the rows with the maximum date
    data = data[data.index == max_date]

    # Rename columns by shifting names one place to the left
    old_col_names = data.filter(like="close_growth").columns.tolist()
    last_col_name = old_col_names[-1] # get last element
    old_col_names.pop() # remove last element from list

    new_col_names = data.filter(like="close_growth_lag").columns.tolist()

    data = data.drop(columns=last_col_name) # drop last column

    # Using list comprehension to create the dictionary
    mapping = {old_col_names[i]: new_col_names[i] for i in range(len(old_col_names))}

    # Rename the columns using the dictionary
    data.rename(columns=mapping, inplace=True)

    return data

def make_predictions(data: pd.DataFrame, preprocessor_name: str, model_name: str, data_path: str, tracking_uri: str, experiment_name: str, stage: str = "Production") -> None:
    """ Make predictions with the best model for the next day.

    Parameters
    ----------
    data : pd.DataFrame
        Data to make predictions on.
    preprocessor_name : str
        Name of the preprocessor.
    model_name : str
        Name of the model.
    data_path : str
        Path to the data folder.
    tracking_uri : str
        Tracking uri.
    experiment_name : str
        Name of the experiment.
    stage : str, optional
        Stage of the model, by default "Production"
    
    Returns
    -------
    None, but puts .json file in data folder with advice.
    """

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    # Load model
    preprocessor = mlflow.sklearn.load_model(model_uri=f"models:/{preprocessor_name}/{stage}")
    model = mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{stage}")

    # Make predictions
    data_reduced = preprocessor.transform(data)
    predictions = model.predict(data_reduced).tolist()

    # Give advice based on predictions
    advice = pd.DataFrame({"ticker": data["ticker"], "prediction": predictions})
    advice["advice"] = advice["prediction"].apply(lambda x: "BUY" if x[0] > 0 else "SELL")
    advice.reset_index(drop=True, inplace=True)

    # Write predictions to json file
    advice.set_index("ticker", inplace=False).to_json(f'{data_path}/advice.json')

    return None


