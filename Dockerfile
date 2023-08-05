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

# Copy the folders and scripts
COPY src /src
COPY run.py /run.py

# Expose ports
# Prefect
EXPOSE 4200

# Start servers 
# Run at startup, not during building of the image
# Use of "pipenv" and "run" instead of "pipenv shell" (create a shell initialized with all the pipenv environment variables)
CMD ["pipenv", "run", "prefect", "server", "start"] 