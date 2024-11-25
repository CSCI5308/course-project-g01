# Use an official Python image as the base
FROM python:3.12-slim

# Set environment variables to prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install system packages and Python dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && python3 -m spacy download en_core_web_sm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code (including the MLbackend folder)
COPY . /app/

# Set the working directory for the application (pointing to MLbackend where app.py resides)
WORKDIR /app/MLbackend

# Expose the desired port (if your app runs on a specific port)
EXPOSE 3000

# Command to run your app
CMD ["python", "-m", "MLbackend.app"]
