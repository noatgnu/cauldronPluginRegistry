# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy poetry lock and pyproject files
COPY poetry.lock pyproject.toml /app/

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copy project
COPY . /app/

# Run migrations
RUN poetry run python manage.py migrate
RUN poetry run python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Run gunicorn
CMD ["poetry", "run", "gunicorn", "cauldronPluginRegistry.wsgi:application", "--bind", "0.0.0.0:8000"]
