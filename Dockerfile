# Use the official Python 3.11 slim image from the Docker Hub
FROM python:3.11-slim

# Set environment variables to avoid buffering
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 9090

# Command to run the application
CMD ["python", "main.py"]