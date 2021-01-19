#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 18 13:14:11 2021

@author: elias
"""

import pandas as pd
import datetime
import numpy as np

#%%Calcul frequence
def frequency_std_database(data: pd.core.frame.DataFrame):
    """Lors du calcul de le frequence:
        - Difference entre deux lignes successives
        - Moyenne de l'écart de type datetime.timedelta : W jours, X heures, Y minutes et 
            Z secondes
    """    
    
    data = data.diff()
    data = data.iloc[1:]
    
    mean_data = data.mean()
    std_data = data.std()
    
    return mean_data, std_data

#%%Recuperation des données en fonction de certaines conditions 
def is_open_hours(data: pd.core.frame.DataFrame, hours_open: datetime.datetime, hours_close: datetime.datetime, colonne_date:str):
    #import datetime
    
    assert type(hours_open) == datetime.datetime
    assert type(hours_close) == datetime.datetime
    assert hours_open < hours_close
    
    hours_index = list()
    
    for index in range(len(data)):
        if hours_close.time() >= data[colonne_date][index].time() >= hours_open.time():      
            hours_index.append(index)
    
    data_hours = data.loc[hours_index,:]
    data_hours = data_hours.reset_index(drop=True)
    
    return data_hours

def is_closed_hours(data: pd.core.frame.DataFrame, hours_open: datetime.datetime, hours_close: datetime.datetime, colonne_date:str):
    #import datetime
    
    assert hours_open <= hours_close

    hours_index = list()
    
    for index in range(len(data)):
        if hours_close.time() < data[colonne_date][index].time() or data[colonne_date][index].time() < hours_open.time():      
            hours_index.append(index)
    
    data_hours = data.loc[hours_index,:]
    data_hours = data_hours.reset_index(drop=True)
    
    return data_hours

def is_open_day(data: pd.core.frame.DataFrame, day_closed: list, day_off: list, holiday_start:list, holiday_end:list, colonne_date:str):    
    #import datetime
    
    assert len(holiday_start) == len(holiday_end), "Every Holiday has a day of start and end"
    
    day_index = list()
    day_in_holidays = False
    
    for index in range(len(data)):
        """Check holiday"""
        day_in_holidays = False
        
        if len(holiday_start) > 0:
            
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
    
    data_days = data.drop(day_index)
    data_days = data_days.reset_index(drop=True)
    
    return data_days

def closed(data: pd.core.frame.DataFrame, opens_date_hours: list, colonne_date:str):
    index = list()
    pre_ouverture = list()
    
    if len(opens_date_hours) == 0:
        return None
    
    open_date = np.unique([date.date() for date in opens_date_hours])

    for i in range(len(data)):
        if data[colonne_date][i].date() in open_date:
            if not data[colonne_date][i] in opens_date_hours:
                pre_ouverture.append(i)
                
        elif not data[colonne_date][i] in opens_date_hours:
            index.append(i)
            
    data_pre_open = data.loc[pre_ouverture,:]
    data_pre_open = data_pre_open.reset_index(drop=True)
    
    data_closed = data.loc[index,:]
    data_closed = data_closed.reset_index(drop=True)
    
    return data_pre_open, data_closed


def segmentation_semaine(data: pd.core.frame.DataFrame, open_hours: datetime.datetime, close_hours: datetime.datetime, colonne_date: str):
    segm_week = np.unique([date.date() for date in data[colonne_date]])
    
    segm_horaire = {date: {'open': [], 'close': []} for date in segm_week}
    segm_week = {date: [] for date in segm_week}    
    
    for index in range(len(data)):
        key = data[colonne_date][index].date()
        if key in segm_week.keys():
            segm_week[key].append(data.loc[index])
      
    if open_hours and close_hours is not None:
        for key in segm_week.keys():
            for index in range(len(segm_week[key])):
                if segm_week[key][index][colonne_date].time() > close_hours.time():
                    segm_horaire[key]['close'].append(segm_week[key][index])
                    
                elif segm_week[key][index][colonne_date].time() < open_hours.time():
                    segm_horaire[key]['open'].append(segm_week[key][index])
        
        return segm_horaire
                    
    return segm_week

#%% Permet de mettre en place une moving average
    
def moving_average(data: pd.core.frame.DataFrame, period: int):
    assert period > 0, "Pour la moving average, vous devez choisir une période surpérieur à 0"
    
    moving_ave = list()
    
    if data.ndim > 1:
        rooms = data.columns.tolist()
        
        for name in rooms:
            moving_ave.append(pd.Series(data[name]).rolling(window=period).mean().iloc[period-1:].values)
    
    elif data.ndim == 1:
        moving_ave.append(pd.Series(data).rolling(window=period).mean().iloc[period-1:].values)
        
    return np.array(moving_ave).T

#%% Analyse

def analyse_temperature_point(data: pd.core.frame.DataFrame, confort_temp: dict, gap: dict, function, Temp_Ext_Name: str, Date_Colonne: str):
    column_display = list(data.columns)
    
    if Temp_Ext_Name in column_display: column_display.remove(Temp_Ext_Name)
    if Date_Colonne in column_display: column_display.remove(Date_Colonne)
    
    #On crée un dict de dict
    tache = {name : [] for name in column_display}
    
    a = 0
    
    for name in column_display:
        a = 0
        for index in range(len(data)):
            conseil = function(data[Temp_Ext_Name][index], data[name][index], confort_temp[name], gap[name])
            if conseil is not None:
                tache[name].append([data[Date_Colonne][index], conseil])
            else:
                a += 1
    
        #print(name, a)
            
    return tache

def conseil_open(data_ext: float, data_room: float, data_confort: float, data_gap: float):
    borne_inf = data_confort * (1-data_gap)
    borne_sup = data_confort * (1+data_gap)
    
    
    if data_ext < borne_inf and data_room < borne_inf:
        return "Need to warm the place"
            
    elif (data_room < borne_inf <= data_ext ):
        return "Reduire Clim"
    
    elif (data_room > borne_inf and data_room <= borne_sup):
        return None
    
    elif data_room > borne_sup and data_ext <= borne_inf:
        return "Reduire chauffage"
    
    elif data_room > borne_sup and borne_inf < data_ext:
        return "Reduire chauffage ou clim"
        #vérifier circuit de chauffe si actif
    
    
    return None

def conseil_closed(data_ext: float, data_room: float, data_confort: float, data_gap: float):
    borne_inf = data_confort * (1-data_gap)
    borne_sup = data_confort * (1+data_gap)
    
    
    if data_room < borne_inf and data_ext < borne_inf:
        if data_room > data_ext:
            return None
        else:
            return None
    
    elif data_room > borne_sup and data_ext < borne_inf:
        return "Chauffage trop fort"
        
    elif data_room >= borne_inf and data_ext < borne_inf:
        return "Chauffage allumé alors que le batiment est fermé"
    
    
    if data_room < borne_inf and borne_inf <= data_ext < borne_sup:
        return None
    
    elif data_room > borne_sup and borne_inf <= data_ext < borne_sup:
        return "Chauffage encore allumé"
        
    elif data_room >= borne_inf and borne_inf <= data_ext < borne_sup:
        if data_room > data_ext:
            return None
        else:
            return None
        
    
    if data_room < borne_inf and data_ext >= borne_sup:
        return "Climatisation encore allumé"
    
    elif data_room > borne_sup and data_ext >= borne_sup:
        if data_room > data_ext:
            return "Chauffage allumé"
        else:
            return None
        
    elif data_room >= borne_inf and data_ext >= borne_sup:
        return "Climatisation allumé"
    
    
    return None

def formatage_conseil(data: dict, data_freq: datetime.datetime, data_std: datetime.datetime):
    """ data doit être strcuturé comme ci dessous
    nom_piece : [[date1, conseil1], [date2, conseil1], [date3, conseil2] ... ]
    """
    
    names = list(data.keys())
    
    analyse = {name:[] for name in names}
    
    for name in names:
        index = 1
        
        analyse[name].append([data[name][index][0], "", data[name][index][1]])
        
        while index < len(data[name]):
            if data[name][index][0] > data[name][index-1][0] + (data_freq - data_std) and \
                data[name][index][0] < data[name][index-1][0] + (data_freq + data_std):
                    
                if not data[name][index][1] == data[name][index-1][1]:
                    analyse[name][-1][1] = data[name][index-1][0]
                    analyse[name].append([data[name][index][0], "", data[name][index][1]])
            else:
                analyse[name][-1][1] = data[name][index-1][0]
                analyse[name].append([data[name][index][0], "", data[name][index][1]])
                
                if name == "Salle A.2.1":
                        print(data[name][index][0], data[name][index-1][0])
                
            index += 1
            
        analyse[name][-1][1] = data[name][index-1][0]
        
        
    """
    Format du tableau de sortie
    piece : date début du conseil - date de fin du conseil - conseil
    
    """        
    return analyse
