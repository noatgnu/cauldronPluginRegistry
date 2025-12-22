# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y curl gpg
RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/postgresql-archive-keyring.gpg] http://apt.postgresql.org/pub/repos/apt trixie-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get -y install git postgresql-client-16 libssl-dev && \
    apt-get -y upgrade

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
