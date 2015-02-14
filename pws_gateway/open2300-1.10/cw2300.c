/*  open2300 - cw2300.c
 *
 *  Version 1.10
 *
 *  Send WS2300 weather station data to CWOP
 *  (Citizen Weather Observation Program)
 *
 *  Copyright 2004, Kenneth Lavrsen/Randy Miller
 *  This program is published under the GNU General Public license
 *
 *  Update History:
 *  1.0 2004 Feb 02 Randy Miller     Inital release
 *                  (N6ABM)          based on WU2300 v 1.0.
 *                                   Introduced also the config file
 *
 *  1.2 2004 Mar 07 Kenneth Lavrsen  Completely re-written to match
 *                  (OZ1IDD)         rw2300 v 1.2 and made Windows
 *                                   compatible.
 */

#include "rw2300.h"

#define CW_SOFTWARETYPE   "open2300v"
#define DEBUG 0  // wu2300 stops writing to standard out if setting this to 0


/********** MAIN PROGRAM ************************************************
 *
 * This program reads data from a WS2300 weather station formats and
 * sends it to Citizens Weather Observer Program (CWOP)
 *
 * It takes one parameter which is the config file name with path
 * If this parameter is omitted the program will look at the default paths
 * See the open2300.conf-dist file for info
 *
 ***********************************************************************/
int main(int argc, char *argv[])
{
	WEATHERSTATION ws2300;
	unsigned char aprsline[3000] = "";
	char datestring[50];        //used to hold the date stamp for the log file
	time_t basictime;
	struct config_type config;
	double tempfloat1, tempfloat2;

	get_configuration(&config, argv[1]);

	/* Setup serial port to weather station */
	if ( (ws2300 = open_weatherstation(config.serial_device_name)) < 0 )
	{
		printf("Cannot open serial device %s\n",config.serial_device_name);
 		exit(-1);
	}

	/* GET DATE AND TIME FOR the WX record in UTC */
	time(&basictime);
	basictime = basictime - atof(config.timezone) * 60 * 60;
	strftime(datestring,sizeof(datestring),"@%d%H%Mz",localtime(&basictime));	

	/* BUILD THE DATA STRING, START WITH URL, ID AND PASSWORD */
	sprintf(aprsline, "%s>APRS,TCPXX*,qAX,%s:%s%s/%s",
	        config.citizen_weather_id, config.citizen_weather_id, // Build weather record
	        datestring,                                           // Add date time 
	        config.citizen_weather_latitude, config.citizen_weather_longitude); // Add Lat Lon


	/* READ WIND DIRECTION (_) AND SPEED (/) - wind data must be mph for CWOP  */
	tempfloat1 = wind_current(ws2300, MILES_PER_HOUR, &tempfloat2); // Fetch current wind data
	sprintf(aprsline,"%s_%03.0f", aprsline, tempfloat2);        // _ wind dir degrees
	sprintf(aprsline,"%s/%03.0f", aprsline, tempfloat1);        // / wind speed mph

	/* WIND GUST */
	/* This requires that you reset the station regularly */
	/* Uncomment the two lines below to activate wind gust     */
//	sprintf(aprsline, "%sg%03.0f", aprsline,
//	        wind_minmax(ws2300, MILES_PER_HOUR, NULL, NULL, NULL, NULL));

	/* READ TEMPERATURE OUTDOOR t - Force deg F for CWOP */
	sprintf(aprsline, "%st%03.0f", aprsline, temperature_outdoor(ws2300, FAHRENHEIT));

	/* READ RAIN 1H r - force inches for CWOP*/
	sprintf(aprsline,"%sr%03.0f",aprsline, rain_1h(ws2300, INCHES) *100); // hundredths of an inch

	/* READ RAIN 24H p */
	sprintf(aprsline,"%sp%03.0f",aprsline, rain_24h(ws2300, INCHES) *100); // hundredths of an inch

	/* RAIN SINCE MIDNIGHT P */
	// not directly readable in LaCrosse

	/* READ RELATIVE HUMIDITY OUTDOOR */
	sprintf(aprsline, "%sh%02d", aprsline, humidity_outdoor(ws2300));

	/* READ BAROMETRIC PRESSURE b */
	sprintf(aprsline,"%sb%05.0f",aprsline,(rel_pressure(ws2300, MILLIBARS) *10)); // tenths of milibars

	/* ADD SOFTWARE TYPE AND ACTION  */
	sprintf(aprsline,"%s.%s%s",aprsline, CW_SOFTWARETYPE, VERSION);

	/* MAKE WEATHER STATION AVAILABLE FOR OTHER PROGRAMS */
	close_weatherstation(ws2300);

	/* CONNECT TO SERVER AND SEND THE RECORD */
	if (citizen_weather_send(&config, aprsline) != 0)
	{
		perror("Could not send data to Citizen Weather!\n");
		exit(-1);
	}
	return(0);
}

