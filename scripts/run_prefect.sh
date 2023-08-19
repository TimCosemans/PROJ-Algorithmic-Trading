#!/bin/bash
env > /etc/environment
service cron start
pipenv run prefect server start --host 0.0.0.0
