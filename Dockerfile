FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# uv binary manager (cài theo lockfile)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

RUN .venv/bin/python manage.py collectstatic --noinput

EXPOSE 8080
ENV PORT=8080

CMD [".venv/bin/gunicorn", "config.wsgi:application", \
    "--bind", "0.0.0.0:8080", \
    "--workers", "2", \
    "--timeout", "300", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]
