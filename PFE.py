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
standard_deviation = datetime.timedelta(days=4)
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

data_norm = data_open_hours.copy()
    
#use n previous periods to calculate moving average 
n=7*24

moving_average_room = moving_average(data_norm[temp_room], n)
moving_average_exterieur = moving_average(data_norm[TEMP_EXT], n)
moving_average_time = data_norm[DATE_COLONNE][(n-1):]

#%% Analyse des donées avec consels
"""Ouverture"""
    
#On analyse les movings average
moving_average_time = moving_average_time.values
#Reshape pour avoir un tableau en 2D (nb_data, 1)
moving_average_time = np.reshape(moving_average_time, (moving_average_time.shape[0], 1))
moving_average_analyse = np.concatenate((moving_average_time, moving_average_room, moving_average_exterieur), axis=1)

moving_average_analyse = pd.DataFrame(data = moving_average_analyse,  
                                      index = [i for i in range(len(moving_average_analyse))],  
                                      columns = [DATE_COLONNE] + temp_room + [TEMP_EXT])

#Provisoire
temp_confort = {name:20 for name in df.columns}
gap_to_confort = {name:0.05 for name in df.columns}

#analyse_data_by_point = analyse_temperature_point(moving_average_analyse, temp_confort, gap_to_confort)
analyse_data_by_point_open = analyse_temperature_point(data_norm[[DATE_COLONNE] + temp_room+ [TEMP_EXT]], temp_confort, gap_to_confort, conseil_open, TEMP_EXT, DATE_COLONNE)
analyse_data_by_point_holidays = analyse_temperature_point(data_closed_hours[[DATE_COLONNE] + temp_room+ [TEMP_EXT]], temp_confort, gap_to_confort, conseil_closed, TEMP_EXT, DATE_COLONNE)

analyse_data_open = formatage_conseil(analyse_data_by_point_open, frequence, standard_deviation)
analyse_data_holidyas = formatage_conseil(analyse_data_by_point_holidays, frequence, standard_deviation)


del moving_average_time, moving_average_room, moving_average_exterieur
#%%
"""Closed""" 

def analyse_pre_post_open(data: dict):
    conseil = dict
    keys_ = list(data.keys())
    
    if type(data[list(data.keys())[0]]) is dict:
        
        for key in keys_:
            data_sorted = sorted(data[key]['open'])
            if data[key]['open'][-1]:
                pass
        
    else:
        pass
            

#%%

def is_error_occurs(data: pd.core.frame.DataFrame, hours_begin: datetime.datetime, hours_end: datetime.datetime):
    hours_index = list()
    
    for index in range(len(data)):
        if hours_end >= data[DATE_COLONNE][index] >= hours_begin :      
            hours_index.append(index)
    
    
    data_hours = data.loc[hours_index,:]
    data_hours = data_hours.reset_index(drop=True)
    
    return data_hours

def ratio_error_between_date(name: str, conseil: str, date_start: datetime.datetime, date_end: datetime.datetime):
    nb = 0
    total = 0
    
    data = data_norm.copy()
    
    for index in range(len(data)):
        if date_end >= data[DATE_COLONNE][index] >= date_start: 
            total += 1
            
    del data
    
    data = analyse_data_by_point_open.copy()
    
    for index in range(len(data[name])):
        
        if date_end >= data[name][index][0] >= date_start:
            if conseil == data[name][index][1]:
                nb += 1
     
    if total == 0:
        return 0
    
    return nb/total


def display(data, name_room:str, confort_temp:float, gap_confort:float, colonne_date:str):
    erreur_list=list(data.get(name_room))
    
    indice = 11
    data_error_occurs = is_error_occurs(data_open_hours, erreur_list[indice][0], erreur_list[indice][1])

    fig, ax = plt.subplots(figsize=(8,6))

    plt.plot(data_error_occurs[colonne_date], data_error_occurs[name_room])
    
    value_conf_inf = [confort_temp*(1-gap_confort) for _ in range(len(data_error_occurs[colonne_date]))]
    value_conf_sup = [confort_temp*(1+gap_confort) for _ in range(len(data_error_occurs[colonne_date]))]
    
    plt.plot(data_error_occurs[colonne_date], np.array([value_conf_inf, value_conf_sup]).T)
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Temperature')
    ax.set_title('')
    plt.legend(['T°C ' + name_room, 'T°C confort inferieur', 'T°C confort superieur'],loc='lower right')
    
    plt.grid()
    plt.show()
    
    ratio = ratio_error_between_date(name_room, erreur_list[indice][2], erreur_list[indice][0], erreur_list[indice][1])
    
    print("Debut - Fin :", erreur_list[indice][0], "-", erreur_list[indice][1])
    print("Pourcentage d\'incident sur cette période {0:.1%}".format(ratio))
    print("Conseil : ", erreur_list[indice][2])
    
    
    
    
name = "Salle A.2.1"
display(analyse_data_open, name, temp_confort[name], gap_to_confort[name], DATE_COLONNE)
display(analyse_data_holidyas, name, temp_confort[name], gap_to_confort[name], DATE_COLONNE)
