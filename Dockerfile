# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Explicitly create a writable directory for the Hugging Face cache
RUN mkdir -p /app/cache && chmod -R 777 /app/cache

# Set environment variable for the transformers cache
ENV TRANSFORMERS_CACHE=/app/cache

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 7860 available to the world outside this container
EXPOSE 7860

# Define the command to run your app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "main:app"]