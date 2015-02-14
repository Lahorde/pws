#!/bin/bash
source ../connection_identifiers.sh

date=$(date '+%s')
data=$(mysql -s -u open2300 -pmysql2300 -D open2300 << !
SELECT timestamp, rec_date, rec_time, ROUND((temp_out * 9 / 5 + 32), 2) AS temp_outf,
ROUND((dewpoint * 9 / 5 + 32), 2) AS dewpointf, rel_hum_out,
ROUND(windspeed * 2.23693629, 2) AS windspeedmph,
wind_angle,
ROUND(rain_1h / 25.4, 2) AS rain_1hin, ROUND(rain_24h / 25.4, 2) AS rain_24hin,
ROUND(rel_pressure / 33.8638864, 3) AS rel_pressurein
FROM weather ORDER BY timestamp DESC LIMIT 1 ;
!
)
if [ $? -ne 0 ]
then
echo "Erreur accés base MySql meteo !"
exit 1
fi

liste="timestampws rec_date rec_time temp_outf dewpointf rel_hum_out windspeedmph wind_angle rain_1hin rain_24hin rel_pressurein"
echo $data | while read $liste
do
datews=`echo $timestampws | cut -c1-8`
heuresws=`echo $timestampws | cut -c9-10`
minutesws=`echo $timestampws | cut -c11-12`
secondesws=`echo $timestampws | cut -c13-14`
secondesdata=`date +%s -d $datews`
timestamp=$(echo "$secondesdata + $heuresws*3600 + $minutesws*60 + $secondesws" | bc)
diffsecondes=$(( $date - $timestamp ))
#echo "Diff. sec. = $diffsecondes"
if [ $diffsecondes -gt 600 ]
then
echo "Donné Ws2300 plus à jour !"
exit 1
fi

BASEURL_wu="weatherstation.wunderground.com"
PATH_wu="/weatherstation/updateweatherstation.php"
SOFTWARETYPE_wu="open2300%20v1.10"
date_wu=$(date -u "+dateutc=%Y-%m-%d+%H%%3A%M%%3A%S")
url_wu="http://$BASEURL_wu$PATH_wu?ID=$WU_PWS_ID&PASSWORD=$WU_PWD&$date_wu&tempf=$temp_outf&dewptf=$dewpointf&humidity=$rel_hum_out&windspeedmph=$windspeedmph&winddir=$wind_angle&rainin=$rain_1hin&dailyrainin=$rain_24hin&baromin=$rel_pressurein&softwaretype=open2300%20v1.10m&action=updateraw"
#echo $url_wu
reponse_wu=$(wget -q -O - "$url_wu")
#echo $reponse_wu
if [ "$reponse_wu" != "success" ]
then
echo "$reponse_wu"
echo "Erreur mise à jour station WS2300 sur Weather UnderGround !"
fi
done