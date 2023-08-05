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

# Copy the app folder to the container /app folder
COPY src/app /app 
# Set the working directory to /app
WORKDIR /app 

# Expose port 9696
EXPOSE 9696 
# Ran at startup
CMD ["pipenv", "run", "gunicorn", "-c", "gunicorn_config.py"] 