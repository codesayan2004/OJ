FROM python:3.11

# Install compilers and runtimes needed for code execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    default-jdk \
    nodejs npm \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /OJ

# Copy project files
COPY . /OJ

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run Django migrations (safe with SQLite)
RUN python manage.py migrate

# Expose Django's default port
EXPOSE 8000

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=backend.settings
ENV PYTHONUNBUFFERED=1

# Start the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
