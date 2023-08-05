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

# Expose ports
# Evidently
EXPOSE 8000

# Start servers 
# Run at startup, not during building of the image
# Use of "pipenv" and "run" instead of "pipenv shell" (create a shell initialized with all the pipenv environment variables)
# workspace is a placeholder, the actual workspace will be mounted from the host
CMD ["pipenv", "run", "evidently", "ui", "--workspace", "/workspace"] 