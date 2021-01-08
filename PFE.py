#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  5 12:49:40 2021

@author: elias
"""

import pandas as pd
import datetime
import matplotlib.pyplot as plt

colonne_date = "Date (Europe/Paris)"

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
    
#%%   
df.plot.line(x = colonne_date, y = name_capteur)

#%%
import numpy as np

def is_open_hours(data, hours_open, hours_close):
    hours_index = list()
    
    for index in range(len(data)):
        if data[colonne_date][index].time() >= hours_open.time() \
                    and data[colonne_date][index].time() <= hours_close.time():
                        
            hours_index.append(index)
    
    data_hours = data.loc[hours_index,:]
    data_hours = data_hours.reset_index(drop=True)
    
    return data_hours

data_open_hours = is_open_hours(df, horaire_ouverture, horaire_fermeture)

def is_open_day(data, day_closed, day_off, holiday_start, holiday_end):
    day_index = list()
    day_in_holidays = False
    
    assert len(holiday_start) == len(holiday_end), "Every Holiday has a day of start and end"
    
    for index in range(len(data)):
        """Check holiday"""
        if len(holiday_start) > 0:
            day_in_holidays = False
            
            for h_day in range(len(holiday_start)):
                if data[colonne_date][index].date() >= holiday_start[h_day].date() \
                            and data[colonne_date][index].date() <= holiday_end[h_day].date():
                    
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

def temp_hours(data, comfort_temp):
    nb_high_temp = {name:0 for name in temp_room}
    
    gap_mean = 0.12
    
    for index in range(len(data)):
        for column in nb_high_temp:
            if data[column][index] > (comfort_temp-comfort_temp * gap_mean) and \
                data[column][index] < (comfort_temp+comfort_temp * gap_mean):
                    if data['T°C ext'][index] <= (comfort_temp+comfort_temp * gap_mean):
                        nb_high_temp[column] += 1

    print(nb_high_temp)
    
temp_hours(data_open_hours, 32)

#%%
data_open_hours.plot.line(x = colonne_date, y = 'Réfectoire primaire')
plt.plot(data_open_hours[colonne_date], [[22,23] for _ in range(len(data_open_hours))])

#%%

horaire_ouverture = datetime.datetime.strptime("07:00:00", '%H:%M:%S')
horaire_fermeture = datetime.datetime.strptime("19:00:00", '%H:%M:%S')

vacance_debut = datetime.date.strptime("21/12/2019", '%d/%m/%Y')
vacance_fin = datetime.datetime.strptime("05/01/2020", '%d/%m/%Y')

#For the days open
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
days_open = [True, False, True, True, False, True, False]

days_open = np.array(days)[np.array(days_open)].tolist()
############

semaine_preced = vacance_debut + datetime.timedelta(days= -7)


""" Pour les données avant les vacances """
is_open = df['Date (Europe/Paris)']>= semaine_preced 
is_close = df['Date (Europe/Paris)']<= vacance_debut

week_before_open = is_open == is_close

data_norm = df[week_before_open]


for name in name_capteur:
    data_norm[name] = data_norm[name] - data_norm['T°C ext']

moyenne_before = np.mean(data_norm[name_capteur])


""" Pour les données pendant les vacances """
is_open = df['Date (Europe/Paris)']>= vacance_debut 
is_close = df['Date (Europe/Paris)']<= vacance_fin

week_before_open = is_open == is_close

data_norm = df[week_before_open]

column_display = ['Réfectoire primaire', 'Salle B.1.3', 'Salle B.2.2', 'Salle A.2.1', 'Salle A.1.1', 'Salle des maitres', 'Salle Maternelle 2 RDC', 'Salle Maternelle 3 1° étage', 'Salle motricité 1° étage']
data_norm.plot.line(x = "Date (Europe/Paris)", y = column_display)

for name in name_capteur:
    data_norm[name] = data_norm[name] - data_norm['T°C ext']

moyenne_holiday = np.mean(data_norm[name_capteur])

#
#arrayA = [ .1, .2, .4 ]
#arrayB = [ .3, .1, .3 ]
#
#np.corrcoef( arrayA, arrayB )[0,1] #see Homework bellow why we are using just one cell
#
#def my_corrcoef( x, y ):    
#    mean_x = np.mean( x )
#    mean_y = np.mean( y )
#    std_x  = np.std ( x )
#    std_y  = np.std ( y )
#    n      = len    ( x )
#    return np.correlate( x - mean_x, y - mean_y, mode = 'valid' )[0] / n / ( std_x * std_y )
#
#my_corrcoef( arrayA, arrayB )


