FROM python:3.11.9-slim-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["/app/docker/entrypoint.sh"]

CMD ["fastapi", "run", "api/main.py"]
