#! /bin/sh

AQI=$(grep 'AQI ' /tmp/wu_polling.data | awk -F " " '{$1=$2=""; print $3}')
color='000000'

if [ -z $AQI ]
then
  exit 1
fi

if [ $AQI -lt 35 ]
then
  color='green'
elif [ $AQI -ge 35 ] && [ $AQI -lt 50 ]
then  
  color='yellow'
elif [ $AQI -ge 50 ] && [ $AQI -lt 75 ] 
then  
  color='orange'
else
  color='red'
fi

echo -n "\${image $PWS_CLIENT_PROJECT_PATH/icons/aqi_${color}.png -p $1,$2 -s $3x$3}"
exit 0
