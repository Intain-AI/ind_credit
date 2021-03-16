# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 11:01:32 2021

@author: DELL
"""
import pandas as pd
import xmltodict
def xml_dataframe(xml_file_path):
    try:
        with open(xml_file_path,encoding="utf8", errors='ignore') as xml_file:
            data_dict = xmltodict.parse(xml_file.read())
        xmin_list = []
        ymin_list = []
        xmax_list = []
        ymax_list = []
        filename_list = []
        filepath_list = []
        cell_id=0
        cell_id_list=[]
        file_name = data_dict['annotation']['filename']
        file_path = data_dict['annotation']['path']
        for label in data_dict['annotation']['object']:
    #         print(label['name'])
            if label['name'] == 'logical_cell':
                xmin_list.append(int(label['bndbox']['xmin']))
                ymin_list.append(int(label['bndbox']['ymin']))
                xmax_list.append(int(label['bndbox']['xmax']))
                ymax_list.append(int(label['bndbox']['ymax']))
                cell_id_list.append(cell_id)
                filename_list.append(file_name)
            cell_id+=1
                #filepath_list.append(file_path)

        df = pd.DataFrame({'FileName':filename_list,'id':cell_id_list,'xmin':xmin_list,'ymin':ymin_list,'xmax':xmax_list,'ymax':ymax_list})
        return(df)
    except:
        print(xml_file_path)