#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------
# Créé par letchap modifié par lahorde pour avoir :
# - les données d'une PWS (personal weather station) 
# depuis weather underground
# - les données de l'habitation (température intérieure
# humidité... depuis influxdb
# - les données de pollution pour votre ville
# wu_pws_polling.py
#----------------------------------------------------
""" récupère les informations météo grace à l'API du site wunderground.com """ 

#import pour les infos meteo
import os.path
import os
import urllib
import urllib.request
import codecs
import json
import csv
import datetime
import dateutil.parser
import sys, traceback
# import pour le démon
import time
import daemon
import lockfile.pidlockfile 
from dateutil.parser import parse
from dateutil import tz
import logging
from influxdb import client as influxdb

NA_FIELD = "--"

try:
    API_KEY = os.environ["WU_KEY"]
    LOGGER_FILE = os.environ["PWS_LOG_PATH"]
    PWS_ID = os.environ["WU_PWS_ID"]
    # emplacement du fichier où sont écrites les informations extraites depuis weather underground
    POLLED_DATA_PATH = os.environ["PWS_POLLING_DATA_PATH"]
    #station vent
    VENT_1_URL_SUFFIX = os.environ["VENT_1_URL_SUFFIX"]
    VENT_PIOU_PIOU_URL_PREFIX = os.environ["VENT_PIOU_PIOU_URL_PREFIX"]
    VENT_1_PIOU_PIOU_URL_SUFFIX = os.environ["VENT_1_PIOU_PIOU_URL_SUFFIX"]
    #data influxdb
    INFLUX_DB_HOST_URL = os.environ["INFLUX_DB_HOST_URL"]
    INFLUX_DB_HOST_PORT = os.environ["INFLUX_DB_HOST_PORT"]
    INFLUX_DB_USER = os.environ["INFLUX_DB_USER"]
    INFLUX_DB_PASS = os.environ["INFLUX_DB_PASS"]
    INFLUXDB_SERIES_SUFFIX = os.environ["INFLUXDB_SERIES_SUFFIX"]
    INFLUXDB_NAME = os.environ["INFLUXDB_NAME"]
    INFLUX_HOME_TEMP_FIELD = os.environ["INFLUXDB_HOME_TEMP_FIELD"]
    INFLUXDB_HOME_HUMIDITY_FIELD = os.environ["INFLUXDB_HOME_HUMIDITY_FIELD"]
    #data pollution
    POLLUTION_STATION_ID = os.environ["POLLUTION_STATION_ID"]
    
except KeyError as e:
    print("Avant de lancer le script - renseigner la configuration dans ../pws_params.sh - parametre manquant : %s" %e)
    sys.exit(2)


#=========================================================== 
#       La classe
#===========================================================        

class LastObservations(): 
    def __init__(self):
        self.db = influxdb.InfluxDBClient(INFLUX_DB_HOST_URL, INFLUX_DB_HOST_PORT, INFLUX_DB_USER, INFLUX_DB_PASS)
    
    def getJSON(self, url):
        try:
            resp = urllib.request.urlopen(url)
            resp_data = resp.read()
            parsed_json = json.loads(resp_data.decode())
            resp.close()
            return parsed_json

        except Exception as e :
            logger.error( "Unable to get parsed json data from %s - %s", url, e )
            sys.exit(2)

    def run(self):
        logger.info("starting wu_pws_polling loop")
        
        while True: # C'est le début de ma boucle pour démoniser mon programme
            logger.info( "Polling weather data...")
        
            ###############################################
            #           Le corps du programme             #
            ###############################################
            # Je récupère les informations fournies par wunderground grâce à leur api, au format json,
            # en une seule fois (forecast et conditions), et en français
            # Un exemple de code est fourni sur le site wunderground
            parsed_json_pws, parsed_json_forecast, parsed_json_wind_1, parsed_json_wind_2 = None, None, None, None
            
            parsed_json_pws = self.getJSON('http://api.wunderground.com/api/' + API_KEY + '/conditions/lang:FR/q/pws:' + PWS_ID + '.json')
            try:
                pws_city = parsed_json_pws['current_observation']['display_location']['city'] # la ville où se situe la pws
                
            except KeyError as e: 
                logger.error( "Unable to parse PWS city from JSON content - %s",  e )
                sys.exit(2) 
            
            parsed_json_forecast = self.getJSON('http://api.wunderground.com/api/' + API_KEY + '/forecast/conditions/lang:FR/q/France/' + pws_city + '.json')
            # WIND    
            page_json_wind_1 = self.getJSON('http://api.wunderground.com/api/' + API_KEY + VENT_1_URL_SUFFIX)
            page_json_wind_2 = self.getJSON(VENT_PIOU_PIOU_URL_PREFIX + VENT_1_PIOU_PIOU_URL_SUFFIX)

            try:
                # Je récupère les informations du jour stokées sur le tag "current_observation"
                # Je fais attention à avoir des variables uniques dans le cas où je fais une recherche sur une chaîne de
                # caractère plus tard (avec un grep par exemple).

                city = parsed_json_pws['current_observation']['display_location']['city'] # la ville
                latitude = parsed_json_pws['current_observation']['display_location']['latitude'] # latitude
                longitude = parsed_json_pws['current_observation']['display_location']['longitude'] # longitude
                elevation = parsed_json_pws['current_observation']['display_location']['elevation'] # altitude
                last_observation = parsed_json_pws['current_observation']['observation_time_rfc822'] # l'heure dernière observation
                last_observation = parse(last_observation)
                last_observation = last_observation.strftime('%d/%m/%Y-%H:%M')
                current_temp = parsed_json_pws['current_observation']['temp_c'] # la température en °C
                current_weather = parsed_json_pws['current_observation']['weather'] # le temps actuel
                #Indication nuit non fournie dans champ "icone". En revanche dans "icon_url" on a cette indication
                # ex : "icon_url":"http://icons.wxug.com/i/c/k/cloudy.gif"
                # c'est le préfixe "nt_" qui indique le type d'icone à prendre (nuit ou jour)
                # Dans les infos de la pws pas de champ supplémentaire "skyicon" pour fournir des infos supplémentaires 
                # afin de choisir une icone plus précise pour le temps actuel - par contre ce champ skyicon est présent pour le forecast
                icon_url_parsed = parsed_json_pws['current_observation']['icon_url'].split('/')
                current_weather_icon = icon_url_parsed[len(icon_url_parsed) - 1].split('.')[0]
                humidity = parsed_json_pws['current_observation']['relative_humidity'] # le taux d'humidité en %
                wind_kph = parsed_json_pws['current_observation']['wind_kph'] # la vitesse du vent
                wind_dir = parsed_json_pws['current_observation']['wind_dir'] # l'orientation du vent
                pressure_mb = parsed_json_pws['current_observation']['pressure_mb'] # la pression atmosphérique
                pressure_trend = parsed_json_pws['current_observation']['pressure_trend'] # l'evolution pression atmosphérique
                feelslike_c = parsed_json_pws['current_observation']['feelslike_c'] # la température ressentie
                visibility = parsed_json_pws['current_observation']['visibility_km'] # la visibilité en km
                precip_last_hr = parsed_json_pws['current_observation']['precip_1hr_metric'] # cumul précipitations sur la dernière heure
                precip_day = parsed_json_pws['current_observation']['precip_today_metric'] # cumul précipitations sur 24h
                UV = parsed_json_pws['current_observation']['UV'] # l'indice UV
                
            except Exception as e:
                logger.error( "Impossible de parser les observations de la pws %s", e)
                sys.exit(2) 

				# vent
            wind_1_last_obs, wind_kph_1, wind_dir_1, wind_2_last_obs, wind_kph_2, wind_dir_2 = NA_FIELD, NA_FIELD, NA_FIELD, NA_FIELD, NA_FIELD, NA_FIELD            
            try:
                if parsed_json_wind_1 != None :
                  wind_1_last_obs = parsed_json_wind_1['current_observation']['observation_time_rfc822'] # l'heure dernière observation
                  wind_1_last_obs = parse(wind_1_last_obs)
                  wind_1_last_obs = wind_1_last_obs.strftime('%d/%m/%Y-%H:%M')
                  wind_kph_1 = parsed_json_wind_1['current_observation']['wind_kph'] # la vitesse du vent
                  wind_dir_1 = parsed_json_wind_1['current_observation']['wind_dir'] # l'orientation du vent

            except KeyError as e:  
                logger.error( "Erreur sur les observations de vent - pas de clé pour %s", e )
            
            try:
                if parsed_json_wind_2 != None :
                  #piou piou
                  wind_2_last_obs = parsed_json_wind_2['data']['measurements']['date'] # l'heure dernière observation
                  wind_2_last_obs = parse(wind_2_last_obs)
                  wind_2_last_obs = wind_2_last_obs.strftime('%d/%m/%Y-%H:%M')
                  wind_kph_2 = parsed_json_wind_2['data']['measurements']['wind_speed_avg'] # la vitesse du vent
                  wind_dir_2 = parsed_json_wind_2['data']['measurements']['wind_heading']# l'orientation du vent
              
            except Exception as e:
                logger.error( "Impossible de parser les observations de pioupiou", e)
            
            # Un petit test sur l'indice UV qui peut être négatif
            if str(UV) == '-1':
                UV = 0
            
            # Une petite transformation de la tendance atmosphérique
            
            if pressure_trend == '-':
                pressure_trend = 'en baisse'
            elif pressure_trend == '+':
                pressure_trend = 'en hausse'
            else:
                pressure_trend = 'stable'
            
            # J'écris ces informations dans un fichier qui servira plus tard pour le conky meteo.
            # En ouvrant le fichier en mode 'w', j'écrase le fichier meteo.txt précédent 
            # Je transforme tous les chiffres en chaînes de caractères et j'encode tous les textes français en UTF8    
            # Je n'ai pas besoin de fermer le fichier en utilisant "with open"

            with open(POLLED_DATA_PATH, 'w') as f: 
                f.write("Meteo = " + current_weather + "\n")
                f.write("Icone_temps = " + current_weather_icon + "\n")
                f.write("Ville = " + city + "\n")
                f.write("Derniere_observation = " + last_observation + "\n")
                f.write("Temperature = " + str(current_temp) + " °C\n")
                f.write("Ressentie = " + str(feelslike_c) + " °C\n")
                f.write("Humidite = " + humidity + "\n")
                f.write("Precip_1h = " + str(precip_last_hr) + "\n")
                f.write("Precip_1j = " + str(precip_day) + "\n")
                f.write("Vent = " + str(wind_kph) + " km/h\n")
                f.write("Dir_vent = " + wind_dir + "\n")
                f.write("Vent_1_Derniere_observation = " + wind_1_last_obs + "\n")
                f.write("Vent_1 = " + str(wind_kph_1) + " km/h\n")
                f.write("Dir_vent_1 = " + str(wind_dir_1) + "\n")
                f.write("Vent_2_Derniere_observation = " + wind_2_last_obs + "\n")
                f.write("Vent_2 = " + str(wind_kph_2) + " km/h\n")
                f.write("Dir_vent_2 = " + str(wind_dir_2) + "\n")
                f.write("Pression = " + str(pressure_mb) + " mb\n")
                f.write("Tend_pres = " + pressure_trend + "\n") 
                f.write("Visibilite = " + str(visibility) + " km\n")
                f.write("Indice_UV = " + str(UV) + "\n")
                f.write("Maison_salon_temp = " + self.influxDbGetLastPoint(INFLUX_HOME_TEMP_FIELD) + "\n")
                f.write("Maison_salon_hum = " + self.influxDbGetLastPoint(INFLUXDB_HOME_HUMIDITY_FIELD) + "\n")             
                
                #Add pollution data
                poll_data = LastObservations.getRAPollutionData(POLLUTION_STATION_ID)
                dioxyde_azote="NA"
                monoxyde_azote = "NA"
                ozone = "NA"
                pm_10 = "NA"
                poll_station="NA"
                poll_timestamp="NA"
                if len(poll_data) != 0 :
                    try :
                        dioxyde_azote = poll_data['Dioxyde d\'azote'][0]
                        monoxyde_azote = poll_data['Monoxyde d\'azote'][0]
                        ozone = poll_data['Ozone'][0]
                        pm_10 = poll_data['Particules PM10'][0]
                        poll_station = poll_data['Station']
                        poll_timestamp=poll_data['Timestamp']
                    except Exception as e:
                        logger.error("Some pollution fields are missing - %s", e)
                    
                f.write('Poll_station = ' + poll_station + '\n') 
                f.write('Poll_timestamp = ' + poll_timestamp + '\n')
                f.write('Dioxyde_azote = ' + dioxyde_azote + '\n') 
                f.write('Monoxyde_azote = ' + monoxyde_azote + '\n') 
                f.write('Ozone = ' + ozone + '\n') 
                f.write('PM10 = ' + pm_10 + '\n') 
            
            # Je récupère les prévisions sous le tag "simpleforecast", en bouclant sur chacune des périodes
            forecast = parsed_json_forecast['forecast']['simpleforecast']['forecastday']
            for i in forecast:
                jour           = i['date']['day']        # jour
                mois           = i['date']['month']      # mois
                annee          = i['date']['year']       # année
                jour_sem       = i['date']['weekday']    # jour de la semaine
                period         = i['period']             # période
                tempmax        = i['high']['celsius']    # température maximale
                tempmin        = i['low']['celsius']     # température minimale
                condition      = i['conditions']         # conditions
                icon           = i['icon']               # icone en lien avec condition
                skyicon        = i['skyicon']            # le couverture nuagueuse
                pop            = i['pop']                # probabilité de précipitation
                hauteur_precip = i['qpf_allday']['mm']   # hauteur de précipitation pour la journée
                hauteur_neige  = i['snow_allday']['cm']  # hauteur de neige pour la journée
                vent           = i['avewind']['kph']     # vitesse moyenne du vent
                vent_dir       = i['avewind']['dir']     # direction du vent
                tx_humidite    = i['avehumidity']        # taux d'humidité

                # Je définis chacune de mes 4 périodes
                if period == 1:
                    date = 'jour1'
                elif period == 2:
                    date = 'jour2'
                elif period == 3:
                    date = 'jour3'
                elif period == 4:
                    date = 'jour4'
                
                icon = LastObservations.addWeatherIconSuffix(icon, skyicon)
                
                # J'écris à la suite, grâce à l'option 'a' append au lieu de 'w'
                with open(POLLED_DATA_PATH, 'a') as f:
                            f.write(date + "_jour = "  + str(jour) + "\n")
                            f.write(date + "_mois = "  + str(mois) + "\n") 
                            f.write(date + "_annee = "  + str(annee) + "\n")     
                            f.write(date + "_jour_sem = "  + jour_sem + "\n")
                            f.write(date + "_tempmax = "  + str(tempmax) + " °C\n")     
                            f.write(date + "_tempmin = "  + str(tempmin) + " °C\n")                              
                            f.write(date + "_conditions = " + condition + "\n")
                            f.write(date + "_icone = " + icon + "\n")
                            f.write(date + "_pop = "  + str(pop) + "%\n")            
                            f.write(date + "_hauteur_precip = "  + str(hauteur_precip) + " mm\n")            
                            f.write(date + "_hauteur_neige = "  + str(hauteur_neige) + " cm\n")            
                            f.write(date + "_vent = "  + str(vent) + " km/h\n")            
                            f.write(date + "_dir_vent = "  + vent_dir + "\n")             
                            f.write(date + "_tx_himidite = "  + str(tx_humidite) + "%\n")          
            ############################################
            #             Le fin du programme          #
            ############################################  
            #SUR WU 10 call/minute ou 500 call /jour max lorsque l'utilisateur a une clé développeur
            time.sleep(600) # C'est la fin de ma boucle de démonisation. La temporisation est de 120 secondes  
        
    def influxDbGetLastPoint(self, valueId):
        # read in the data from influxdb
        try:
            # check db exists 
            all_dbs_list = self.db.get_list_database()

            if INFLUXDB_NAME not in [str(x['name']) for x in all_dbs_list]:
                logger.error("{0} not in dd list".format(INFLUXDB_NAME))
                return NA_FIELD
            else :   
                self.db.switch_database(INFLUXDB_NAME)

            val = self.db.query('select * from ' + valueId + INFLUXDB_SERIES_SUFFIX + ' where time>now() - 10m order by time desc limit 1')
            utcDate = parse(list(val.get_points())[0]['time'])            
            
            #convert UTC date to local date 
            from_zone = tz.tzutc()
            to_zone = tz.tzlocal()
            localDate = utcDate.astimezone(to_zone)
            return str(round(list(val.get_points())[0]['value'], 2)) + " " + localDate.strftime('%d/%m/%Y-%H:%M')
        except Exception as detail:
            logger.error( 'Error when getting influxdb point field %s - %s', valueId, detail)
            return NA_FIELD
        
    @staticmethod   
    def getRAPollutionData(station_id):
        try :
            last_url = 'http://www.air-rhonealpes.fr/aasqa_air_station/download-data/' + station_id + '/periodicity/2'
            page_csv_poll = urllib.request.urlopen(last_url)
            # http://stackoverflow.com/questions/18897029/read-csv-file-from-url-into-python-3-x-csv-error-iterator-should-return-str
            # Do not use ftpstream.read().decode('utf-8')
            read_data = codecs.iterdecode(page_csv_poll, 'utf_8_sig')
        except Exception as e :
            logger.error('Cannot get RhoneAlpes pollution data for station %s - %s', station_id, e)
            return {}
        
        # Create a custom dialect
        # http://stackoverflow.com/questions/6879596/why-is-the-python-csv-reader-ignoring-double-quoted-fields
        csv.register_dialect(
            'air-rhonealpes_data',
            delimiter = ';',
            quotechar = '"',
            doublequote = True,
            skipinitialspace = True,
            lineterminator = '\r\n',
            quoting = csv.QUOTE_MINIMAL)    
    
        # Iterator returned by DictReader must be used several times.
        # It needs to be resetted, simple way is to make a list but
        # in this case whole CSV is loaded into memory
        cr = list(csv.DictReader(read_data, dialect='air-rhonealpes_data'))
        
        # Get last observation parsing all fields to date for a given row 
        last_meas = None
        first_row = cr[0]
        for field in first_row :
            try :
                dt = parse(field)
                if (last_meas is None) or (dt > parse(last_meas)) :
                    last_meas = field
            except :
                #field is not a date ignore it                
                continue
            
        #Reject last observation if too old    
        if(datetime.datetime.now() - parse(last_meas)).total_seconds() > 60*60  :
            logger.info("Pollution data is too old - date = %s", last_meas)
            return {} 
        ret = {}   
        value = None
        for row in cr :
            if (row[last_meas]) == "-" :
                value = "NA"
            else : 
                value = row[last_meas]
            ret[row['Polluant']]=(value, row['Unité'])  
        ret['Station'] = first_row['Station']
        ret['Timestamp'] = parse(last_meas).strftime('%H:%M') 
        return ret        

    @staticmethod
    def addWeatherIconSuffix(icon, skyicon):
        # Encore un petit test pour les icones. Je combine icon et skyicon pour avoir la représentation graphique 
        # la plus proche de la réalité en particulier "partiellement couvert et pluvieux" qui n'existe pas
        # D'abord je définis 3 listes pour l'orage, la pluie et la neige
        orage = ['tstorms','chancetstorms','nt_tstorms', 'nt_chancetstorms']
        pluie = ['rain','chancerain','nt_rain', 'nt_chancerain', ]
        neige = ['snow','flurries','chancesnow','chanceflurries','nt_snow','nt_flurries','nt_chancesnow','nt_chanceflurries','sleet', 'nt_sleet','chancesleet','nt_chancesleet']
        # puis je définis mes icones
        if icon in orage:
            icone = skyicon+icon
        elif icon in pluie:
            icone = skyicon+icon
        elif icon in neige:
            icone = skyicon+icon
        else:
            icone = icon
        return icone

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOGGER_FILE)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - ' + os.path.basename(__file__) + ' - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info("starting wu_pws_polling script")
    
    lastObs = LastObservations()
    pidfile = lockfile.pidlockfile.PIDLockFile("/tmp/pws.pid")
    with daemon.DaemonContext(stdout=sys.stdout, stderr=sys.stderr, files_preserve = [fh.stream], pidfile=pidfile):
        lastObs.run()
