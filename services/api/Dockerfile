FROM python:3.12.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.lock.txt /app/requirements.lock.txt
RUN pip install --no-cache-dir -r requirements.lock.txt && useradd --uid 10001 --create-home career
COPY services /app/services
COPY config /app/config
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations
COPY scripts /app/scripts
RUN mkdir /app/artifacts && chown career:career /app/artifacts
USER career
ENV PYTHONPATH=/app/services/api
CMD ["sh", "-c", "alembic upgrade head && uvicorn career_app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log"]
