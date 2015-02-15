#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------
# Créé par letchap modifié par lahorde pour avoir :
# - les données d'une PWS (personal weather station) 
# depuis weather underground
# - les données de l'habitation (température intérieure
# humidité... depuis emoncms
# wu_pws_polling.py
#----------------------------------------------------
""" récupère les informations météo grace à l'API du site wunderground.com """ 

#import pour les infos meteo
import os.path
import os
import urllib2
import json
import sys, traceback
# import pour le démon
import time
from daemon import runner
# import pour l'éphemeride
import ephem

try:
    API_KEY = os.environ["WU_KEY"]
    PWS_ID = os.environ["WU_PWS_ID"]
    # emplacement du fichier où sont écrites les informations extraites depuis weather underground
    POLLED_DATA_PATH = "/tmp/wu_polling.data"
    #station vent
    VENT_1_URL_SUFFIX = os.environ["VENT_1_URL_SUFFIX"]
    VENT_2_URL_SUFFIX = os.environ["VENT_2_URL_SUFFIX"]
    #data emoncms
    EMONCMS_KEY = os.environ["EMONCMS_KEY"]
    EMONCMS_HUMIDITY_FIELD=os.environ["EMONCMS_HUMIDITY_FIELD"]
    EMONCMS_TEMP_FIELD=os.environ["EMONCMS_TEMP_FIELD"]
except KeyError as e:
    print "Avant de lancer le script - renseigner la configuration dans ../pws_params.sh - parametre manquant : %s" %e
    sys.exit(2)

#=========================================================== 
#       La classe
#===========================================================        

class App(): 
    # Tout ça, c'est pour le démon
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null' # J'ai remplacé /dev/tty par dev/null pour éviter les plantages au démarrage par init.d
        self.stderr_path = '/dev/null' # J'ai remplacé /dev/tty par dev/null pour éviter les plantages au démarrage par init.d
        self.pidfile_path = '/tmp/meteo.pid'
        self.pidfile_timeout = 5  
    
    # Bien appelé la fonction 'run' pour le démon
    def run(self):    
        # champ non dispo
        NA_FIELD = "--"
     
        while True: # C'est le début de ma boucle pour démoniser mon programme
        
            ###############################################
            #           Le corps du programme             #
            ###############################################
            try:
            # Je récupère les informations fournies par wunderground grâce à leur api, au format json,
            # en une seule fois (forecast et conditions), et en français
            # Un exemple de code est fourni sur le site wunderground
        
                # Je charge ma page des observations pws
                page_json_pws = urllib2.urlopen('http://api.wunderground.com/api/' + API_KEY + '/conditions/lang:FR/q/pws:' + PWS_ID + '.json')
                # Je lis la page
                json_string = page_json_pws.read()
                # Je mets cette page dans un parseur
                parsed_json_pws = json.loads(json_string)
                # Et je peux fermer ma page meteo, je n'en ai plus besoin
                page_json_pws.close()
		
                pws_city = parsed_json_pws['current_observation']['display_location']['city'] # la ville où se situe la pws
		
                # Je charge ma page des prévisions pws
                page_json_forecast = urllib2.urlopen('http://api.wunderground.com/api/' + API_KEY + '/forecast/conditions/lang:FR/q/France/' + pws_city + '.json')
                # Je lis la page
                json_string = page_json_forecast.read()
                # Je mets cette page dans un parseur
                parsed_json_forecast = json.loads(json_string)
                # Et je peux fermer ma page meteo, je n'en ai plus besoin
                page_json_forecast.close()
                
                page_json_wind_1 = urllib2.urlopen('http://api.wunderground.com/api/' + API_KEY + VENT_1_URL_SUFFIX)
                # Je lis la page
                json_string = page_json_wind_1.read()
                # Je mets cette page dans un parseur
                parsed_json_wind_1 = json.loads(json_string)
                # Et je peux fermer ma page meteo, je n'en ai plus besoin
                page_json_wind_1.close()
                
                page_json_wind_2 = urllib2.urlopen('http://api.wunderground.com/api/' + API_KEY + VENT_2_URL_SUFFIX)
                # Je lis la page
                json_string = page_json_wind_2.read()
                # Je mets cette page dans un parseur
                parsed_json_wind_2 = json.loads(json_string)
                # Et je peux fermer ma page meteo, je n'en ai plus besoin
                page_json_wind_2.close() 
            
            except Exception as e: 
                print "Les informations meto ne sont pas accessibles sur le site wunderground.com - %s" % e
                sys.exit(2) # pour sortir du programme si la requête n'aboutit pas

            try:
				# Je récupère les informations du jour stokées sur le tag "current_observation"
				# Je fais attention à avoir des variables uniques dans le cas où je fais une recherche sur une chaîne de
				# caractère plus tard (avec un grep par exemple).

				city = parsed_json_pws['current_observation']['display_location']['city'] # la ville
				latitude = parsed_json_pws['current_observation']['display_location']['latitude'] # latitude
				longitude = parsed_json_pws['current_observation']['display_location']['longitude'] # longitude
				elevation = parsed_json_pws['current_observation']['display_location']['elevation'] # altitude
				last_observation = parsed_json_pws['current_observation']['observation_time_rfc822'] # l'heure dernière observation
				current_temp = parsed_json_pws['current_observation']['temp_c'] # la température en °C
				current_weather = parsed_json_pws['current_observation']['weather'] # le temps actuel
				current_weather_icon = parsed_json_pws['current_observation']['icon'] # icone du temps actuel
				humidity = parsed_json_pws['current_observation']['relative_humidity'] # le taux d'humidité en %
				wind_kph = parsed_json_pws['current_observation']['wind_kph'] # la vitesse du vent
				wind_dir = parsed_json_pws['current_observation']['wind_dir'] # l'orientation du vent
				pressure_mb = parsed_json_pws['current_observation']['pressure_mb'] # la pression atmosphérique
				pressure_trend = parsed_json_pws['current_observation']['pressure_trend'] # l'evolution pression atmosphérique
				feelslike_c = parsed_json_pws['current_observation']['feelslike_c'] # la température ressentie
				visibility = parsed_json_pws['current_observation']['visibility_km'] # la visibilité en km
				precip_last_hr = parsed_json_pws['current_observation']['precip_1hr_in'] # cumul précipitations sur la dernière heure
				precip_day = parsed_json_pws['current_observation']['precip_today_in'] # cumul précipitations sur 24h
				UV = parsed_json_pws['current_observation']['UV'] # l'indice UV
            except Exception as e:
                print "Impossible de parser les observations de la pws - %s" % e
                sys.exit(2) 

            wind_1_last_obs, wind_kph_1, wind_dir_1, wind_2_last_obs, wind_kph_2, wind_dir_2 = NA_FIELD, NA_FIELD, NA_FIELD, NA_FIELD, NA_FIELD, NA_FIELD
            
            #wind_1_last_obs = parsed_json_wind_1['current_observation']['observation_time_rfc822'] # l'heure dernière observation
            try:
				# vent
                wind_1_last_obs = parsed_json_wind_1['current_observation']['observation_time_rfc822'] # l'heure dernière observation
                wind_kph_1 = parsed_json_wind_1['current_observation']['wind_kph'] # la vitesse du vent
                wind_dir_1 = parsed_json_wind_1['current_observation']['wind_dir'] # l'orientation du vent
                wind_2_last_obs = parsed_json_wind_2['current_observation']['observation_time_rfc822'] # l'heure dernière observation
                wind_kph_2 = parsed_json_wind_2['current_observation']['wind_kph'] # la vitesse du vent
                wind_dir_2 = parsed_json_wind_2['current_observation']['wind_dir'] # l'orientation du vent
            except KeyError as e:  
                print "Erreur sur les observations de vent - pas de clé pour %s" % e
            
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
                f.write("Meteo = " + current_weather.encode('utf8') + "\n")
                f.write("Icone_temps = " + current_weather_icon + "\n")
                f.write("Ville = " + city.encode('utf8') + "\n")
                f.write("Derniere_observation = " + last_observation.encode('utf8') + "\n")
                f.write("Temperature = " + str(current_temp) + " °C\n")
                f.write("Ressentie = " + str(feelslike_c) + " °C\n")
                f.write("Humidite = " + humidity + "\n")
                f.write("Precip_1h = " + str(precip_last_hr) + "\n")
                f.write("Precip_1j = " + str(precip_day) + "\n")
                f.write("Vent = " + str(wind_kph) + " km/h\n")
                f.write("Dir_vent = " + wind_dir + "\n")
                f.write("Vent_1_Derniere_observation = " + wind_1_last_obs.encode('utf8') + "\n")
                f.write("Vent_1 = " + str(wind_kph_1) + " km/h\n")
                f.write("Dir_vent_1 = " + str(wind_dir_1) + "\n")
                f.write("Vent_2_Derniere_observation = " + wind_2_last_obs.encode('utf8') + "\n")
                f.write("Vent_2 = " + str(wind_kph_2) + " km/h\n")
                f.write("Dir_vent_2 = " + str(wind_dir_2) + "\n")
                f.write("Pression = " + str(pressure_mb) + " mb\n")
                f.write("Tend_pres = " + pressure_trend.encode('utf8') + "\n") #Ok, l'utf8 ne sert à rien là
                f.write("Visibilite = " + str(visibility) + " km\n")
                f.write("Indice_UV = " + str(UV) + "\n")
                f.write("Maison_salon_temp = " + App.emoncmsFeedval(EMONCMS_TEMP_FIELD) + "\n")
                f.write("Maison_salon_hum = " + App.emoncmsFeedval(EMONCMS_HUMIDITY_FIELD) + "\n")             
            
            #prendre icone avec lune ou soleil selon ephemeride
            user = ephem.Observer()
            user.lat = latitude
            user.lon = longitude
            user.elevation = float(elevation)
            next_sunrise_datetime = user.next_rising(ephem.Sun()).datetime()
            next_sunset_datetime = user.next_setting(ephem.Sun()).datetime()
	
            icone_suffix = ""
    
            #le jour est levé, la date du prochain coucher de soleil est plus proche que celle du prochain lever
            if next_sunset_datetime > next_sunrise_datetime:
                icone_suffix += "_night"
            
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
                
                # Encore un petit test pour les icones. Je combine icon et skyicon pour avoir la représentation graphique 
                # la plus proche de la réalité en particulier "partiellement couvert et pluvieux" qui n'existe pas
                # D'abord je définis 3 listes pour l'orage, la pluie et la neige
                orage = ['tstorms','chancetstorms','nt_tstorms', 'nt_chancetstorms']
                pluie = ['rain','chancerain','nt_rain', 'nt_chancerain', ]
                neige = ['snow','flurries','chancesnow','chanceflurries','nt_snow','nt_flurries','nt_chancesnow','nt_chanceflurries','sleet', 'nt_sleet','chancesleet','nt_chancesleet']
                # puis je définis mes icones
                if icon in orage:
                    icone = skyicon+"storm"
                elif icon in pluie:
                    icone = skyicon+"rain"
                elif icon in neige:
                    icone = skyicon+"snow"
                else:
                    icone = icon
                    
                # Ajout suffixe pour icone de nuit
                icone += icone_suffix
                
                # J'écris à la suite, grâce à l'option 'a' append au lieu de 'w'
                with open(POLLED_DATA_PATH, 'a') as f:
                            f.write(date + "_jour = "  + str(jour) + "\n")
                            f.write(date + "_mois = "  + str(mois) + "\n") 
                            f.write(date + "_annee = "  + str(annee) + "\n")     
                            f.write(date + "_jour_sem = "  + jour_sem.encode('utf8') + "\n")  # C'est du luxe, il n'y a pas d'accent dans les jours de la semaine
                            f.write(date + "_tempmax = "  + str(tempmax) + " °C\n")     
                            f.write(date + "_tempmin = "  + str(tempmin) + " °C\n")                              
                            f.write(date + "_conditions = " + condition.encode('utf8') + "\n")
                            f.write(date + "_icone = " + icone + "\n")
                            f.write(date + "_pop = "  + str(pop) + "%\n")            
                            f.write(date + "_hauteur_precip = "  + str(hauteur_precip) + " mm\n")            
                            f.write(date + "_hauteur_neige = "  + str(hauteur_neige) + " cm\n")            
                            f.write(date + "_vent = "  + str(vent) + " km/h\n")            
                            f.write(date + "_dir_vent = "  + vent_dir + "\n")             
                            f.write(date + "_tx_himidite = "  + str(tx_humidite) + "%\n")          
            ############################################
            #             Le fin du programme          #
            ############################################  
            time.sleep(600) # C'est la fin de ma boucle de démonisation. La temporisation est de 120 secondes  
        
    @staticmethod
    def emoncmsFeedval(feedid):
        data_url="http://emoncms.org/feed/value.json?apikey=" + EMONCMS_KEY + "&id=" + str(feedid)
        # read in the data from emoncms
        try:
                sock = urllib2.urlopen(data_url)
                data_str = sock.read()
                sock.close
                return data_str[1:-1]
        except Exception, detail:
                print "Error ", detail  
                return NA_FIELD

# Toujours commencer la lecture d'un programme python par la fin. C'est là qu'on lance le démon
app = App()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()
#app.run()