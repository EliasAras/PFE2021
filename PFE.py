#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  5 12:49:40 2021

@author: elias
"""

import pandas as pd
import datetime
import matplotib.pyplot.plot

#%% Formatage
# Read CSV file into DataFrame df
df = pd.read_csv('LCSC-03_12_2020 08_00_00.csv', delimiter=";")

# Show dataframe
name_capteur = df.columns.values.tolist()
del name_capteur[0], name_capteur[0]

for index in range(len(df["Date (Europe/Paris)"])): 
    df["Date (Europe/Paris)"][index] = datetime.datetime.strptime(df["Date (Europe/Paris)"][index], '%d/%m/%Y %H:%M:%S')
    
    for name in name_capteur:
        #remove ,
        value = df[name][index].replace(',' , '.') 
        df[name][index] = float(value)
    
#%%   
df.plot.line(x = "Date (Europe/Paris)", y = name_capteur)

#%%
import numpy as np

horaire_ouverture = "07:00:00"
horaire_fermeture = "19:00:00"

vacance_debut = datetime.datetime.strptime("21/12/2019", '%d/%m/%Y')
vacance_fin = datetime.datetime.strptime("05/01/2020", '%d/%m/%Y')

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


