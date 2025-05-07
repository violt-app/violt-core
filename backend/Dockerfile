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

# Install specific version of bcrypt to avoid warnings
RUN pip install bcrypt==4.1.3

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

# Initialize Alembic environment (creates 'migrations' folder and alembic.ini)
# RUN alembic init migrations
# RUN alembic revision --autogenerate -m "Initial migration"
# RUN alembic upgrade head
# Initialize database (if applicable)
# RUN python -c "from src.database import init_db; init_db()"

# Expose the application port
EXPOSE 8000

# Run the application directly using uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
