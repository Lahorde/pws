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

# Emoncms Key for home data
export EMONCMS_KEY=""
export EMONCMS_HUMIDITY_FIELD=""
export EMONCMS_TEMP_FIELD=""

# where are polling data
export PWS_POLLING_DATA_PATH=""

# logs
export PWS_LOG_PATH=""