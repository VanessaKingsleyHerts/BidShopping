# Dockerfile – builds app image from pre-installed CI base
FROM registry.gitlab.com/uhthesis/bidshopping:ci-base

WORKDIR /app

# Copy source code and install only prod dependencies
COPY . .

# Ensure only minimal runtime deps are added here
RUN pip install -r requirements.txt

# Static files collection
RUN mkdir -p /tmp/static && python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
