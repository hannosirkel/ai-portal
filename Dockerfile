FROM python:3.13-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

USER 10001:10001
EXPOSE 8080

CMD ["python", "-m", "uvicorn", "portal.server:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
