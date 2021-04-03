#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This application exposes user metrics from Turf to Prometheus.
"""

import os
import logging
import sys
import datetime
import json
from flask import Flask
from celery import Celery
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
app.config['broker_url'] = REDIS_URL
app.config['beat_schedule'] = {
    'get_users_statistics': {
        'task': 'turfgame_exporter.tasks.get_users_statistics',
        'schedule': datetime.timedelta(seconds=(int(CHECK_INTERVAL_SEC))),
    }
}

# Initialize Celery
celery = Celery(app.name, broker=app.config['broker_url'])
celery.conf.update(app.config)
celery.autodiscover_tasks(['turfgame_exporter'])

REDIS_KEY_PREFIX = 'turfgame_user'

ENABLED_METRICS = [
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
     'type': 'counter', 'help': 'Number of unique zones the user has taken'},

     {'turf_name': 'medals', 'prometheus_name': 'medals_taken',
      'type': 'counter', 'help': 'Number of medals the user has taken'}
]

METRIC_NAMES = [metric['turf_name'] for metric in ENABLED_METRICS]
METRIC_NAMES_MAP = {k['turf_name']: k['prometheus_name'] for k in [i for i in ENABLED_METRICS]}


def generate_body():
    """ Returns the HTTP body sent to Turf API """
    body = []
    for user in TURF_USERS:
        body.append({"name": user})

    return body

def update_stats_in_redis(statistics):
    """ Updates keys in Redis for all metrics """
    if len(statistics) == 0:
        log.warning('Got empty response from %s. Check if all usernames in TURF_USERS is valid.', TURF_API_USERS_URL)

    else:
        for user_stat in statistics:
            user_dict = {}

            for key, value in user_stat.items():
                if key in METRIC_NAMES:
                    if key in ['zones', 'medals']:
                        value = len(value)

                    user_dict[METRIC_NAMES_MAP[key]] = value
            REDISCONN.set('{}.{}'.format(REDIS_KEY_PREFIX, user_stat['name']), json.dumps(user_dict))


def generate_response():
    """ Returns response for specific metric """

    response = []
    user_statistics = {}
    failed_users = []

    for user in TURF_USERS:
        data = REDISCONN.get('{}.{}'.format(REDIS_KEY_PREFIX, user))

        try:
            json_data = json.loads(data)

        except TypeError as errormsg:
            log.error('Error when retrieving data for user {}'.format(user), errormsg)
            failed_users.append(user)
            continue

        else:
            user_statistics[user] = json_data

    for metric in ENABLED_METRICS:
        response.append('# HELP {}_{} {}'.format(
            REDIS_KEY_PREFIX,
            metric['prometheus_name'],
            metric['help']))

        response.append('# TYPE {}_{} {}'.format(
            REDIS_KEY_PREFIX,
            metric['prometheus_name'],
            metric['type'].lower()))

        for key, value in user_statistics.items():
            if key not in failed_users:
                response.append('{}_{}{{user="{}"}} {}'.format(
                    REDIS_KEY_PREFIX,
                    metric['prometheus_name'],
                    key,
                    value[metric['prometheus_name']]))

    return response


@app.route('/metrics')
def expose_metrics():
    """ Returns all metrics when /metrics HTTP endpoint is accessed """

    return '\n'.join(generate_response()), {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/ping')
def ping():
    """ Returns success when /ping HTTP endpoint is accessed """
    return 'success'


if __name__ == "__main__":
    app.run()
