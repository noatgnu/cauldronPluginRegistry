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
RUN chmod +x /app/run.sh

# Expose port 8000
EXPOSE 8000

# Run the entrypoint script
CMD ["/app/run.sh"]
