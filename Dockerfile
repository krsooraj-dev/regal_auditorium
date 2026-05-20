# Use official light-weight Python image
FROM python:3-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set working directory
WORKDIR /app

# Copy dependency definition
COPY requirements.txt /app/

# Install dependencies (using psycopg2-binary for PostgreSQL)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . /app/

# Run database seeder/initializer and launch FastAPI with Uvicorn
CMD sh -c "python -m backend.seed && uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
