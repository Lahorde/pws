/*  open2300 - fetch2300.c
 *  
 *  Version 1.10
 *  
 *  Control WS2300 weather station
 *  
 *  Copyright 2003-2005, Kenneth Lavrsen
 *  This program is published under the GNU General Public license
 */

#include "rw2300.h"

 
/********** MAIN PROGRAM ************************************************
 *
 * This program reads all current and min/max data from a WS2300
 * weather station and write it to standard out. This is the program that
 * the program weatherstation.php uses to display a nice webpage with
 * current weather data.
 *
 * It takes one parameter which is the config file name with path
 * If this parameter is omitted the program will look at the default paths
 * See the open2300.conf-dist file for info
 *
 ***********************************************************************/
int main(int argc, char *argv[])
{
	WEATHERSTATION ws2300;
	unsigned char logline[3000] = "";
	char datestring[50];     //used to hold the date stamp for the log file
	const char *directions[]= {"N","NNE","NE","ENE","E","ESE","SE","SSE",
	                           "S","SSW","SW","WSW","W","WNW","NW","NNW"};
	double winddir[6];
	char tendency[15];
	char forecast[15];
	struct config_type config;
	double tempfloat_min, tempfloat_max;
	int tempint, tempint_min, tempint_max;
	struct timestamp time_min, time_max;
	time_t basictime;

	get_configuration(&config, argv[1]);

	ws2300 = open_weatherstation(config.serial_device_name);


	/* READ TEMPERATURE INDOOR */
	
	sprintf(logline, "%sTi %.1f\n", logline,
	        temperature_indoor(ws2300, config.temperature_conv) );

	temperature_indoor_minmax(ws2300, config.temperature_conv, &tempfloat_min,
	                          &tempfloat_max, &time_min, &time_max);
	
	sprintf(logline, "%sTimin %.1f\n", logline, tempfloat_min);
	sprintf(logline, "%sTimax %.1f\n", logline, tempfloat_max);
	sprintf(logline,"%sTTimin %02d:%02d\nDTimin %04d-%02d-%02d\n", logline,
	        time_min.hour, time_min.minute, time_min.year,
	        time_min.month, time_min.day);
	sprintf(logline,"%sTTimax %02d:%02d\nDTimax %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);
	
	
	/* READ TEMPERATURE OUTDOOR */

	sprintf(logline, "%sTo %.1f\n", logline,
	        temperature_outdoor(ws2300, config.temperature_conv) );

	temperature_outdoor_minmax(ws2300, config.temperature_conv, &tempfloat_min,
	                           &tempfloat_max, &time_min, &time_max);
	
	sprintf(logline, "%sTomin %.1f\n", logline, tempfloat_min);
	sprintf(logline, "%sTomax %.1f\n", logline, tempfloat_max);
	sprintf(logline,"%sTTomin %02d:%02d\nDTomin %04d-%02d-%02d\n", logline,
	        time_min.hour, time_min.minute, time_min.year,
	        time_min.month, time_min.day);
	sprintf(logline,"%sTTomax %02d:%02d\nDTomax %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);

	
	/* READ DEWPOINT */

	sprintf(logline, "%sDP %.1f\n", logline,
	        dewpoint(ws2300, config.temperature_conv) );

	dewpoint_minmax(ws2300, config.temperature_conv, &tempfloat_min,
	                &tempfloat_max, &time_min, &time_max);
	
	sprintf(logline, "%sDPmin %.1f\n", logline, tempfloat_min);
	sprintf(logline, "%sDPmax %.1f\n", logline, tempfloat_max);
	sprintf(logline,"%sTDPmin %02d:%02d\nDDPmin %04d-%02d-%02d\n", logline,
	        time_min.hour, time_min.minute, time_min.year,
	        time_min.month, time_min.day);
	sprintf(logline,"%sTDPmax %02d:%02d\nDDPmax %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);
	
	
	/* READ RELATIVE HUMIDITY INDOOR */

	sprintf(logline, "%sRHi %d\n", logline,
		humidity_indoor_all(ws2300, &tempint_min, &tempint_max,
		                    &time_min, &time_max) );
	
	sprintf(logline, "%sRHimin %d\n", logline, tempint_min);
	sprintf(logline, "%sRHimax %d\n", logline, tempint_max);
	sprintf(logline,"%sTRHimin %02d:%02d\nDRHimin %04d-%02d-%02d\n", logline,
	        time_min.hour, time_min.minute, time_min.year,
	        time_min.month, time_min.day);
	sprintf(logline,"%sTRHimax %02d:%02d\nDRHimax %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);
	
	
	/* READ RELATIVE HUMIDITY OUTDOOR */

	sprintf(logline, "%sRHo %d\n", logline,
		    humidity_outdoor_all(ws2300, &tempint_min, &tempint_max,
		                         &time_min, &time_max) );
	
	sprintf(logline, "%sRHomin %d\n", logline, tempint_min);
	sprintf(logline, "%sRHomax %d\n", logline, tempint_max);
	sprintf(logline,"%sTRHomin %02d:%02d\nDRHomin %04d-%02d-%02d\n", logline,
	        time_min.hour, time_min.minute, time_min.year,
	        time_min.month, time_min.day);
	sprintf(logline,"%sTRHomax %02d:%02d\nDRHomax %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);


	/* READ WIND SPEED AND DIRECTION */
	
	sprintf(logline,"%sWS %.1f\n", logline,
	       wind_all(ws2300, config.wind_speed_conv_factor, &tempint, winddir));
	sprintf(logline,"%sDIRtext %s\nDIR0 %.1f\nDIR1 %0.1f\n"
	        "DIR2 %0.1f\nDIR3 %0.1f\nDIR4 %0.1f\nDIR5 %0.1f\n",
			logline, directions[tempint], winddir[0], winddir[1],
			winddir[2], winddir[3], winddir[4], winddir[5]);
			
			
	/* WINDCHILL */
	
	sprintf(logline, "%sWC %.1f\n", logline,
	        windchill(ws2300, config.temperature_conv) );
	
	windchill_minmax(ws2300, config.temperature_conv, &tempfloat_min,
	                 &tempfloat_max, &time_min, &time_max); 

	sprintf(logline, "%sWCmin %.1f\n", logline, tempfloat_min);
	sprintf(logline, "%sWCmax %.1f\n", logline, tempfloat_max);

	sprintf(logline,"%sTWCmin %02d:%02d\nDWCmin %04d-%02d-%02d\n", logline,
	        time_min.hour, time_min.minute, time_min.year,
	        time_min.month, time_min.day);
	sprintf(logline,"%sTWCmax %02d:%02d\nDWCmax %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);
	        

	/* READ WINDSPEED MIN/MAX */

	wind_minmax(ws2300, config.wind_speed_conv_factor, &tempfloat_min,
	            &tempfloat_max, &time_min, &time_max);

	sprintf(logline, "%sWSmin %.1f\n", logline, tempfloat_min);
	sprintf(logline, "%sWSmax %.1f\n", logline, tempfloat_max);

	sprintf(logline,"%sTWSmin %02d:%02d\nDWSmin %04d-%02d-%02d\n", logline,
	        time_min.hour, time_min.minute, time_min.year,
	        time_min.month, time_min.day);
	sprintf(logline,"%sTWSmax %02d:%02d\nDWSmax %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);

	
	/* READ RAIN 1H */

	sprintf(logline,"%sR1h %.2f\n", logline,
	        rain_1h_all(ws2300, config.rain_conv_factor,
	                    &tempfloat_max, &time_max));
	sprintf(logline,"%sR1hmax %.2f\n", logline, tempfloat_max);
	sprintf(logline,"%sTR1hmax %02d:%02d\nDR1hmax %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);


	/* READ RAIN 24H */

	sprintf(logline,"%sR24h %.2f\n", logline,
	        rain_24h_all(ws2300, config.rain_conv_factor,
	                     &tempfloat_max, &time_max));
	sprintf(logline,"%sR24hmax %.2f\n", logline, tempfloat_max);
	sprintf(logline,"%sTR24hmax %02d:%02d\nDR24hmax %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);

	
	/* READ RAIN TOTAL */
	
	sprintf(logline,"%sRtot %.2f\n", logline,
	        rain_total_all(ws2300, config.rain_conv_factor, &time_max));
	sprintf(logline,"%sTRtot %02d:%02d\nDRtot %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);


	/* READ RELATIVE PRESSURE */

	sprintf(logline,"%sRP %.3f\n", logline,
	        rel_pressure(ws2300, config.pressure_conv_factor) );

	
	/* RELATIVE PRESSURE MIN/MAX */

	rel_pressure_minmax(ws2300, config.pressure_conv_factor, &tempfloat_min,
	                    &tempfloat_max, &time_min, &time_max);

	sprintf(logline, "%sRPmin %.3f\n", logline, tempfloat_min);
	sprintf(logline, "%sRPmax %.3f\n", logline, tempfloat_max);

	sprintf(logline,"%sTRPmin %02d:%02d\nDRPmin %04d-%02d-%02d\n", logline,
	        time_min.hour, time_min.minute, time_min.year,
	        time_min.month, time_min.day);
	sprintf(logline,"%sTRPmax %02d:%02d\nDRPmax %04d-%02d-%02d\n", logline,
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);


	/* READ TENDENCY AND FORECAST */
	
	tendency_forecast(ws2300, tendency, forecast);
	sprintf(logline, "%sTendency %s\nForecast %s\n", logline, tendency, forecast);


	/* GET DATE AND TIME FOR LOG FILE, PLACE BEFORE ALL DATA IN LOG LINE */
	
	time(&basictime);
	strftime(datestring,sizeof(datestring),"Date %Y-%b-%d\nTime %H:%M:%S\n",
	         localtime(&basictime));

	// Print out and leave

	printf("%s%s",datestring, logline);

	close_weatherstation(ws2300);

	return(0);
}

