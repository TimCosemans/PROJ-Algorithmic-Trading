PROJ-Algorithmic-Trading
==============================

Project for the course MLOps Zoomcamp.

Problem statement
-----------------

As a trader of stocks, you might want to know when to sell and buy stocks. This repo answers this question by using a machine learning model to predict the price of a stock for the next day, based on data from the past 60 days. It does so for all the stocks currently belonging to the [BEL 2O index](https://live.euronext.com/en/product/indices/BE0389555039-XBRU/market-information) and returns the trading advice (BUY/SELL) as well as the prediction of next day's closing stock price for each ticker through an API (available at http://172.187.161.17:9696/advice). This API can be called on from the trader's application of choice.


Model training
--------------

All code for getting the data, training the model, making predictions and monitoring model performance is available in the [source folder](./src/). [Data](./src/data/) is pulled each time through the [Yahoo Finance API](https://pypi.org/project/yfinance/). After data cleaning, a linear regression is set up to predict the relative change in price for the next day. The amount of lags to take into account when predicting the price change is finetuned using [Hyperopt](http://hyperopt.github.io/hyperopt/). The finetuning process is logged in [MLFlow](./src/train_model/), after which the best model (based on the MAPE of the test set) is registered and put into production. The UI to monitor this process is available at http://172.187.161.17:5000.

Prediction
----------
After putting the model into production, it is used to make [predictions](./src/predict/) for the next day's change in closing price for each ticker. These predictions are then used to determine whether to buy or sell the stock. The trading advice is returned through a [flask API](./src/predict/app/), available at http://172.187.161.17:9696/advice. Because models can start to drift over time, we model the performance of the model using [Evidently](https://evidentlyai.com/). The UI to monitor this process is available at http://172.187.161.17:8080.

Orchestration and deployment
----------------------------
The whole process is orchestrated using Prefect. The [orchestration script](./run.py) is run hourly using a [Cron](./crontab) job, and fetches the data, trains the model, registers the best model, makes predictions for the API to use and monitors model performance. The Prefect UI for this project is available at http://172.187.161.17:4200.

The [orchestration script](./Dockerfile), as well as the [model training logging](./src/train_model/Dockerfile), [performance monitoring](./src/monitoring/Dockerfile) and [API app](](./src/predict/app/Dockerfile)) are run in docker containers that are registered on the [Azure Container Registry](https://azure.microsoft.com/en-us/services/container-registry/). We use [Portainer](172.187.161.17:9443) on an [Azure Virtual Machine](https://azure.microsoft.com/en-us/services/virtual-machines/) to set these up using the [docker compose file](./docker-compose.yml).

You can login to the Portainer portal as a read-only user with the following credentials:
username: reviewer
password: MLOpsReview2!

CI/CD and pre-commit hooks
--------------------------
Before pushing code to the repo, we check whether the code style using a [pre-commit hook](.pre-commit-config.yaml). Packages and versions are specified in the [Pipfile](./Pipfile).

We orchestrate CI/CD through the use of a [Makefile](./Makefile), that specifies all the steps to be taken to check code style, perform a [unit test](./tests/), build the docker containers, push them to the Azure Container Registry and deploy them to the Azure Virtual Machine. The [GitHub Actions workflow](.github/workflows/) then uses the steps in this Makefile to build the CI/CD pipeline.

HOW TO RUN
----------
To run the docker compose file in the cloud (and start all of the necessary services), you need to create a virtual machine. You can do this in the Azure portal.
Expose ports 4200, 9696, 8080, 9443 and 5000 by adding them in the networking section. Set destination port ranges to the ones you want to open, specify TCP protocol. SSH into the virtual machine and install the [docker engine](https://docs.docker.com/engine/install/ubuntu/) and [portainer](https://docs.portainer.io/start/install-ce/server/docker/linux).

Then go to the portainer UI and create a new stack. Link your repo to the stack and add the docker compose file.
Go to the container registry on Azure to retrieve the login server, username and password. Then add these to the portainer UI under registries.

Copy the reference data and tickers.pkl by using the terminal of your local laptop:

```scp -r data username@ip.of.vm:/home/username #secure copy protocol ```

Then, ssh into the virtual machine and copy the data to the docker volume

```sudo docker cp data prefect:/shared```

Now, all the services should be running. You can check this by going to the portainer UI and checking the containers.
