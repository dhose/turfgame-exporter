web: gunicorn turfgame_exporter.main:app
worker: celery worker -A turfgame_exporter.main.celery --loglevel=info
beat: celery -A turfgame_exporter.main.celery beat
