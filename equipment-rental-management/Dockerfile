# Equipment Rental Management: Flask app image for CISC 327 A4.
# Build:  docker build -t cisc327-a4 .
# Run:    docker run --rm -p 5000:5000 cisc327-a4
FROM python:3.12-slim

# Don't write .pyc files into the image, and flush logs straight to `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only what the app needs to run.
COPY app/ app/
COPY run.py notification_service.py ./

# Run as an unprivileged user instead of root.
RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

# Listen on 0.0.0.0 so the app is reachable from outside the container.
CMD ["flask", "--app", "run", "run", "--host=0.0.0.0", "--port=5000"]
