# Multi-stage build for Cloud Run deployment
FROM python:3.12-slim as builder

# Install Poetry
RUN pip install poetry==1.8.0

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create virtual env (we're in a container)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY profiles/ ./profiles/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application
CMD exec uvicorn src.rehearsed_multi_student.api.main:app --host 0.0.0.0 --port ${PORT}
