# turfgame_exporter

Flask application that exposes user metrics from [Turf](https://turfgame.com/) to [Prometheus](https://prometheus.io/). The application is built as an [12-factor](https://12factor.net/) app and uses Redis as backing service.

## Deployment using Dokku

###### On host running Dokku

```
$ dokku apps:create turfgame_exporter && \
  dokku redis:create turfgame_exporter && \
  dokku redis:link turfgame_exporter turfgame_exporter && \
  dokku config:set turfgame_exporter TURF_USERS=<turf username>
```

###### In a directory containing a clone of this repository

```
git remote add turfgame_exporter dokku@<host_running_dokku>:turfgame_exporter
```

###### Deploy with git push

```
$ git push turfgame_expoter master
```

## Configuration

Configuration is done using environment variables.

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
# HELP turfgame_zones_owned Number of zones owned
# TYPE turfgame_zones_owned gauge
turfgame_zones_owned{user="someuser"} 1
# HELP turfgame_points_per_hour Number of points received per hour
# TYPE turfgame_points_per_hour gauge
turfgame_points_per_hour{user="someuser"} 4
# HELP turfgame_points Number of points received in this round
# TYPE turfgame_points gauge
turfgame_points{user="someuser"} 14956
# HELP turfgame_blocktime The users blocktime
# TYPE turfgame_blocktime counter
turfgame_blocktime{user="someuser"} 16
# HELP turfgame_taken Number of zones taken
# TYPE turfgame_taken counter
turfgame_taken{user="someuser"} 1387
# HELP turfgame_total_points The users total points
# TYPE turfgame_total_points counter
turfgame_total_points{user="someuser"} 218623
# HELP turfgame_rank The users rank
# TYPE turfgame_rank counter
turfgame_rank{user="someuser"} 26
# HELP turfgame_place The users place
# TYPE turfgame_place gauge
turfgame_place{user="someuser"} 1774
# HELP turfgame_unique_zones_taken Number of unique zones the user has taken
# TYPE turfgame_unique_zones_taken counter
turfgame_unique_zones_taken{user="someuser"} 263
```

