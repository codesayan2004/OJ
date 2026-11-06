# CodeSphere web image: Django served by Gunicorn.
# User code is NOT executed in this container: for every run the web app
# asks the host's Docker daemon to start a fresh, locked-down container
# from the runner image (../sandbox/Dockerfile, coderunner/sandbox.py).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=backend.settings

# Docker CLI only (no daemon) to launch sandbox containers via the
# mounted /var/run/docker.sock.
COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh \
 && useradd --uid 1000 --create-home app \
 && mkdir -p /data /app/staticfiles \
 && chown -R app:app /app /data

USER app
EXPOSE 8000

# entrypoint.sh: migrate + collectstatic, then exec the CMD (Gunicorn).
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "backend.wsgi:application", "--config", "gunicorn.conf.py"]
