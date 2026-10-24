FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv

# api/requirements.txt installs ../../packages/shared, so keep the same layout.
# Compose provides the shared package as the "shared" build context.
WORKDIR /app/services/api
COPY --from=shared . /app/packages/shared
COPY api/requirements.txt ./
RUN uv pip install --system -r requirements.txt

COPY api ./

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
