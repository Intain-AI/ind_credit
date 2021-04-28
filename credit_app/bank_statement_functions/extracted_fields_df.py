import pandas as pd
import json
import re

mixed_column = ['type','debit','debits','withdrawalamt.','dr','dr amount','withdrawal','withdrawal no','amount dr','withdrawal amt','withdrawal amount','withdrawal amt.','withdrawals','withdrawal dr','withdrawal in rs.','withdrawal amount inr', 'credit','credits','depositamt.','deposit amt.','cr amount','cr','deposit','amount cr','credit amt','deposits','deposit amount','deposit cr','deposits in rs.','deposit amount inr']
desc_remove=['brought forward','carried forward','closing balance','transaction total','b/f','balance b/f','brought forward :','total:','total','opening balance']
not_date=['statementsummary','openingbalance','totalwithdrawalamount','totaldepositamount','closingbalance','withdrawalcount','depositcount','totaltransactioncount','totaldebitcount','totalcreditcount']
import datefinder
from .functions import preprocess_date,correct_date,get_blank_coordinates,header_dict

def cleanSeries(column_name):
    column_name = column_name.astype(str)
    column_name=column_name.apply(lambda x:re.sub('[^[0-9-.]','',x))
    column_name=column_name.apply(pd.to_numeric,errors='ignore')
    column_name=column_name.fillna(0)
    return(column_name)

def extractedDataToDf(data):
    table = {}
    real_columns = []
    result = data["result"]
    total_pages = len(result) - 1
    for pageNo in range(1, total_pages+1):
        page_no = "Page_" + str(pageNo)
        table_datas = result[page_no]["extraction_results"]["tabledata"]
        if table_datas:
            for table_no, table_data in enumerate(table_datas):
                for key, value in table_data.items():
                    if key == "columns":
                        if not real_columns:
                            for column_name in value:
                                real_columns.append(column_name)
                                table[column_name] = []
                                table[column_name + "_columnNo"] = []
            #                     table[column_name + "_token"] = []
                                table[column_name + "_coordinates"] = []
                                table["row_coordinates"] = []
                                table["page_no"] = []
                                table["table_no"]= []
                    elif key == "data":
                        for value_dict in value:
                            for i, col_name in enumerate(real_columns):
                                if col_name != "row_coordinates":
                                    table[col_name].append(value_dict[i]["word"])
                                    table[col_name + "_columnNo"].append(value_dict[i]["columnNo"])
            #                         table[col_name + "_token"].append(value_dict[i]["token"])
                                    table[col_name + "_coordinates"].append(value_dict[i]["coordinates"])
                            table["page_no"].append(pageNo)
                            table["table_no"].append(table_no)
                    elif key == "row_coordinates":
                        for value_dict in value:
                            table["row_coordinates"].append(value_dict)
    df = pd.DataFrame(table)
    return df, real_columns

def check_DrCrMix(df, real_columns):
    same_index = []
    for i, column_name in enumerate(real_columns):
        df[column_name]=df[column_name].astype(str)
        if column_name!='Description' and column_name!='Transaction_Type':
            if df[column_name].str.lower().str.contains("credit").any() and df[column_name].str.lower().str.contains("debit").any():
                same_index.append(i)
            
            elif df[column_name].str.lower().str.contains("cr").any() and df[column_name].str.lower().str.contains("dr").any():
                same_index.append(i)
            
            elif df[column_name].str.lower().str.contains("\+\d",regex=True).any() and df[column_name].str.lower().str.contains("\-\d",regex=True).any():
                same_index.append(i)
    
    print(same_index)
    if len(set(same_index)) == 1:
        return {"isMixed":1, "MixedIndex":same_index[0]}
    
    elif len(same_index) >= 1 or len(same_index) == 0:
        same_index_new = []
        for i in same_index:
            column_name = real_columns[i].strip()
            seperated_columns = " ".join(column_name.split("/")).split()
            for col in seperated_columns:
                for col_mixed in mixed_column:
                    if col_mixed.strip().lower() == col.strip().lower():
                        same_index_new.append(i)
        print(same_index_new)
        if len(set(same_index_new)) == 1: 
            return {"isMixed":1, "MixedIndex":same_index_new[0]}
        else:
            return {"isMixed":0, "MixedIndex":0}
    else:
        return {"isMixed":0, "MixedIndex":0}
            
# isMixed = check_DrCrMix(real_columns)

def check_DrCramountSameColumn(real_columns):
    flagAmountDrCrMix = True # to check amount and Dr and Cr in same column
    amount_index=0
    for i,column in enumerate(real_columns):
        if "amount" in column.lower():
            amount_index=i
            flagAmountDrCrMix = False
    return flagAmountDrCrMix,amount_index

# function if dr and cr and amount is in same column
def AddColumnMix(df, column_name_new, MatchingChar, column_name_actual):
    coordinates = []
    llist = []
    for x in df.iterrows():
        if MatchingChar in x[1][column_name_actual].lower():
            llist.append(re.sub(r'[^0-9,/.]', '', x[1][column_name_actual]))
            coordinates.append(x[1][column_name_actual + "_coordinates"])
        else:
            llist.append('0')
            coordinates.append(get_blank_coordinates())
    df[column_name_new] = llist
    df[column_name_new + "_coordinates"] = coordinates
    return df

# function if Amount AND DR CR ARE IN DIFFERENT COLUMN
def AddColumnNotMix(df, column_name_new, MatchingChar, column_name_actual,amount_name):
    coordinates = []
    llist = []
    for x in df.iterrows():
        if MatchingChar in x[1][column_name_actual].lower():
            llist.append(x[1][amount_name])
            coordinates.append(x[1][amount_name+"_coordinates"])
        else:
            llist.append('0')
            coordinates.append(get_blank_coordinates())
    df[column_name_new] = llist
    df[column_name_new + "_coordinates"] = coordinates
    return df

def correct_date_df(df):
    df['Date']=df['Date'].apply(preprocess_date)
    df['correct_date']=df['Date'].apply(correct_date)
    wrong_date_index_list=df[df.correct_date.isin([-2])].index.tolist()
    correct_date_df=df[~df.correct_date.isin([-2])]
    df['Date']=correct_date_df['correct_date']
    df.drop('correct_date',inplace=True,axis=1)
    return df,wrong_date_index_list

def remove_unwanted(df):
    try:
        df=df[~ df.Description.str.lower().str.strip().isin(header_dict['Description'])]
        df=df[~ df.Description.str.lower().str.strip().isin(desc_remove)]
    except:
        pass
    try:
        df=df[~ df.Date.str.lower().str.strip().isin(not_date)]
    except:
        pass
    df=df.reset_index(drop=True)
    return(df)

def is_reversed(df):
    error_balance_rows=balance_check(df)
    if len(error_balance_rows)>int(len(df)/2):
        df1=df.iloc[::-1].reset_index(drop=True)
        error_balance_rows_reverse=balance_check(df1)
        if len(error_balance_rows)>len(error_balance_rows_reverse):
            print("reverse date")
            return df1,error_balance_rows_reverse
    return df,error_balance_rows

def balance_check(df):
    error_balance_rows=[]
    for index,rows in df[['Credit','Debit','Balance']].iterrows():
        if index==0:
            continue
        try:
            if df['Balance'][index-1]<df['Balance'][index]:
                if abs(df['Credit'][index]-(df['Balance'][index]-df['Balance'][index-1]))>0.1:
                    print("Crediiiit",index)
                    error_balance_rows.append(index)
            elif df['Balance'][index]<df['Balance'][index-1]:
                if abs(df['Debit'][index]-(df['Balance'][index-1]-df['Balance'][index]))>0.1:
                    print("Debiittt",index)
                    error_balance_rows.append(index)
        except:
            error_balance_rows.append(index)
    return error_balance_rows

def string_convert(df):
    df['Balance'] = df['Balance'].astype(str)
    df['Credit'] = df['Credit'].astype(str)
    df['Debit'] = df['Debit'].astype(str)
    return df

def jsonDict(data):
    correct=1
    df, real_columns = extractedDataToDf(data)
    print(real_columns)
    df=remove_unwanted(df)
    wrong_date_index_list=[]
    try:
        df,wrong_date_index_list=correct_date_df(df)
    except:
        correct=0
    if not('Balance' in real_columns and 'Debit' in real_columns and 'Credit' in real_columns):
        print("fixing columns")
        df = fixCrDrMixMain(real_columns, df)
    error_rows=[]
    if 'Balance' in real_columns and 'Credit' in real_columns and 'Debit' in real_columns:
        if len(df['Credit'])!=len(df['Debit']) and len(df['Credit'])!=len(df['Balance']) and len(df['Debit'])!=len(df['Balance']):
            print("Length Match Error\n")
        else:
            print("checking balance")
            df['Balance']=cleanSeries(df['Balance'])
            df['Credit']=cleanSeries(df['Credit'])
            df['Debit']=cleanSeries(df['Debit'])
            df,error_rows=is_reversed(df)
            df=string_convert(df)
    else:
        correct=0
    df=df.fillna("")
    df, final_json = dfToDict(df, data)
    return df,final_json,wrong_date_index_list,error_rows,correct

def fixCrDrMixMain(real_columns, df):
    # Check if column is mixed or not
    isMixed = check_DrCrMix(df, real_columns)
    print(isMixed)
    if isMixed['isMixed'] != 1:
        return df
    indexMixed = isMixed['MixedIndex']
    column_name = real_columns[indexMixed]
    match_char_credit='cr'
    match_char_debit='dr'
    if df[column_name].str.lower().str.contains('credit', regex=False).any():
        match_char_credit='credit'
        match_char_debit='debit'
    elif df[column_name].str.lower().str.contains("\+",regex=True).any():
        match_char_credit='+'
        match_char_debit='-'    
    
    # check if drcr in same column
    flagAmountDrCrMix,amount_index = check_DrCramountSameColumn(real_columns)
    if flagAmountDrCrMix:
        #cr dr with amount
        print("if")
        df = AddColumnMix(df, "Credit", match_char_credit, column_name)
        df = AddColumnMix(df, "Debit",match_char_debit, column_name)
    else:
        amount_name=real_columns[amount_index]
        print("else")
        df = AddColumnNotMix(df, "Credit",match_char_credit, column_name,amount_name)
        df = AddColumnNotMix(df, "Debit",match_char_debit, column_name,amount_name)
    return df  

def dfToDict(df, old_dict): 
    all_columns = [x for x in list(df.columns) if "_columnNo" not in x if "_coordinates" not in x if "page_no" not in x if "table_no" not in x]
    all_pages = set(sorted(df.page_no.to_list()))
    for pg in all_pages:
        all_tables_in_page = set(sorted(df[df["page_no"] == pg].table_no.to_list()))
        for table_no in all_tables_in_page:
            table_wise = []
            for row in df.iterrows():
                if row[1]["page_no"] == pg and row[1]["table_no"] == table_no:
                    one_row = []
                    for key, values in row[1].items():
                        for col in all_columns:
                            cell = {}
                            if key == col:
                                cell["word"] = row[1][key]
                                cell["columnNo"] = all_columns.index(col)
                                cell["token"] = [] 
                                cell["coordinates"] = row[1][key + "_coordinates"]
                                one_row.append(cell)
                    table_wise.append(one_row)
            old_dict["result"]["Page_" + str(pg)]["extraction_results"]["tabledata"][table_no]["data"] = table_wise
    return df, old_dict

# df, dick = dfToDict(df, data)

if __name__=="__main__":
    data = json.load(open ("/home/credit/ind_credit/Response.json"))
    df,final_json=jsonDict(data)
    print(df)
