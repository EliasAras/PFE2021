#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  5 12:49:40 2021

@author: elias
"""

import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt

from functions import *

DATE_COLONNE = "Date (Europe/Paris)"
TEMP_EXT = "T°C ext"

#%% Formatage
# Read CSV file into DataFrame df
df = pd.read_csv('/Users/elias/Desktop/PFE/GitHub/PFE2021/LCSC-03_12_2020 08_00_00.csv', delimiter=";")

# Show dataframe
name_capteur = df.columns.values.tolist()
del name_capteur[0], name_capteur[0]

for index in range(len(df)): 
    df[DATE_COLONNE][index] = datetime.datetime.strptime(df[DATE_COLONNE][index], '%d/%m/%Y %H:%M:%S')
    
    for name in name_capteur:
        #remove ,
        value = df[name][index].replace(',' , '.') 
        df[name][index] = float(value)

del index, name, value, name_capteur

#%%

frequence, standard_deviation = frequency_std_database(df[DATE_COLONNE])
standard_deviation = datetime.timedelta(days=8)
#%%   
#df.plot.line(x = DATE_COLONNE, y = name_capteur)

#%%Personnalisation des datas

horaire_ouverture = datetime.datetime.strptime("07:00:00", '%H:%M:%S')
horaire_fermeture = datetime.datetime.strptime("19:00:00", '%H:%M:%S')

vacance_debut = datetime.datetime.strptime("21/12/2019", '%d/%m/%Y')
vacance_fin = datetime.datetime.strptime("05/01/2020", '%d/%m/%Y')

#For the days open
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
days_open = [True, True, True, True, True, False, False]
days_closed = ~np.array(days_open)

days_open = np.array(days)[np.array(days_open)].tolist()
days_closed = np.array(days)[np.array(days_closed)].tolist()

data_open_hours = is_open_day(df, days_closed, [], [], [], DATE_COLONNE)
data_open_hours = is_open_hours(data_open_hours, horaire_ouverture, horaire_fermeture, DATE_COLONNE)

#separer les données avant ouverture du batiment et fermeture totale du batiment (vacances)
data_closed_hours, data_closed_days = closed(df, data_open_hours[DATE_COLONNE].tolist(), DATE_COLONNE)
data_per_week_per_hours = segmentation_semaine(data_closed_hours, horaire_ouverture, horaire_fermeture, DATE_COLONNE)

del days, days_open, days_closed
#%%
temp_room = ['Réfectoire primaire',
             'Salle B.1.3',
             'Salle B.2.2',
             'Salle A.2.1',
             'Salle A.1.1',
             'Salle des maitres',
             'Salle Maternelle 2 RDC',
             'Salle Maternelle 3 1° étage',
             'Salle motricité 1° étage']

"""
Il faudra detecter le type de chaque colonne
"""

#%% Moving average 
    
#use n previous periods to calculate moving average 
n=7*24

moving_average_room = moving_average(data_open_hours[temp_room], n)
moving_average_exterieur = moving_average(data_open_hours[TEMP_EXT], n)
moving_average_time = data_open_hours[DATE_COLONNE][(n-1):]

#On analyse les movings average
moving_average_time = moving_average_time.values
#Reshape pour avoir un tableau en 2D (nb_data, 1)
moving_average_time = np.reshape(moving_average_time, (moving_average_time.shape[0], 1))
moving_average_analyse = np.concatenate((moving_average_time, moving_average_room, moving_average_exterieur), axis=1)

moving_average_analyse = pd.DataFrame(data = moving_average_analyse,  
                                      index = [i for i in range(len(moving_average_analyse))],  
                                      columns = [DATE_COLONNE] + temp_room + [TEMP_EXT])

del moving_average_time, moving_average_room, moving_average_exterieur
#%% Analyse des donées avec consels
"""Ouverture"""

#Provisoire
temp_confort = {name:20 for name in df.columns}
gap_to_confort = {name:0.05 for name in df.columns}

#analyse_data_by_point = analyse_temperature_point(moving_average_analyse, temp_confort, gap_to_confort)
analyse_data_by_point_open = analyse_temperature_point(data_open_hours[[DATE_COLONNE] + temp_room+ [TEMP_EXT]], temp_confort, gap_to_confort, conseil_open, TEMP_EXT, DATE_COLONNE)
analyse_data_by_point_holidays = analyse_temperature_point(data_closed_hours[[DATE_COLONNE] + temp_room+ [TEMP_EXT]], temp_confort, gap_to_confort, conseil_closed, TEMP_EXT, DATE_COLONNE)

analyse_data_open = formatage_conseil(analyse_data_by_point_open, frequence, standard_deviation)
analyse_data_holidyas = formatage_conseil(analyse_data_by_point_holidays, frequence, standard_deviation)


#%%

#%%
        
name = "Salle A.2.1"
display(data_open_hours, analyse_data_open, analyse_data_by_point_open, name, temp_confort[name], gap_to_confort[name], DATE_COLONNE)
display(data_closed_days, analyse_data_holidyas, analyse_data_by_point_holidays, name, temp_confort[name], gap_to_confort[name], DATE_COLONNE)
