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
# MLFlow
EXPOSE 5000

# Start servers
# Run at startup, not during building of the image
# Use of "pipenv" and "run" instead of "pipenv shell" (create a shell initialized with all the pipenv environment variables)
# Set host to 0.0.0.0 to make it accessible from outside the container
CMD ["pipenv", "run", "mlflow", "server", "--host", "0.0.0.0", "--backend-store-uri", "file:///shared/mlruns", "--default-artifact-root", "file:///shared/mlruns"]
