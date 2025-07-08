# Dockerfile – app image built *from* ci-base
FROM registry.gitlab.com/uhthesis/bidshopping:ci-base

WORKDIR /app
COPY . .

# Collect static assets
RUN mkdir -p /tmp/static && python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
