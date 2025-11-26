# Multi-stage build for Cloud Run deployment
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install dependencies directly (extract from pyproject.toml)
RUN pip install --no-cache-dir \
    fastapi>=0.122.0 \
    uvicorn>=0.38.0 \
    pyyaml>=6.0.3 \
    pydantic>=2.12.5 \
    pydantic-settings>=2.12.0 \
    google-genai>=1.52.0 \
    google-cloud-texttospeech>=2.14.0

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (profiles are inside src/)
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8080

# Run the application
CMD ["sh", "-c", "uvicorn rehearsed_multi_student.api.main:app --host 0.0.0.0 --port ${PORT}"]
