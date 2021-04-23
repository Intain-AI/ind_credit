import pandas as pd
import json
import re

mixed_column = ['type','debit','debits','withdrawalamt.','dr','dr amount','withdrawal','withdrawal no','amount dr','withdrawal amt','withdrawal amount','withdrawal amt.','withdrawals','withdrawal dr','withdrawal in rs.','withdrawal amount inr', 'credit','credits','depositamt.','deposit amt.','cr amount','cr','deposit','amount cr','credit amt','deposits','deposit amount','deposit cr','deposits in rs.','deposit amount inr']

def extractedDataToDf(data):
    table = {}
    real_columns = []
    result = data["result"]
    total_pages = len(result) - 1
    for pageNo in range(1, total_pages+1):
        page_no = "Page_" + str(pageNo)
        table_data = result[page_no]["extraction_results"]["tabledata"][0]
#         for table_data in table_datas:          
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
            elif key == "data":
                for value_dict in value:
                    for i, col_name in enumerate(real_columns):
                        if col_name != "row_coordinates":
                            table[col_name].append(value_dict[i]["word"])
                            table[col_name + "_columnNo"].append(value_dict[i]["columnNo"])
    #                         table[col_name + "_token"].append(value_dict[i]["token"])
                            table[col_name + "_coordinates"].append(value_dict[i]["coordinates"])
                    table["page_no"].append(pageNo)
            elif key == "row_coordinates":
                for value_dict in value:
                    table["row_coordinates"].append(value_dict)
    print(len(table["page_no"]))
    print(len(table["row_coordinates"]))
    print(len(table["Transaction_Type"]))
    df = pd.DataFrame(table)
    return df, real_columns

def check_DrCrMix(real_columns):
    same_index = []
    for i, column_name in enumerate(real_columns):
        column_name.strip()
        seperated_columns = " ".join(column_name.split("/")).split()
        for col in seperated_columns:
            for col_mixed in mixed_column:
                if col_mixed.strip().lower() == col.strip().lower():
                    same_index.append(i)
                        
    if len(set(same_index)) == 1:
        return {"isMixed":1, "MixedIndex":same_index[0]}
#     else if "type" in real_columns:
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
            coordinates.append({})
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
            coordinates.append({})
    df[column_name_new] = llist
    df[column_name_new + "_coordinates"] = coordinates
    return df

def jsonDict(data):
    df, real_columns = extractedDataToDf(data)
    df = fixCrDrMixMain(real_columns, df)
    print("After fixing\n",df)
    df, final_json = dfToDict(df, data)
    return df,final_json


def fixCrDrMixMain(real_columns, df):
    # Check if column is mixed or not
    isMixed = check_DrCrMix(real_columns)
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
    # check if drcr in same column
    flagAmountDrCrMix,amount_index = check_DrCramountSameColumn(real_columns)
    if flagAmountDrCrMix:
        #cr dr with amount
        df = AddColumnMix(df, "Credit", match_char_credit, column_name)
        df = AddColumnMix(df, "Debit",match_char_debit, column_name)
    else:
        amount_name=real_columns[amount_index]
#         print(df)
        df = AddColumnNotMix(df, "Credit",match_char_credit, column_name,amount_name)
        df = AddColumnNotMix(df, "Debit",match_char_debit, column_name,amount_name)    
    return df  

def dfToDict(df, old_dict): 
    all_columns = [x for x in list(df.columns) if "_columnNo" not in x if "_coordinates" not in x if "page_no" not in x]
    all_pages = set(sorted(df.page_no.to_list()))
    page_wise = []
    count = 0
    for pg in all_pages:
        all_rows_page = []
        for row in df.iterrows():
            if row[1]["page_no"] == pg:
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
                all_rows_page.append(one_row)
        page_wise.append(all_rows_page)
                
    for i in all_pages:
        old_dict["result"]["Page_" + str(i)]["extraction_results"]["tabledata"][0]["columns"] = all_columns
        old_dict["result"]["Page_" + str(i)]["extraction_results"]["tabledata"][0]["data"] = page_wise[i-1]
    return df, old_dict

# df, dick = dfToDict(df, data)

if __name__=="__main__":
    data = json.load(open ("/home/credit/ind_credit/Response.json"))
    df,final_json=jsonDict(data)
    print(df)
