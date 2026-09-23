FROM python:3.13-slim-bookworm@sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

USER 10001:10001
EXPOSE 8080

CMD ["python", "-m", "uvicorn", "portal.server:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
