# Start with the Python 3.10-slim image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libmariadb-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*  # Clean up

# Set the working directory inside the container
WORKDIR /app

COPY requirements.txt .



ENV PYTHONPATH=/app

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Copy the application code into the container
COPY . /app/

# Expose port 8000 for FastAPI
EXPOSE 8000




# Run the application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
