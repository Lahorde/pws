#!/bin/sh
echo reading pws client parameters

#Weather Underground PWS ID
export WU_PWS_ID=""

# Weather underground key
export WU_KEY=""

# Weather underground password
export WU_PWD=""

# Weather station server prefix
export VENT_PIOU_PIOU_URL_PREFIX="http://api.pioupiou.fr/v1/live/"

# WU stations for wind
export VENT_1_URL_SUFFIX=""

# Piou Piou stations for wind
export VENT_1_PIOU_PIOU_URL_SUFFIX=""

# influxdb Key for home data
export INFLUX_DB_HOST_URL=""
export INFLUX_DB_HOST_PORT=""
export INFLUXDB_NAME=""
export INFLUX_DB_USER=""
export INFLUX_DB_PASS=""
export INFLUXDB_SERIES_SUFFIX=""
export INFLUXDB_HOME_TEMP_FIELD=""
export INFLUXDB_HOME_HUMIDITY_FIELD=""

# Rhone Alpes Air network
# Rhone Alpes station id: http://www.air-rhonealpes.fr/donnees/acces-par-station
export POLLUTION_STATION_ID=""

# Air Visual API
export AIR_VISUAL_KEY=""
export AIR_VISUAL_STATION_LAT=""
export AIR_VISUAL_STATION_LONG=""

# where are polling data
export PWS_POLLING_DATA_PATH=""

