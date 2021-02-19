
import pandas as pd
# from valid_dataframe import get_valid_dataframe
# from pandas import ExcelWriter
import csv,json
# import os
# import config.config as project_configs
# txndata_json = project_configs.INTAIN_BANK_STATEMENT_TXNDATA_JSON


def combined_dataframe(bank_name,data,file_path):

    try:
        data_response = data['response']
    except:
        data_response = data
    excel_data = []
    for item in data_response:
        excel_data.append(item['excel_data'])
    first_df = excel_data[0]
    first_df = pd.read_json(first_df)
    first_df = first_df.T
    data_list = []
    for item in excel_data:
        train = pd.read_json(item)
        train = train.T
        data_list.append(train)
    new_path = file_path.split('.')[:-1]
    new_file_path = ".".join(new_path)
    csv_path = new_file_path + ".csv"
    excel_path = new_file_path + ".xlsx"
    print("++++ CSV Path = {} ++++".format(csv_path))
    final_data = pd.concat(data_list, ignore_index = True)
    final_dataframe,bank_type = get_valid_dataframe(bank_name,final_data)

    original_dataframe = final_dataframe
    if bank_name == "KOTAK MAHINDRA BANK" or bank_type == 'AXIS BANK A' or bank_type == 'ICICI BANK 9':
        final_dataframe.to_csv(csv_path, encoding='utf-8',header=True, index=False)
        final_dataframe.to_excel(excel_path,'transaction_data',header=True,index=False)
        # writer.save()

    else:
        final_dataframe.to_csv(csv_path, encoding='utf-8',header=False, index=False)
        final_dataframe.to_excel(excel_path,'transaction_data',header=False,index=False)
        new_header = final_dataframe.iloc[0] #grab the first row for the header
        final_dataframe = final_dataframe[1:] #take the data less the header row
        final_dataframe.columns = new_header
                          
    final_dataframe.fillna("", inplace = True) 
    final_dataframe.to_json(txndata_json,orient='records')
    csv_path_new = csv_path.split('bank_statement_analysis')[-1]
    excel_path = excel_path.split('bank_statement_analysis')[-1]
    with open(txndata_json) as f:
        final_combined = json.load(f)
    return original_dataframe, csv_path_new,bank_type,excel_path,final_combined

