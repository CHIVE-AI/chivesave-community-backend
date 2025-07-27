# Use a lightweight Python base image
FROM python:3.10-slim-buster

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY ./app /app/app

# Create directories for artifacts at the root of the WORKDIR
RUN mkdir -p artifacts current_active_artifact

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application
# Point to the app.main module
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
