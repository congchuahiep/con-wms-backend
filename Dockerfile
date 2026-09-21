# Container backend cho con-wms (Django + Gunicorn) — chạy được trên
# Google Cloud Run / Fly.io / bất kỳ nơi chạy OCI container nào.
#
# Dùng `uv` để cài dependency nhanh, khớp chính xác `uv.lock`.

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# uv binary manager (cài theo lockfile)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Cài dependency TRƯỚC khi copy code → tận dụng Docker layer cache.
# `--no-install-project`: chỉ cài các thư viện, source sẽ COPY ở bước sau.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy toàn bộ source (xem .dockerignore — không mang .venv/db.sqlite3 của host)
COPY . .

# Static files phải được build SẴN vào image — Cloud Run disk read-only lúc runtime
# (WhiteNoise sẽ phục vụ static/admin từ STATIC_ROOT này).
RUN .venv/bin/python manage.py collectstatic --noinput

EXPOSE 8080
ENV PORT=8080

# - `RUN_MIGRATIONS=1` → chạy `migrate` rồi mới serve dữ liệu
#   (dùng cho Cloud Run Job / lệnh docker run một lần; không bật mặc định để
#   tránh nhiều instance chạy migrate cùng lúc).
# - Log ghi ra stdout/stderr để Cloud Run thu thập.
CMD ["sh", "-c", "if [ \"$RUN_MIGRATIONS\" = \"1\" ]; then .venv/bin/python manage.py migrate --noinput; fi; exec .venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers ${WEB_CONCURRENCY:-2} --timeout 300 --access-logfile - --error-logfile -"]