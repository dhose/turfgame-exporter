from __future__ import absolute_import, unicode_literals
from turfgame_exporter.main import celery, generate_body, update_stats_in_redis, TURF_API_USERS_URL
from turfgame_exporter import PROJECT_NAME, PROJECT_URL
import requests
import logging

log = logging.getLogger(__name__)

@celery.task(bind=True)
def get_users_statistics(self):
    """ Scheduled task that every CHECK_INTERVAL_SEC updates user statistics from Turf API """
    self.body = generate_body()
    self.headers = {
        'Content-Type': 'application/json',
        'User-Agent': '%s (%s)' % (PROJECT_NAME, PROJECT_URL)
    }

    try:
        self.response = requests.post(TURF_API_USERS_URL, headers=self.headers, json=self.body, timeout=2)

        if self.response.status_code == 200:
            update_stats_in_redis(self.response.json())

        else:
            log.warning('Got status code %s but 200 was expected.', self.response.status_code)

    except requests.exceptions.RequestException as errormsg:
        log.error(errormsg)
