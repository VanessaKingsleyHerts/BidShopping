FROM python:3.10

# Set working directory
WORKDIR /app

# Copy your code
COPY . .

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install coverage selenium psycopg2-binary

# Add flake8 (✅ Add this during build!)
RUN pip install flake8

# Optional: expose the port
EXPOSE 8000

# Default command (optional)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
