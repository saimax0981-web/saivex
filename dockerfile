FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PORT=5000
ENV PRODUCTION=1

RUN apt-get update && apt-get install -y build-essential libjpeg-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p instance uploads static/generated static/generated/uploads logs

EXPOSE 5000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]