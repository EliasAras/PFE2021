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

colonne_date = "Date (Europe/Paris)"
Temp_ext = "T°C ext"

#%% Formatage
# Read CSV file into DataFrame df
df = pd.read_csv('/Users/elias/Desktop/PFE/GitHub/PFE2021/LCSC-03_12_2020 08_00_00.csv', delimiter=";")

# Show dataframe
name_capteur = df.columns.values.tolist()
del name_capteur[0], name_capteur[0]

for index in range(len(df)): 
    df["Date (Europe/Paris)"][index] = datetime.datetime.strptime(df["Date (Europe/Paris)"][index], '%d/%m/%Y %H:%M:%S')
    
    for name in name_capteur:
        #remove ,
        value = df[name][index].replace(',' , '.') 
        df[name][index] = float(value)

#%%Calcul frequence
def frequency_std_database(data):
    """Lors du calcul de le frequence:
        - Difference entre deux lignes successives
        - Moyenne de l'écart de type datetime.timedelta : W jours, X heures, Y minutes et 
            Z secondes
    """    
    
    data = data[colonne_date].diff()
    data = data.iloc[1:]
    
    mean_data = data.mean()
    std_data = data.std()
    return mean_data, std_data
    
frequence, standard_deviation = frequency_std_database(df)
#%%   
df.plot.line(x = colonne_date, y = name_capteur)

#%%

horaire_ouverture = datetime.datetime.strptime("07:00:00", '%H:%M:%S')
horaire_fermeture = datetime.datetime.strptime("19:00:00", '%H:%M:%S')

vacance_debut = datetime.datetime.strptime("21/12/2019", '%d/%m/%Y')
vacance_fin = datetime.datetime.strptime("05/01/2020", '%d/%m/%Y')

#For the days open
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
days_open = [False, False, False, False, False, True, True]

days_open = np.array(days)[np.array(days_open)].tolist()
#########

#%%

def is_open_hours(data: pd.core.frame.DataFrame, hours_open: datetime.datetime, hours_close: datetime.datetime):
    hours_index = list()
    
    for index in range(len(data)):
        if hours_close.time() >= data[colonne_date][index].time() >= hours_open.time():      
            hours_index.append(index)
    
    data_hours = data.loc[hours_index,:]
    data_hours = data_hours.reset_index(drop=True)
    
    return data_hours

def is_open_day(data: pd.core.frame.DataFrame, day_closed: list, day_off: list, holiday_start:list, holiday_end:list):
    day_index = list()
    day_in_holidays = False
    
    assert len(holiday_start) == len(holiday_end), "Every Holiday has a day of start and end"
    
    for index in range(len(data)):
        """Check holiday"""
        if len(holiday_start) > 0:
            day_in_holidays = False
            
            for h_day in range(len(holiday_start)):
                if holiday_end[h_day].date() >= data[colonne_date][index].date() >= holiday_start[h_day].date():
                    day_index.append(index)
                    day_in_holidays = True
                    break
                
        #We already find a day close we dont need to check to following condition
        if day_in_holidays:
            continue
          
        if len(day_off) > 0:
            if data[colonne_date][index].date() in day_off:
                day_index.append(index)
                continue
        
        if len(day_closed) > 0:           
            if data[colonne_date][index].strftime("%A") in day_closed:
                day_index.append(index)
                continue
    
    data_days = data.loc[day_index,:]
    data_days = data_days.reset_index(drop=True)
    
    return data_days

data_open_hours = is_open_day(df, days_open, [], [], [])

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

#%% centrer par rapport à T°C ext

data_norm = data_open_hours.copy()
confort_temp = 20
    
#use n previous periods to calculate moving average 
n=7*24

moving_average_room = list()

#calculate moving average
for name in temp_room:
    moving_average_room.append(pd.Series(data_norm[name]).rolling(window=n).mean().iloc[n-1:].values)

moving_average_room = np.array(moving_average_room).T

moving_average_exterieur = pd.Series(data_norm[Temp_ext]).rolling(window=n).mean().iloc[n-1:].values
#Pour créer un tableau de dim (nb_data, 1)
moving_average_exterieur = np.reshape(moving_average_exterieur, (moving_average_exterieur.shape[0], 1))

moving_average_time = data_norm[colonne_date][(n-1):]

#data_norm.plot.line(x = colonne_date, y = 'Réfectoire primaire')
#plt.plot(data_norm[colonne_date], data_norm[Temp_ext])

#plt.plot(moving_average_time, moving_average_room[:,1])
#plt.plot(moving_average_time, moving_average_exterieur)
#plt.plot(data_norm[colonne_date], [[confort_temp-1, confort_temp+1] for _ in range(len(data_norm))])
#plt.legend(
# ['Room', 'Ext'],
# loc='upper left'
# )
#
#plt.show()

def analyse_temperature_point(data: pd.core.frame.DataFrame, confort_temp: dict, gap: dict):
    column_display = list(data.columns)
    
    if Temp_ext in column_display: column_display.remove(Temp_ext)
    if colonne_date in column_display: column_display.remove(colonne_date)
    
    #On crée un dict de dict
    tache = {name : [] for name in column_display}
    
    for name in column_display:
        for index in range(len(data)):
            conseil = position(data[Temp_ext][index], data[Temp_ext][index], confort_temp[name], gap[name])
            if conseil is not None:
                tache[name].append([data[colonne_date][index], conseil])
            
    return tache
    
def position(data_ext: float, data_room: float, data_confort: float, data_gap: float):
    borne_inf = data_confort * (1-data_gap)
    brone_sup = data_confort * (1+data_gap)
    
    
    if (data_ext and data_room) < borne_inf:
        return "Need to warm the place"
            
    elif (data_room < borne_inf <= data_ext ):
        return "Reduire Clim"
    
    elif (data_room > borne_inf and data_room <= brone_sup):
        return None
    
    elif data_room > brone_sup and data_ext <= borne_inf:
        return "Reduire chauffage 1"
    
    elif data_room > brone_sup and borne_inf < data_ext:
        return "Reduire chauffage 2"
    
    
    return None

def formatage_conseil(data: dict):
    """ data doit être strcuturé comme ci dessous
    nom_piece : [[date1, conseil1], [date2, conseil1], [date3, conseil2] ... ]
    """
    
    names = list(data.keys())
    
    analyse = {name:[] for name in names}
    
    for name in names:
        index = 1
        analyse[name].append([data[name][index][0], "", data[name][index][1]])
        
        while index < len(data[name]):
            # if x in range(y,z) <=> (y <= x < z)
            if data[name][index][0] > data[name][index-1][0] + (frequence -standard_deviation) and \
                data[name][index][0] < data[name][index-1][0] + (frequence + standard_deviation):
                if not data[name][index][1] == data[name][index-1][1]:
                    analyse[name][-1][1] = data[name][index-1][0]
                    analyse[name].append([data[name][index][0], "", data[name][index][1]])
            else:
                analyse[name][-1][1] = data[name][index-1][0]
                analyse[name].append([data[name][index][0], "", data[name][index][1]])
            
            index += 1
            
        analyse[name][-1][1] = data[name][index-1][0]
    """
    Format du tableau de sortie
    piece : date début du conseil - date de fin du conseil - conseil
    
    """        
    return analyse
    
#On analyse les movings average
moving_average_time = moving_average_time.values
#Reshape pour avoir un tableau en 2D (nb_data, 1)
moving_average_time = np.reshape(moving_average_time, (moving_average_time.shape[0], 1))

moving_average_analyse = np.concatenate((moving_average_time, moving_average_room, moving_average_exterieur), axis=1)

moving_average_analyse = pd.DataFrame(data = moving_average_analyse,  
                                      index = [i for i in range(len(moving_average_analyse))],  
                                      columns = [colonne_date] + temp_room + [Temp_ext])

#Provisoire
temp_confort = {name:16 for name in df.columns}
gap_to_confort = {name:0.1 for name in df.columns}

analyse_data_by_point = analyse_temperature_point(moving_average_analyse, temp_confort, gap_to_confort)
analyse_data_sasasasa = formatage_conseil(analyse_data_by_point)

#if room in I1 and temp_ext in I1:
#    chauffe
#    
#if room in I1 and temp_ext in (I2 or I3):
#    chaleur exterieur ne rentre pas la piece, CAVE ? reduire clim
#
#if room in I2 and temp_ext in (I1 or I2 or I3):
#    garde la meme conso
#    
#if room in I3 and temp_ext in I1:
#    surconso
#    
#if room in I3 and temp_ext in I2 or I3:
#    baisser conso ou clim
