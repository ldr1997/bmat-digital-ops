
#Tells Docker to use the official python 3 image from dockerhub as a base image
FROM python:3.9
# Sets an environmental variable that ensures output from python is sent straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1
# Sets the container's working directory to /app
WORKDIR /app
# Copies all files from our local project into the container
COPY . /app
# runs the pip install command for all packages listed in the requirements.txt file
RUN pip install pipenv && pipenv install --system

# # Pull a base image
# FROM python:3.9

# # Set environment variables
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# # Create a working directory for the django project
# WORKDIR /code

# ADD ./code
# # Copy requirements to the container
# COPY Pipfile Pipfile.lock /code/

# # Install the requirements to the container
# RUN pip install pipenv && pipenv install --system

# # Copy the project files into the working directory
# COPY . /code/

# # Open a port on the container
EXPOSE 8000