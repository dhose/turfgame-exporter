web: gunicorn turfgame_exporter.main:app
worker: celery -A turfgame_exporter.main.celery worker --loglevel=info
beat: celery -A turfgame_exporter.main.celery beat
