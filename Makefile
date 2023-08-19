#contains all of the steps that will be called by the ci/cd pipeline

quality_checks:
	pipenv run isort .
	pipenv run black .

test:
	pipenv run pytest tests/

build:
	docker build -t tradingadviceregistry.azurecr.io/trading_advice:latest -f src/predict/app/Dockerfile .
	docker build -t tradingadviceregistry.azurecr.io/mlflow:latest -f src/train_model/Dockerfile .
	docker build -t tradingadviceregistry.azurecr.io/evidently:latest -f src/monitoring/Dockerfile .
	docker build -t tradingadviceregistry.azurecr.io/prefect:latest .

login:
	docker login -u ${AZ_REGISTRY_USERNAME} -p ${AZ_REGISTRY_PASSWORD} tradingadviceregistry.azurecr.io

#gets variables from .env file automatically (restart terminal after changing .env file)

push:
	docker push tradingadviceregistry.azurecr.io/trading_advice:latest
	docker push tradingadviceregistry.azurecr.io/mlflow:latest
	docker push tradingadviceregistry.azurecr.io/evidently:latest
	docker push tradingadviceregistry.azurecr.io/prefect:latest

dev_install:
	pipenv install --dev
	pipenv run pre-commit install

deploy:
	curl -X POST -k "${PORTAINER_WEBHOOK_URL}"
#updates stack using portainer api
