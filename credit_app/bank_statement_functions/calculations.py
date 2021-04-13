import pandas as pd
import numpy as np
import re
from datetime import datetime
import os,json,traceback
from .response import textfield_list
from .Named_Entity_Recognition.NER_Extractor import nerMain
from .functions import empty_values,change_column_name,preprocess_amount,preprocess_date,transaction_type_description,guess_date,get_blank_coordinates,add_blank_col,balance_column_check,validate_column_header,add_dictionary

mandatory_columns=['Date','Description','Credit','Debit','Balance']
desc_remove=['brought forward','carried forward','closing balance','transaction total']

def validate_description(row_list,column_index,others_error,error,index):
    for i,cols in enumerate(row_list):
        if cols['columnNo'] == column_index['Description']:
            desc = cols['word']
            col_dict={}
            col_dict['word']=transaction_type_description(desc)
            # print("Description Type", desc,col_dict['word'])
            col_dict_coordinates = get_blank_coordinates()
            col_dict['columnNo']=0
            col_dict['token']=[]
            col_dict['coordinates']=col_dict_coordinates
            if (col_dict['word']=='Others'):
                error['type']=1
                others_error.append(index)
            row_list.append(col_dict)
    return(row_list,others_error,error)

def validate_columns(row_list,column_index,error,credit_list,debit_list,balance_list,date_list,date_error):
    for index,cols in enumerate(row_list):
        if column_index['Credit']!=0 and column_index['Debit']!=0 and column_index['Balance']!=0:  
            if cols['columnNo']==column_index['Credit']:
                cols['word']=preprocess_amount(cols['word'])
                credit_list.append(cols['word'])
            if cols['columnNo']==column_index['Debit']:
                cols['word']=preprocess_amount(cols['word'])
                debit_list.append(cols['word'])
            if cols['columnNo']==column_index['Balance']:
                cols['word']=preprocess_amount(cols['word'])
                balance_list.append(cols['word'])
        if column_index['Date']!=0:
            if cols['columnNo']==column_index['Date']:
                cols['word']=preprocess_date(cols['word'])
                try:
                    date=guess_date(cols['word'])
                    if date:
                        cols['word']=date
                        date_list.append(date)
                    else:
                        error['date']=1
                        print("else date error",date,index)
                        date_error.append(index)
                except:
                    error['date']=1
                    print("date error",index)
                    date_error.append(index)
    return (row_list,error,credit_list,debit_list,balance_list,date_list,date_error)

def extraction_results(data):
    try:
        # print(textfield_list)
        # with open (json_file_path, 'w') as file:
        #     file.write(json.dumps(eval(str(data)), indent=3))
        # dict_bank=get_logical_text(data) # Rule Based Extraction
        dict_bank = nerMain(data) # NER Based Extraction
        others_error={}
        print(dict_bank)
        column_list=[]
        error_whole=[]
        found_header=0
        error_header={'Description':0,'Credit':0,'Debit':0,'Balance':0,'Date':0}
        for key,value in data['result'].items():
            tabledata=[]
            error_key=[]
            error_others_key=[]
            error_balance_key=[]
            error_date_key=[]
            extraction_results={}
            digitized_details=data['result'][key]['digitized_details']
            #     print(data['result'][key])
            if digitized_details['table_cells']:
                print(key)
                for tables in digitized_details['table_cells']:
                    error={'header':0,'balance':0,'date':0,'type':0,'reconcilation':0}
                    others_error=[]
                    credit_list=[]
                    debit_list=[]
                    balance_list=[]
                    date_list=[]
                    # row_list=[]
                    #finding header and renaming it.
                    if found_header==0:
                        new_column=sorted(tables['rows'][0]['cells'], key = lambda i: i['columnNo'])
                        # print("*****\n\n",new_column)
                        lst = []
                        for i in new_column:
                            lst.append(int(i['columnNo']))
                        new_column=add_blank_col(new_column,'text',max(lst),1)
                        # print("*****\n\n",new_column)
                        for cells in new_column:
                            column_list.append(cells['text'])
                        column_list=change_column_name(column_list)
                        column_list.insert(0,'Transaction_Type')
                        print("Coluuuuumn list",column_list)
                        column_index=validate_column_header(column_list,error_header)
                        print("column index",column_index)
                        found_header=1
                        if 0 in column_index.values():
                            error['header']=1
                    row_list1=[]
                    row_coordinates_list=[]
                    print(column_list)
                    for index in range(1,len(tables['rows'])):  
                        row_list=[]              
                        rows=tables['rows'][index]
                        row_coordinates={}
                        row_coordinates=add_dictionary(rows,['width','top','left','height','id','rowNo'])
                        row_coordinates_list.append(row_coordinates)
                        for cells in tables['rows'][index]['cells']:
                            col_dict={}
                            col_dict_coordinates={} 
                            # print(type(columns['width']),type(columns['top']),type(columns['id']))
                            col_dict_coordinates=add_dictionary(cells,['width','top','left','height','id'])
                            col_dict['word']=cells['text']
                            col_dict['columnNo']= cells['columnNo']
                            col_dict['token']= cells['token']
                            col_dict['coordinates']=col_dict_coordinates
                            row_list.append(col_dict)
                        col_dict={}
                        if column_index['Description']!=0:
                            row_list,others_error,error=validate_description(row_list,column_index,others_error,error,index)
                        row_list = sorted(row_list, key = lambda i: i['columnNo'])
                        # print("roooooow_list\n",row_list)
                        row_list=add_blank_col(row_list,'word',len(column_list),0)
                        row_list = sorted(row_list, key = lambda i: i['columnNo'])
                        date_error=[]
                        date_list=[]
                        row_list,error,credit_list,debit_list,balance_list,date_list,date_error=validate_columns(row_list,column_index,error,credit_list,debit_list,balance_list,date_list,date_error)
                        error_date_key.append(date_error)
                        row_list1.append(row_list)
                    if len(credit_list)!=0 and len(debit_list)!=0 and len(balance_list)!=0: 
                        if error['date']==0:
                            error,balance_error=balance_column_check(date_list,credit_list,debit_list,balance_list,error)
                            print("errrrroorrrr",balance_error)
                            if len(balance_error)!=0:
                                error['balance']=1
                            if error['reconcilation']==1:
                                error['balance']=1
                            error_balance_key.append(balance_error)
                    error_others_key.append(others_error)
                    
                    error_key.append(error)
                    tabledata.append({'columns':column_list,'mandatory_columns':mandatory_columns,'data':row_list1,"row_coordinates":row_coordinates_list,"column_coordinates":tables['column_cords']})
                
                extraction_results["tabledata"]=tabledata
                error_whole.append(error_key)
            if key=="Page_1":
                extraction_results["fields"]=True
            else:
                extraction_results["fields"]=False
            data['result'][key]['extraction_results']=extraction_results
            data['result'][key]['error']={'isError':error_key,'error':{'header':error_header,'type':error_others_key,'balance':error_balance_key,'date':error_date_key}}    
        data['result']['header_fields']=dict_bank
        print("error whole",error_whole)
        return error_whole,dict_bank, data
    except:
        print(traceback.print_exc())
        return -2



def json_to_excel(response):
    data = response.copy()
    # excel_file_path =  os.getcwd()+'/credit_app'+ excel_file_path
    # with open(response, "r") as json_file:
    #     data=json.load(json_file)
    df_list_new = []
    extracted_fields =data['result']['header_fields']
    for key,value in data['result'].items():
        tabledata=[]
        if 'extraction_results' in value:
            try:
                extracted_details=data['result'][key]['extraction_results']['tabledata']
                column_list=extracted_details[0]['columns']
                column_list = [re.sub('\s+', ' ',x) for x in column_list]
                df=pd.DataFrame()
                for rows in extracted_details[0]['data']:
                    row_list=[]
                    for row in rows:
                        row_list.append(row['word'])
                    # print('row_list',row_list,len(row_list))
                    df=df.append([row_list])
            
                df.reset_index(drop=True,inplace=True)
                df.columns=column_list 
                # df.to_excel('SSSSSSS.xlsx')
                def trim(x):
                    if x.dtype == object: x = x.str.strip().replace('\s+', ' ',regex=True)
                    return(x)
                df = df.apply(trim)
                df_list_new.append(df)
            except:
                print(traceback.print_exc())
                pass
    textfield_dict = {}
    for index in extracted_fields:
        print('+++++++++++++++++++',index['label'],index['value'])
        textfield_dict[index['label']]  = index['value']
    return df_list_new,textfield_dict
