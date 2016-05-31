# PWS
## Description

Connect your Personal Weather Station (PWS) and get its data on a nice desktop widget.

## Steps

  - get a PWS -> connect it to a linux machine (PWS gateway)

Gateway  in ``` ./pws_gateway/ ``` sends : 

  - outdoor data to http://www.wunderground.com/

Indoor data get from PWS or some other sensors must be saved to an influxdb. 
 
  - display your pws data ``` ./pws_client ```

  - fill all personal info in ``` ./pws_params.sh ```

## PWS gateway - results

Here are your pws page on wunderground :

![alt text](https://github.com/Lahorde/pws/raw/master/snapshot/weather_underground.png)

## pws_client - results

Here is result in xfce :

![alt text](https://github.com/Lahorde/pws/raw/master/snapshot/pws_conky.jpg)

## References

  * http://blog.vermot.net/2013/01/14/raspberrypi-utilisation-dopen2300-pour-les-stations-meteo-la-crosse-technology/
  * http://letchap.github.io/2013/07/08/afficher-la-meteo-avec-conky-et-python-1ere-partie/
  * Icon glossary - http://www.wunderground.com/weather/api/d/docs?d=resources/phrase-glossary
  * https://github.com/bacpluszero/pioupiou-v0
