
FROM python:3.9
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY . /app
RUN pip install pipenv && pipenv install --system
EXPOSE 8000