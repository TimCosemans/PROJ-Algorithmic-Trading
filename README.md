PROJ-Algorithmic-Trading
==============================

Project for the course MLOps Zoomcamp. 

As a trader, you might want to know when to sell and buy stocks

Based on the closing price each day, you will decide whether to buy or sell the stock the next day. 
Because the price can be assumed to be non-stationary, we will work with the relative change in price instead of the price itself.


Before you run, create a .env file with x
DATAPATH: the path to the data folder x
MLFLOW_TRACKING_URI: your mlflow tracking uri (e.g., a local folder) x

To see your mlflow ui, run mlflow server in the source folder. Experiments always include the date of day on which they were run. 


The src-folder contains all of the functions needed to get the data, train and evaluate the model and register the best model. 
The run.py script is the prefect orchestration script that runs the functions in the correct order. It fetches the data on a daily basis, trains the model and registers the best model. Then ths model returns buy or sell signals for the next day. These signals are distributed through a flask api. To get these, run 

gunicorn -c gunicorn_config.py 'app:app' in the app directory

To run locally, type python run.py local in the terminal. Then start the ui with prefect server start

launch the monitorign dasboard with evidently ui --workspace ./evidently_workspace 

create a prefect.yaml file by running prefect deploy in the root folder and following the wizard

use lsof -i :5000 to find the process id of the flask api and kill it with kill -9 <pid>


containerize process
deploy to cloud

username: timcosemans
password: VXLccyU6wp8%48

to build the docker containers, run 

docker build -t trading_advice:latest -f src/predict/app/Dockerfile .
docker build -t mlflow:latest -f src/train_model/Dockerfile .
docker build -t evidently:latest -f src/monitoring/Dockerfile .
docker build -t prefect:latest .

all in the root folder 

to run an individual container, run

docker run -p 5000:5000 trading_advice:latest


then run 

docker compose up -d

install portainer 

then go to localhost:9443 and check the logs for debugging. you can run code directly in portainer 

shut down the stack using docker compose down
if you update a container, docker compose does not register this (down and up again). if you make a new one, then it does

Deploy to Cloud 
----------------
To deploy to cloud, you first need to create both a resource group, a service principal and a storage account in Azure. 

Then create a container registry 

az login
az group create --name myResourceGroup --location eastus
az acr create --resource-group myResourceGroup --name <acrName> --sku Basic
az acr login --name <acrName>

prefix all images in the docker compose with 'tradingadviceregistry.azurecr.io/' so the image can be pulled to run in Azure Container Registry

then, change their tag to match this before you upload them

docker tag trading_advice tradingadviceregistry.azurecr.io/trading_advice:latest
docker tag mlflow tradingadviceregistry.azurecr.io/mlflow:latest
docker tag evidently tradingadviceregistry.azurecr.io/evidently:latest
docker tag prefect tradingadviceregistry.azurecr.io/prefect:latest

see if it worked by typing

docker images 


then, push them to the registry

docker push tradingadviceregistry.azurecr.io/trading_advice:latest
docker push tradingadviceregistry.azurecr.io/mlflow:latest
docker push tradingadviceregistry.azurecr.io/evidently:latest
docker push tradingadviceregistry.azurecr.io/prefect:latest

to list the images: 
az acr repository list --name tradingadviceregistry --output table


then create an azure file share and mount this as a storage account in your docker compose file

az storage share create --name trading-advice-share --account-name tradingadviceblob

you can copy files to this share using the azure storage dexplorer



then, create a container instance

docker login azure
docker context create aci trading-advice-context
docker context use trading-advice-context

login to the container registry 
az acr login --name tradingadviceregistry --expose-token
docker login tradingadviceregistry.azurecr.io --username 00000000-0000-0000-0000-000000000000 --password-stdin <<< $TOKEN

docker compose up 
docker ps 

# Update DNS name label (restarts container), leave other properties unchanged
az container create --resource-group rg-Databricks_ML_Studio_Training --name proj-algorithmic-trading  --dns-name-label mlops




az container exec --resource-group rg-Databricks_ML_Studio_Training --name proj-algorithmic-trading --container-name prefect --exec-command "/bin/bash"

Project Organization
------------

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py
    │
    └── tox.ini            <- tox file with settings for running tox; see tox.readthedocs.io


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
