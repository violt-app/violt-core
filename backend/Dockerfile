FROM python:3.11-slim

WORKDIR /app

# Update pip and install dependencies
RUN pip install --upgrade pip

# Install system dependencies (platform-specific)
RUN if [ "$(uname -s)" = "Linux" ]; then \
        apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs config

# Set environment variables
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000
# Add platform detection with default to auto-detect
ENV PLATFORM=auto

# Create entrypoint script for platform-specific initialization
RUN echo '#!/bin/sh\n\
# Detect platform if set to auto\n\
if [ "$PLATFORM" = "auto" ]; then\n\
    export PLATFORM=$(uname -s | tr "[:upper:]" "[:lower:]")\n\
    echo "Auto-detected platform: $PLATFORM"\n\
fi\n\
\n\
# Create required directories\n\
mkdir -p /app/data /app/logs /app/config\n\
\n\
# Run the application\n\
exec uvicorn src.main:app --host $HOST --port $PORT\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Initialize Alembic environment (creates 'migrations' folder and alembic.ini)
# RUN alembic init migrations
# RUN alembic revision --autogenerate -m "Initial migration"
# RUN alembic upgrade head
# Initialize database (if applicable)
# RUN python -c "from src.database import init_db; init_db()"

# Expose the application port
EXPOSE 8000

# Run the application using the entrypoint script
CMD ["/app/entrypoint.sh"]
