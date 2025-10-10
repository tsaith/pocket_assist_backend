FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# Install packages
RUN apt-get update 

# Copy project to container
WORKDIR /app
COPY . /app


# Install poetry and python packages
RUN pip install --upgrade pip \
    && pip install poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies with poetry
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# Set virtual environment
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Open specified port, allow system outside container to access application  
EXPOSE 8080


# Start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]