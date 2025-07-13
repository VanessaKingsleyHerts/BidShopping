##### Dockerfile — Application Runtime Image #####
FROM registry.gitlab.com/uhthesis/bidshopping:ci-base

# Set workdir
WORKDIR /app

# Cache requirements before copying everything
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Collect static files
RUN mkdir -p /tmp/static && \
    python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
