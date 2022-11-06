# turfgame_exporter

Flask application that exposes user metrics from [Turf](https://turfgame.com/) to [Prometheus](https://prometheus.io/). The application is built as an [12-factor](https://12factor.net/) app and uses Redis as backing service and Celery for background tasks.

## Deployment using [Dokku](https://github.com/dokku)

###### On host running Dokku

```
$ dokku apps:create turfgame-exporter && \
  dokku redis:create turfgame-exporter && \
  dokku redis:link turfgame-exporter turfgame-exporter && \
  dokku config:set turfgame-exporter TURF_USERS=<turf username> && \
  dokku ps:scale turfgame-exporter beat=1 web=1 worker=1
```

###### In a directory containing a clone of this repository

```
git remote add turfgame-exporter dokku@<host_running_dokku>:turfgame-exporter
```

###### Deploy with git push

```
$ git push turfgame-exporter master
```

## Deployment using [Heroku](https://www.heroku.com/)
https://devcenter.heroku.com/articles/getting-started-with-python

## Configuration

Configuration is done with environment variables using `dokku config:set`:

```
dokku config:set turfgame-exporter TURF_USERS=<turf username>
```

### Required

| Environment variable | Description                            |
| -------------------- | -------------------------------------- |
| REDIS_URL            | Connection string to Redis             |
| TURF_USERS           | Comma separated list of Turf usernames |

### Optional

| Environment variable | Default value                     | Description                                           |
| -------------------- | --------------------------------- | ----------------------------------------------------- |
| TURF_API_USERS_URL   | https://api.turfgame.com/v4/users | Turf API enpoint                                      |
| CHECK_INTERVAL_SEC   | 300                               | Interval in which statistics is polled from Turf API. |
| LOGLEVEL             | INFO                              | Set loglevel                                          |

## Example output

The data exposed when visiting the `/metrics`-endpoint:

```
# HELP turfgame_user_zones_owned Number of zones owned
# TYPE turfgame_user_zones_owned gauge
turfgame_user_zones_owned{user="someuser"} 1
# HELP turfgame_user_points_per_hour Number of points received per hour
# TYPE turfgame_user_points_per_hour gauge
turfgame_user_points_per_hour{user="someuser"} 4
# HELP turfgame_user_points Number of points received in this round
# TYPE turfgame_user_points gauge
turfgame_user_points{user="someuser"} 14956
# HELP turfgame_user_blocktime The users blocktime
# TYPE turfgame_user_blocktime counter
turfgame_user_blocktime{user="someuser"} 16
# HELP turfgame_user_taken Number of zones taken
# TYPE turfgame_user_taken counter
turfgame_user_taken{user="someuser"} 1387
# HELP turfgame_user_total_points The users total points
# TYPE turfgame_user_total_points counter
turfgame_user_total_points{user="someuser"} 218623
# HELP turfgame_user_rank The users rank
# TYPE turfgame_user_rank counter
turfgame_user_rank{user="someuser"} 26
# HELP turfgame_user_place The users place
# TYPE turfgame_user_place gauge
turfgame_user_place{user="someuser"} 1774
# HELP turfgame_user_unique_zones_taken Number of unique zones the user has taken
# TYPE turfgame_user_unique_zones_taken counter
turfgame_user_unique_zones_taken{user="someuser"} 263
# HELP turfgame_user_medals_taken Number of medals the user has taken
# TYPE turfgame_user_medals_taken counter
turfgame_user_medals_taken{user="someuser"} 16
```
