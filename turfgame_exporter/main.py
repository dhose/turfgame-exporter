#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This application exposes user metrics from Turf to Prometheus].
"""

import os
import logging
import sys
import datetime
from flask import Flask
from celery import Celery
import requests
import redis

# Environment variables
REDIS_URL = os.getenv('REDIS_URL')
TURF_API_USERS_URL = os.getenv('TURF_API_USERS_URL', 'https://api.turfgame.com/v4/users')
TURF_USERS = [u.strip() for u in os.getenv('TURF_USERS').split(',')]
CHECK_INTERVAL_SEC = os.getenv('CHECK_INTERVAL_SEC', '300')
LOGLEVEL = os.getenv('LOGLEVEL', 'INFO').upper()

# Logging configuration
log = logging.getLogger(__name__)
log.setLevel(LOGLEVEL)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
log.addHandler(handler)

REDISCONN = redis.from_url(REDIS_URL)

app = Flask(__name__)

# Celery configuration
app.config['CELERY_BROKER_URL'] = REDIS_URL
app.config['CELERYBEAT_SCHEDULE'] = {
    'get_users_statistics': {
        'task': 'turfgame_exporter.main.get_users_statistics',
        'schedule': datetime.timedelta(seconds=(int(CHECK_INTERVAL_SEC)))
    }
}

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

REDIS_METRIC_PREFIX = 'turfgame'

ACCEPTED_METRICS = [
    {'turf_name': 'zones', 'prometheus_name': 'zones_owned',
     'type': 'gauge', 'help': 'Number of zones owned'},

    {'turf_name': 'pointsPerHour', 'prometheus_name': 'points_per_hour',
     'type': 'gauge', 'help': 'Number of points received per hour'},

    {'turf_name': 'points', 'prometheus_name': 'points',
     'type': 'gauge', 'help': 'Number of points received in this round'},

    {'turf_name': 'blocktime', 'prometheus_name': 'blocktime',
     'type': 'counter', 'help': 'The users blocktime'},

    {'turf_name': 'taken', 'prometheus_name': 'taken',
     'type': 'counter', 'help': 'Number of zones taken'},

    {'turf_name': 'totalPoints', 'prometheus_name': 'total_points',
     'type': 'counter', 'help': 'The users total points'},

    {'turf_name': 'rank', 'prometheus_name': 'rank',
     'type': 'counter', 'help': 'The users rank'},

    {'turf_name': 'place', 'prometheus_name': 'place',
     'type': 'gauge', 'help': 'The users place'},

    {'turf_name': 'uniqueZonesTaken', 'prometheus_name': 'unique_zones_taken',
     'type': 'counter', 'help': 'Number of unique zones the user has taken'}
]

METRIC_NAMES = [metric['turf_name'] for metric in ACCEPTED_METRICS]

def generate_body():
    """ Returns the HTTP body sent to Turf API """
    body = []
    for user in TURF_USERS:
        body.append({"name": user})

    return body

def update_stats_in_redis(statistics):
    """ Updates keys in Redis for all metrics """
    for user_stat in statistics:
        for key, value in user_stat.items():
            if key in METRIC_NAMES:
                if key == 'zones':
                    value = len(value)

                redis_key = '{}.{}.{}'.format(REDIS_METRIC_PREFIX, user_stat['name'], key)
                REDISCONN.set(redis_key, value)

@celery.task(bind=True)
def get_users_statistics(self):
    """ Scheduled task that every CHECK_INTERVAL_SEC updates statistics from Turf API """
    self.body = generate_body()
    self.headers = {'Content-Type': 'application/json'}

    try:
        self.response = requests.post(TURF_API_USERS_URL, headers=self.headers, json=self.body)

        if self.response.status_code == 200:
            update_stats_in_redis(self.response.json())

        else:
            log.warning('Got status code %s but 200 was expected.', self.response.status_code)

    except requests.exceptions.RequestException as errormsg:
        log.error(errormsg)

def generate_response(metric):
    """ Returns response for specific metric """
    metric_response = []
    metric_response.append('# HELP {}_{} {}'.format(
        REDIS_METRIC_PREFIX,
        metric['prometheus_name'],
        metric['help']))
    metric_response.append('# TYPE {}_{} {}'.format(
        REDIS_METRIC_PREFIX,
        metric['prometheus_name'],
        metric['type'].lower()))

    for user in TURF_USERS:
        try:
            value = REDISCONN.get('{}.{}.{}'.format(REDIS_METRIC_PREFIX, user, metric['turf_name']))
            metric_response.append('{}_{}{{user="{}"}} {}'.format(
                REDIS_METRIC_PREFIX,
                metric['prometheus_name'],
                user,
                int(value)))

        except TypeError:
            log.error('%s.%s.%s does not exist in Redis.',
                      REDIS_METRIC_PREFIX,
                      user,
                      metric['turf_name'])
            continue

    return metric_response

@app.route('/metrics')
def expose_metrics():
    """ Returns all metrics when /metrics HTTP endpoint is accessed """
    response = []

    for metric in ACCEPTED_METRICS:
        response = response + generate_response(metric)

    return '\n'.join(response), {'Content-Type': 'text/plain'}

@app.route('/ping')
def ping():
    """ Returns success when /ping HTTP endpoint is accessed """
    return 'success'

if __name__ == "__main__":
    app.run()
