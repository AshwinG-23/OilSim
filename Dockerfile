FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

CMD ["sh", "-c", "gunicorn web.app:app --timeout 180 --workers 2 --bind 0.0.0.0:$PORT"]
