# Dockerfile
FROM python:3.10-slim

# Install system packages (if needed)
RUN apt-get update && apt-get install -y gcc libpq-dev curl chromium-driver

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install coverage flake8

# Collect static files (optional at build)
RUN mkdir -p /tmp/static
RUN python manage.py collectstatic --noinput

# Expose the app port
EXPOSE 8000

# Default command (overwritten in CI)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
