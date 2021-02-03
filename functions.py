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

def analyse_temperature_point(full_data: pd.core.frame.DataFrame, data: pd.core.frame.DataFrame, column_display, confort_temp: dict, gap: dict, function, Temp_Ext_Name: str, Date_Colonne: str, association: dict):    
    #On crée un dict de dict
    tache = {name : [] for name in column_display}
    
    for name in column_display:
        for index in range(len(data)):
            anomalie = function(data[Temp_Ext_Name][index], data[name][index], confort_temp[name], gap[name], is_heater_on(full_data, association, data[Date_Colonne][index], name, Date_Colonne))
            if anomalie is not None:
                tache[name].append([data[Date_Colonne][index], anomalie])
            
    return tache

def is_heater_on(full_data: pd.core.frame.DataFrame, association: dict, date_observation: datetime.datetime, name:str, colonne_date: str):
    index = full_data[full_data[colonne_date] == date_observation].index.tolist()[0]
    
    if name in association.keys():
        relation_circuit = association[name]
          
        if index > 0:
            if full_data[relation_circuit][index-1:index].mean() > 30 :
                return True
            else:
                return False
        else:
            return full_data[relation_circuit][index] > 30
    else:
        return False
        
def anomalie_open(data_ext: float, data_room: float, data_confort: float, data_gap: float, heater: bool):
    borne_inf = data_confort * (1-data_gap)
    borne_sup = data_confort * (1+data_gap)
        
    if data_room < borne_inf and data_ext < borne_inf:
        if heater:
            return None
        else:
            return "Le batiment est ouvert, le chauffage est éteint alors que la température de la pièce est trop basse."
    
    elif data_room > borne_sup and data_ext < borne_inf:
        if heater:
            return "Le batiment est ouvert, le chauffage est allumé alors que la température de la pièce est trop haute."
        else:
            return None
        
    elif data_room >= borne_inf and data_ext < borne_inf:
        return None
    
    
    if data_room < borne_inf and borne_inf <= data_ext < borne_sup:
        if heater:
            return "Le batiment est ouvert, le chauffage est allumé et la température de la pièce est trop basse."
        else:
            return "Le batiment est ouvert, le chauffage est éteint alors que la température de la pièce est trop basse."
    
    elif data_room > borne_sup and borne_inf <= data_ext < borne_sup:
        if heater:
            return None
        else:
            return "Le batiment est ouvert, le chauffage est allumé alors que la température de la pièce est trop haute."
        
    elif data_room >= borne_inf and borne_inf <= data_ext < borne_sup:
        return None
        
    
    if data_room < borne_inf and data_ext >= borne_sup:
        return "Le batiment est ouvert, le chauffage est allumé et la température de la pièce est trop basse."
    
    elif data_room > borne_sup and data_ext >= borne_sup:
        if heater:    
            return "Le batiment est ouvert, le chauffage est allumé alors que la température de la pièce est trop haute."
        else:
            return None
        
    elif data_room >= borne_inf and data_ext >= borne_sup:
        return None
    
    
    return None

def anomalie_closed(data_ext: float, data_room: float, data_confort: float, data_gap: float, heater: bool):
    borne_inf = data_confort * (1-data_gap)
    borne_sup = data_confort * (1+data_gap)
    
    if heater:
        return "Le batiment est fermé et le chauffage est allumé"
    
    if data_room < borne_inf and data_ext < borne_inf:
        if data_room > data_ext:
            return None
        else:
            return None
    
    elif data_room > borne_sup and data_ext < borne_inf:
        return "Le batiment est fermé, le chauffage est éteint et la température de la salle est trop élevée par rapport à la température extérieur"
        
    elif data_room >= borne_inf and data_ext < borne_inf:
        return "Le batiment est fermé, le chauffage est éteint et la température de la salle est trop élevée par rapport à la température extérieur"
    
    
    if data_room < borne_inf and borne_inf <= data_ext < borne_sup:
        return None
    
    elif data_room > borne_sup and borne_inf <= data_ext < borne_sup:
        return "Le batiment est fermé, le chauffage est éteint et la température de la salle est trop élevée par rapport à la température extérieur"
        
    elif data_room >= borne_inf and borne_inf <= data_ext < borne_sup:
        if data_room > data_ext:
            return None
        else:
            return None
        
    
    if data_room < borne_inf and data_ext >= borne_sup:
        return None
    
    elif data_room > borne_sup and data_ext >= borne_sup:
        if data_room > data_ext:
            return None
        else:
            return None
        
    elif data_room >= borne_inf and data_ext >= borne_sup:
        return None
    
    
    return None

def formatage_probleme(data: dict, data_freq: datetime.datetime, data_std: datetime.datetime):
    """ data doit être strcuturé comme ci dessous
    nom_piece : [[date1, anomalie1], [date2, anomalie1], [date3, anomalie2] ... ]
    """
    
    names = list(data.keys())
    
    analyse = {name:[] for name in names}
    
    for name in names:
        index = 1
        
        if len(data[name]) > 0:
            analyse[name].append([data[name][0][0], "", data[name][0][1]])
            
            while index < len(data[name]):
                if data[name][index][0] > data[name][index-1][0] + (data_freq - data_std) and \
                    data[name][index][0] < data[name][index-1][0] + (data_freq + data_std):
                        
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
    piece : date début du probleme - date de fin du probleme - probleme
    
    """        
    return analyse

def index_to_display(full_data, start, end): 
    if not end - start > 4:
        if start == 0:
            end = 7

        elif start == 1:
            start = 0
            end += 3
   
        elif start ==  2:
            start = 0
            end += 3

        elif end == (len(full_data)-1):
            start -= 7

        elif end == (len(full_data)-2):
            end = (len(full_data)-1)
            start -= 3

        elif end == (len(full_data)-3):
            end = (len(full_data)-1)
            start -= 3

        else:
            start -= 3
            end += 3 
          
    return start, end
    
def remodelage_analyse(full_data: pd.core.frame.DataFrame, analyse_anomalie: dict, freq, colonne_date: str):
    freq_anomalie = {name: {} for name in analyse_anomalie.keys()}
    
    for name in analyse_anomalie.keys():
        if len(analyse_anomalie[name]) > 0:
            
            index_start = full_data.loc[full_data[colonne_date] == analyse_anomalie[name][0][0]].index[0]
            index_end = full_data.loc[full_data[colonne_date] == analyse_anomalie[name][0][1]].index[0]
                    
            index_start, index_end = index_to_display(full_data, index_start, index_end)
            
            freq_anomalie[name] = {analyse_anomalie[name][0][2] : [[full_data[colonne_date][index_start], full_data[colonne_date][index_end], analyse_anomalie[name][0][0], analyse_anomalie[name][0][1]]]}
            
            for index in range(1, len(analyse_anomalie[name])):
                
                name_anomalie = analyse_anomalie[name][index][2]
                index_start = full_data.loc[full_data[colonne_date] == analyse_anomalie[name][index][0]].index[0]
                index_end = full_data.loc[full_data[colonne_date] == analyse_anomalie[name][index][1]].index[0]
                    
      
                index_start, index_end = index_to_display(full_data, index_start, index_end)
                
                if name_anomalie in freq_anomalie[name].keys():
                    freq_anomalie[name][name_anomalie].append([full_data[colonne_date][index_start], full_data[colonne_date][index_end], analyse_anomalie[name][index][0], analyse_anomalie[name][index][1]])
                    
                else:
                    freq_anomalie[name][name_anomalie] = [[full_data[colonne_date][index_start], full_data[colonne_date][index_end], analyse_anomalie[name][index][0], analyse_anomalie[name][index][1]]]
    

    #convert in dataframe
    for name in freq_anomalie.keys():
        for anomalie in freq_anomalie[name].keys():
            freq_anomalie[name][anomalie] = pd.DataFrame( data = freq_anomalie[name][anomalie],  
                                                        index = [i for i in range(len(freq_anomalie[name][anomalie]))],  
                                                        columns = ["Display_Debut", "Display_Fin", "Debut", "Fin"])
                    
    return freq_anomalie
      
    

#%%Retourne Error + Display

def is_error_occurs(data: pd.core.frame.DataFrame, hours_begin: datetime.datetime, hours_end: datetime.datetime, colonne_date: str):
    hours_index = list()
    
    for index in range(len(data)):
        if hours_end >= data[colonne_date][index] >= hours_begin :      
            hours_index.append(index)
    
    
    data_hours = data.loc[hours_index,:]
    data_hours = data_hours.reset_index(drop=True)
    
    return data_hours

def ratio_error_between_date(data: pd.core.frame.DataFrame, analyse_data: dict, name: str, anomalie: str, date_start: datetime.datetime, date_end: datetime.datetime, colonne_date: str):
    nb = 0
    total = 0
    
    for index in range(len(data)):
        if date_end >= data[colonne_date][index] >= date_start: 
            total += 1
    
    for index in range(len(analyse_data[name])):
        
        if date_end >= analyse_data[name][index][0] >= date_start:
            if anomalie == analyse_data[name][index][1]:
                nb += 1
     
    if total == 0:
        return 0
    
    return nb/total


def display(data: pd.core.frame.DataFrame, analyse: dict, analyse_point: dict, name_room:str, confort_temp:float, gap_confort:float, colonne_date:str):
    import matplotlib.pyplot as plt
    
    erreur_list=list(analyse.get(name_room))
    
    indice = 'A'
    
    while indice != "A":
        indice = input("Choissisez un probleme entre 0 et " + str(len(erreur_list)-1) + " :")
        
        if not indice.isdigit():
            continue
        
        if 0 <= int(indice) < len(erreur_list):
            indice = int(indice)
            break
    
    if str(indice) == "A":
        indice = np.random.randint(0, len(erreur_list)-1)
    
    data_error_occurs = is_error_occurs(data, erreur_list[indice][0], erreur_list[indice][1], colonne_date)

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
    
    ratio = ratio_error_between_date(data, analyse_point, name_room, erreur_list[indice][2], erreur_list[indice][0], erreur_list[indice][1], colonne_date)
    
    analyse[name_room][indice].append(ratio)
    
    print("Debut - Fin :", erreur_list[indice][0], "-", erreur_list[indice][1])
    print("Pourcentage d\'incident sur cette période {0:.1%}".format(ratio))
    print("Conseil : ", erreur_list[indice][2])
    
    
#%%
def format_to_send_csv(data: pd.core.frame.DataFrame, full_data: pd.core.frame.DataFrame, analyse: dict, analyse_point: dict, colonne_date: str):
    
    #parcourir a et remplir
    for name in analyse.keys():
        for anomalie in analyse[name].keys():
            for index in range(len(analyse[name][anomalie][0])):
                ratio = ratio_error_between_date(full_data, analyse_point, name, anomalie, analyse[name][anomalie][0]['Debut'][index], analyse[name][anomalie][0]['Fin'][index], colonne_date)
                
                if (str(analyse[name][anomalie][0]['Debut'][index]) == data['Start']).any() and (str(analyse[name][anomalie][0]['Fin'][index]) == data['End']).any():
                    truth_table = ((str(analyse[name][anomalie][0]['Debut'][index]) == data['Start']) & (str(analyse[name][anomalie][0]['Fin'][index]) == data['End']))
                    data.loc[truth_table, name] = anomalie + '\n' + "{0:.1%}".format(ratio)
                else:
                    data = data.append({ name   : anomalie + '\n' + "{0:.1%}".format(ratio),
                                         'Start' : str(analyse[name][anomalie][0]['Debut'][index]),
                                          'End'   : str(analyse[name][anomalie][0]['Fin'][index]) }, 
                                ignore_index=True)
    
    data = data.sort_values(by=['Start', 'End']).reset_index(drop=True)
    
    return data

def format_to_send_json(analyse_format:list, analyse_open: dict, analyse_close: dict):
    #On convertit nos dataframe en dict
    for name in analyse_open.keys():
        for anomalie in analyse_open[name].keys():
            analyse_open[name][anomalie] = analyse_open[name][anomalie].astype(str).to_dict(orient='index')
        
        if name in analyse_close.keys(): 
            for anomalie in analyse_close[name].keys():
                analyse_close[name][anomalie] = analyse_close[name][anomalie].astype(str).to_dict(orient='index')
                
    #On convertit notre dict dans le format souhaité par le site
    for name in analyse_open.keys():
        anomalie_info = list()
        for anomalie in analyse_open[name].keys():
            date_observation = list()
            for indice in analyse_open[name][anomalie].keys():
                date_observation.append({"display_Debut": analyse_open[name][anomalie][indice]["Display_Debut"],
                                        "display_Fin": analyse_open[name][anomalie][indice]["Display_Fin"],
                                        "debut": analyse_open[name][anomalie][indice]["Debut"],
                                        "fin": analyse_open[name][anomalie][indice]["Fin"]})
    
            anomalie_info.append({"nom": anomalie, "liste": date_observation})
        
        if name in analyse_close.keys(): 
            for anomalie in analyse_close[name].keys():
                date_observation = list()
                for indice in analyse_close[name][anomalie].keys():
                    date_observation.append({"display_Debut": analyse_close[name][anomalie][indice]["Display_Debut"],
                                            "display_Fin": analyse_close[name][anomalie][indice]["Display_Fin"],
                                            "debut": analyse_close[name][anomalie][indice]["Debut"],
                                            "fin": analyse_close[name][anomalie][indice]["Fin"]})
        
                anomalie_info.append({"nom": anomalie, "liste": date_observation})
                
        analyse_format.append({"salle": name, "anomalie": anomalie_info})
  
    
    return analyse_format