import xml.etree.ElementTree as ET
import pandas as pd
import glob
import os
import traceback
import numpy as np
from flask import Flask, jsonify, request
import traceback
from DocIdentifierProcessing import *
from table_reconstruction import get_table_data
import time


def read_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    final_data = []
    table_data=[]
    for member in root.findall('table'):
        table_attribs = member.attrib
        for child in member:
            row_attribs = child.attrib
            for c in child:
                cell_text = c.text
                cell_attribs = c.attrib
                data = [cell_text, cell_attribs['xmin'], cell_attribs['ymin'], cell_attribs['xmax'],cell_attribs['ymax'], cell_attribs['id'],row_attribs['id'], table_attribs['id']]
                final_data.append(data)
        table_data.append(table_attribs)
    df = pd.DataFrame(final_data, columns = ['text', 'xmin', 'ymin','xmax','ymax','columnNo', 'linNo', 'tableNo'])
    print('++++++++++',df)
    return table_data, df

def table_reconstruct(tabledf):
        tabledf = tabledf.sort_values(['linNo', 'columnNo'])
        tabledf[['linNo', 'columnNo']] = tabledf[['linNo', 'columnNo']].astype(float)
        rowdf = tabledf.groupby('linNo')
        rowdf.fillna(0, inplace=True)
        lines = []
        for linNo, linNo_df in rowdf:
            column_iter = 1
        
            final_text = []
            coldf = linNo_df.groupby('columnNo')
            for columnNo, column_df in coldf:
                textline = []
                
                for index, space in column_df.iterrows():
                    text = column_df['text'].get(index)
                    textline.append(text)
#                     print(textline)
                    if textline[0] is not None:
                        textline = [' '.join(textline)]
                    else:
                        textline = [' ']
                if columnNo - column_iter != 0:
                    for i in range(int(int(columnNo) - column_iter)):
                        final_text.append(' ')
                        column_iter += 1
                final_text.append(textline[0])
                column_iter += 1
            lines.append(final_text)
        final_table = pd.DataFrame(lines)
        final_table.replace(' ', np.nan, inplace=True)
        final_table.dropna(how='all', axis=1, inplace=True)
        final_table.replace(np.nan, ' ', inplace=True)
#         print(final_table)
        return final_table

# if __name__ == "__main__":

def get_table_data(xml_folderpath):
    try:
        print("+++++++++++++++++",xml_folderpath)
        xml_files = glob.glob(xml_folderpath+'/*.xml')
        excel_file_path = xml_folderpath + '/' + xml_folderpath.split('/')[-1]+'.xlsx'
        print('>>>>>>>>>',excel_file_path)
        for xml_file in range(1,len(xml_files)+1):
            try:
                table_data,tabledf = read_xml(xml_folderpath+'/Page_'+str(xml_file)+'.xml')
                table_gr = tabledf.groupby('tableNo')
                for tableNo, tabledf in table_gr:
                    df = table_reconstruct(tabledf)
                    print(tableNo)
                sheet_name='Page_'+str(xml_file)
                if xml_file == 1:
                    with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='w') as writer:  
                        df.to_excel(writer, sheet_name = sheet_name)
                else:
                    with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer:  
                        df.to_excel(writer, sheet_name = sheet_name)
            except:
                continue
        return  excel_file_path
    except:
        print(traceback.print_exc())
        print('No Table Data')
        return 

if __name__ == '__main__':
    tf=get_table_data("/home/credit/Credit-Testing/static/images/Allahabad_Bank_Sample")