FROM python:3.10-slim

# Install system deps
RUN apt-get update && apt-get install -y libpq-dev gcc

# Set workdir
WORKDIR /app

# Copy code
COPY . /app/

# Install Python deps
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Collect static files
RUN mkdir -p /tmp/static && python manage.py collectstatic --noinput

# Expose the Django dev server port
EXPOSE 8000

# Command to run the server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
