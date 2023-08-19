# Base image
FROM python:3.10
# Copy the Pipfile file to the container
COPY Pipfile /Pipfile
# This already specifies the versions etc. so we can just copy it
COPY Pipfile.lock /Pipfile.lock
# Upgrade pip
RUN pip install --upgrade pip
# Install pipenv
RUN pip install pipenv
# Install the dependencies
RUN pipenv install
# Install cron
RUN apt-get update && apt-get -y install cron

# Copy the folders and scripts
COPY src /src
COPY run.py /run.py
RUN chmod 0744 /run.py

# Schedule the run.py script to run every day at 6h
COPY crontab /etc/cron.d/crontab

# Sets permissions (644 owner can read and write, group and others can read)
RUN chmod 0644 /etc/cron.d/crontab
RUN crontab /etc/cron.d/crontab
RUN touch /var/log/cron.log

# Expose ports
# Prefect
EXPOSE 4200

# Start servers
# Run at startup, not during building of the image
# Use of "pipenv" and "run" instead of "pipenv shell" (create a shell initialized with all the pipenv environment variables)
# Allow traffic from outside the container
CMD ["cron", "&&", "pipenv", "run", "prefect", "server", "start", "--host", "0.0.0.0"]
