#contains all of the steps that will be called by the ci/cd pipeline

quality_checks:
	black .

test:
	pytest tests/

build:
	docker build -t tradingadviceregistry.azurecr.io/trading_advice:latest -f src/predict/app/Dockerfile .
	docker build -t tradingadviceregistry.azurecr.io/mlflow:latest -f src/train_model/Dockerfile .
	docker build -t tradingadviceregistry.azurecr.io/evidently:latest -f src/monitoring/Dockerfile .
	docker build -t tradingadviceregistry.azurecr.io/prefect:latest .

login:
	docker login tradingadviceregistry.azurecr.io -u ${AZ_REGISTRY_USERNAME} --password-stdin <<< ${AZ_REGISTRY_PASSWORD}

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
	curl -X POST "https://172.187.161.17:9443/api/stacks/webhooks/a0490689-cf5a-4ed8-b2f2-65e01afd89fb"
#updates stack using portainer api
