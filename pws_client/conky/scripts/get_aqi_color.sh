#! /bin/sh

AQI=$(grep 'AQI ' /tmp/wu_polling.data | awk -F " " '{$1=$2=""; print $3}')
color='000000'

if [ -z $AQI ]
then
  exit 1
fi

if [ $AQI -lt 35 ]
then
  color='76D250'
elif [ $AQI -ge 35 ] && [ $AQI -lt 50 ]
then  
  color='FBD948'
elif [ $AQI -ge 50 ] && [ $AQI -lt 75 ] 
then  
  color='F119B48'
elif [ $AQI -ge 75 ] && [ $AQI -lt 100 ] 
then  
  color='D93241'
else
  color='red'
fi

echo -n "\${color $color}"
exit 0
