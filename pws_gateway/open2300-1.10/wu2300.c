/*  open2300 - wu2300.c
 *  
 *  Version 1.10
 *  
 *  Control WS2300 weather station
 *  
 *  Copyright 2004-2005, Kenneth Lavrsen
 *  This program is published under the GNU General Public license
 */

#define DEBUG 0  // wu2300 stops writing to standard out if setting this to 0

#include "rw2300.h"

/********** MAIN PROGRAM ************************************************
 *
 * This program reads all current weather data from a WS2300
 * and sends it to Weather Underground.
 *
 * It takes one parameter which is the config file name with path
 * If this parameter is omitted the program will look at the default paths
 * See the open2300.conf-dist file for info
 *
 ***********************************************************************/
int main(int argc, char *argv[])
{
	WEATHERSTATION ws2300;
	struct config_type config;
	unsigned char urlline[3000] = "";
	char datestring[50];        //used to hold the date stamp for the log file
	double tempfloat;
	time_t basictime;

	get_configuration(&config, argv[1]);

	ws2300 = open_weatherstation(config.serial_device_name);

	
	/* START WITH URL, ID AND PASSWORD */

	sprintf(urlline, "http://%s%s?ID=%s&PASSWORD=%s",
			WEATHER_UNDERGROUND_BASEURL,WEATHER_UNDERGROUND_PATH,
			config.weather_underground_id,config.weather_underground_password);

	/* GET DATE AND TIME FOR URL */
	
	time(&basictime);
	basictime = basictime - atof(config.timezone) * 60 * 60;
	strftime(datestring,sizeof(datestring),"&dateutc=%Y-%m-%d+%H%%3A%M%%3A%S",
	         localtime(&basictime));
	sprintf(urlline, "%s%s", urlline, datestring);


	/* READ TEMPERATURE OUTDOOR - deg F for Weather Underground */

	sprintf(urlline, "%s&tempf=%.2f", urlline,
	        temperature_outdoor(ws2300, FAHRENHEIT) );


	/* READ DEWPOINT - deg F for Weather Underground*/
	
	sprintf(urlline, "%s&dewptf=%.2f", urlline, dewpoint(ws2300, FAHRENHEIT) );


	/* READ RELATIVE HUMIDITY OUTDOOR */

	sprintf(urlline, "%s&humidity=%d", urlline, humidity_outdoor(ws2300) );


	/* READ WIND SPEED AND DIRECTION - miles/hour for Weather Underground */

	sprintf(urlline,"%s&windspeedmph=%.2f", urlline,
	        wind_current(ws2300, MILES_PER_HOUR, &tempfloat) );
	sprintf(urlline,"%s&winddir=%.1f",	urlline, tempfloat);


	/* READ RAIN 1H - inches for Weather Underground */
	
	sprintf(urlline,"%s&rainin=%.2f", urlline, rain_1h(ws2300, INCHES) );


	/* READ RAIN 24H - inches for Weather Underground */

	sprintf(urlline,"%s&dailyrainin=%.2f", urlline, rain_24h(ws2300, INCHES) );


	/* READ RELATIVE PRESSURE - Inches of Hg for Weather Underground */

	sprintf(urlline,"%s&baromin=%.3f",urlline,
	        rel_pressure(ws2300, INCHES_HG) );


	/* ADD SOFTWARE TYPE AND ACTION */
	sprintf(urlline,"%s&softwaretype=%s%s&action=updateraw",urlline,
	        WEATHER_UNDERGROUND_SOFTWARETYPE,VERSION);


	/* SEND DATA TO WEATHER UNDERGROUND AS HTTP REQUEST */
	/* or print the URL if DEBUG is enabled in the top of this file */

	close_weatherstation(ws2300);

	if (DEBUG)
	{
		printf("%s\n",urlline);
	}
	else
	{
		http_request_url(urlline);
	}
	
	return(0);
}

