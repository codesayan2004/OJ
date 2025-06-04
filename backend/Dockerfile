FROM python:3.11

# Set the working directory
WORKDIR /OJ
COPY . /OJ

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py migrate

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=backend.settings
ENV PYTHONUNBUFFERED=1

CMD [ "python","manage.py","runserver","0.0.0.0:8000" ]
