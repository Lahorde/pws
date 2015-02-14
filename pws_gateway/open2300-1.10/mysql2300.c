/*       mysql2300.c
 *
 *       Version 1.3 - open2300 1.10
 *
 *       Get data from WS2300 weather station
 *       and add them to MySQL database
 *
 *       Copyright 2003,2004, Kenneth Lavrsen/Thomas Grieder
 *
 *       This program is published under the GNU General Public license
 *
 *  0.1  2004 Feb 21  Thomas Grieder
 *       Creates mysql2300. A Rewrite of log2300.
 *       Logline is now comma delimited for added support to write
 *       to MySQL
 *       (see also http://www.unixreview.com/documents/s=8989/ur0401a/)
 *
 *  1.2  2004 Mar 07  Kenneth Lavrsen
 *       Complete rewrite of the code to support the new rw2300 library.
 *       Logfile feature removed to make it a clean MySQL program.
 *       Added support for config file and program should be able to
 *       compile under Windows with the right MySQL client headers
 *       and libraries installed.
 *
 *  1.3  As 1.2
 */

#include <mysql.h>
#include "rw2300.h"

 
/********** MAIN PROGRAM ************************************************
 *
 * This program reads current weather data from a WS2300
 * and writes the data to a MySQL database.
 *
 * The open2300.conf config file must contain the following parameters
 * 
 * Table structure for table `weather`
 * 
   CREATE TABLE `weather` (
     `timestamp` bigint(14) NOT NULL default '0',
     `rec_date` date NOT NULL default '0000-00-00',
     `rec_time` time NOT NULL default '00:00:00',
     `temp_in` decimal(2,1) NOT NULL default '0.0',
     `temp_out` decimal(2,1) NOT NULL default '0.0',
     `dewpoint` decimal(2,1) NOT NULL default '0.0',
     `rel_hum_in` tinyint(3) NOT NULL default '0',
     `rel_hum_out` tinyint(3) NOT NULL default '0',
     `windspeed` decimal(3,1) NOT NULL default '0.0',
     `wind_angle` decimal(3,1) NOT NULL default '0.0',
     `wind_direction` char(3) NOT NULL default '',
     `wind_chill` decimal(2,1) NOT NULL default '0.0',
     `rain_1h` decimal(3,1) NOT NULL default '0.0',
     `rain_24h` decimal(3,1) NOT NULL default '0.0',
     `rain_total` decimal(4,1) NOT NULL default '0.0',
     `rel_pressure` decimal(4,1) NOT NULL default '0.0',
     `tendency` varchar(7) NOT NULL default '',
     `forecast` varchar(6) NOT NULL default '',
     UNIQUE KEY `timestamp` (`timestamp`)
   ) TYPE=MyISAM;
 *
 * It takes one parameters. The config file name with path
 * If this parameter is omitted the program will look at the default paths
 * See the open2300.conf-dist file for info
 *
 ***********************************************************************/
int main(int argc, char *argv[])
{
	WEATHERSTATION ws2300;
	MYSQL mysql;
	unsigned char logline[3000] = "";
	char datestring[50];       //used to hold the date stamp for the log file
	const char *directions[]= {"N","NNE","NE","ENE","E","ESE","SE","SSE",
	                           "S","SSW","SW","WSW","W","WNW","NW","NNW"};
	double winddir[6];
	int tempint;
	char tendency[15];
	char forecast[15];
	struct config_type config;
	time_t basictime;
	char query[4096];

	get_configuration(&config, argv[1]);

	ws2300 = open_weatherstation(config.serial_device_name);


	/* READ TEMPERATURE INDOOR */

	sprintf(logline,"%s\'%.1f\',", logline,
	        temperature_indoor(ws2300, config.temperature_conv) );
	

	/* READ TEMPERATURE OUTDOOR */

	sprintf(logline,"%s\'%.1f\',", logline,
	        temperature_outdoor(ws2300, config.temperature_conv) );
	

	/* READ DEWPOINT */

	sprintf(logline,"%s\'%.1f\',", logline,
	        dewpoint(ws2300, config.temperature_conv) );
	

	/* READ RELATIVE HUMIDITY INDOOR */

	sprintf(logline,"%s\'%d\',", logline, humidity_indoor(ws2300) );
	
	
	/* READ RELATIVE HUMIDITY OUTDOOR */

	sprintf(logline,"%s\'%d\',", logline, humidity_outdoor(ws2300) );


	/* READ WIND SPEED AND DIRECTION aND WINDCHILL */

	sprintf(logline,"%s\'%.1f\',", logline,
	        wind_all(ws2300, config.wind_speed_conv_factor,
	                 &tempint, winddir) );

	sprintf(logline,"%s\'%.1f\',\'%s\',", logline,
	        winddir[0], directions[tempint]);
	

	/* READ WINDCHILL */

	sprintf(logline,"%s\'%.1f\',", logline,
	        windchill(ws2300, config.temperature_conv) );

	
	/* READ RAIN 1H */

	sprintf(logline,"%s\'%.1f\',", logline,
	        rain_1h(ws2300, config.rain_conv_factor) );
	
	
	/* READ RAIN 24H */

	sprintf(logline,"%s\'%.1f\',", logline,
	        rain_24h(ws2300, config.rain_conv_factor) );

	
	/* READ RAIN TOTAL */

	sprintf(logline,"%s\'%.1f\',", logline,
	        rain_total(ws2300, config.rain_conv_factor) );

	
	/* READ RELATIVE PRESSURE */

	sprintf(logline,"%s\'%.1f\',", logline,	
	        rel_pressure(ws2300, config.pressure_conv_factor) );


	/* READ TENDENCY AND FORECAST */
	
	tendency_forecast(ws2300, tendency, forecast);
	sprintf(logline,"%s\'%s\',\'%s\'", logline, tendency, forecast);


	/* GET DATE AND TIME FOR LOG FILE, PLACE BEFORE ALL DATA IN LOG LINE */
	
	time(&basictime);
	strftime(datestring,sizeof(datestring),
	         "\'%Y%m%d%H%M%S\',\'%Y-%m-%d\',\'%H:%M:%S\'",
	         localtime(&basictime) );

	/* CLOSE THE WEATHER STATION TO ENABLE OTHER PROGRAMS TO ACCESS */
	close_weatherstation(ws2300);

	// printf("%s %s\n",datestring, logline);  //disabled to be used in cron job

	/* INIT MYSQL AND CONNECT */
	if(!mysql_init(&mysql))
	{
	fprintf(stderr, "Cannot initialize MySQL");
	exit(0);
	}

	if(!mysql_real_connect(&mysql, config.mysql_host, config.mysql_user,
	                       config.mysql_passwd, config.mysql_database,
	                       config.mysql_port, NULL, 0))
	{
		fprintf(stderr, "%d: %s \n",
		mysql_errno(&mysql), mysql_error(&mysql));
		exit(0);
	}

	sprintf(query, "INSERT INTO weather VALUES (%s, %s)", datestring, logline);

	if(mysql_query(&mysql, query))
	{
		fprintf(stderr, "Could not insert row. %s %d: \%s \n", query, mysql_errno(&mysql), mysql_error(&mysql));
		mysql_close(&mysql);
		exit(0);
	}

	mysql_close(&mysql);

	return(0);
}
