### Description

Connect your Personal Weather station and get its data on a nice desktop widget.

More precisely :
-get a PWS -> connect it to a linux machine (pws gateway)
Gateway sends : 
 - indoor data sent to http://emoncms.org/
 - outdoor data to http://www.wunderground.com/
 
-display your pws data -> on a linux machine data are polled from emoncms and displayed in a conky

### pws_gateway

Files pws_gateway folder
Some useful links : 
http://blog.vermot.net/2013/01/14/raspberrypi-utilisation-dopen2300-pour-les-stations-meteo-la-crosse-technology/

Here are your pws page on wunderground :

![alt text](https://github.com/Lahorde/pws/raw/master/snapshot/weather_underground.png)

### pws_client

Files in pws_client
Some useful links :
http://letchap.github.io/2013/07/08/afficher-la-meteo-avec-conky-et-python-1ere-partie/

Here is result in xfce :

![alt text](https://github.com/Lahorde/pws/raw/master/snapshot/pws_conky.jpg)
