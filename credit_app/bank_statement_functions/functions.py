import pandas as pd
import numpy as np
import re
from datetime import datetime
import os,json,traceback
from .response import textfield_list
import datefinder

idd=50000
desc_dict={
    "Salary":'salary|stipend',
    "Cheque":"by clearing|by cheque|clg",
    "Net Banking":"neft|tpt|rtgs|imps|utr|TO TRANSFER|OFT|TPFT|inb|BRN-RTGS",
    "Payment Gateway":"abps|ecom|paytm|RAZPRAZORPAYSOFTWARE|billdesk|gpay|othpg|razorpay",
    "Auto Debit":"nach|ach|emi|ecs|msi",
    "Bank Charges":"DEBIT CARD ANNUAL FEE|SMS CHARGES|INSPECTION CHGS|GST|DOCUMENTATION CHARGE|PROCESSING FEE|Charges|CHEQUE BOOK ISSUE CHARGES|CHRGS|RTN CHQ CHGS|tbms|AMB CHRG|debit interest captialised",
    "ATM Transaction":"atm|atw|cash|atm csw|nwd|owd|cwdr|ats|eaw|nfs|awb|vat|mat",
    "Card Transaction":"pos|POSTXN|PRCR|medr|vps|prcr|pcd",
    "Bank Credit":'credit|credit interest captialised',
    "Bill Pay":'bpay|bil|billpay|ebpp|blpgcm',
    "Loan":'disburse',          
    "Demand Draft":'dd/cc|dd',
    "UPI":'upi'}
header_dict = {'Description': ['description','transaction description','account description','narration','naration','particular','particulars','transaction remarks','remarks','details','keterangan'],
'Date':['date','bate','tran date','txn date','transaction date & time','cid:9 txn date','txn. date','transaction date','post date','post dt','tanggal'],
'Debit':['debit','debits','withdrawalamt.','dr','dr amount','withdrawal','withdrawal no','amount dr','withdrawal amt','withdrawal amount','withdrawal amt.','withdrawals','withdrawal dr','withdrawal in rs.','withdrawal amount inr','withdrawal s'],
'Credit': ['credit','credits','depositamt.','deposit amt.','cr amount','cr','deposit','amount cr','credit amt','deposits','deposit amount','deposit cr','deposits in rs.','deposit amount inr'],
'Balance':['closingbalance','balance','closing balance','running balance','balace','closing bal','balance amt','balance amount','balance inr','balance in rs.','balance amount inr','saldo','balance rs.']}
combined_list=[]
desc_remove=['brought forward','carried forward','closing balance','transaction total']
for key in header_dict:
    combined_list.extend(header_dict[key])
# def empty_values():
#     dict_empty_type={}
#     for key in desc_dict:
#         dict_empty_type['No of '+key+' Transactions']=0  
#     # print(dict_empty_type)
#     dict_empty_type['No of Other Transactions']=0  
#     return(dict_empty_type)
#     # df={'No of Auto Debit Transactions':0,
#     # 'No of Debit Card Transactions':0,
#     # ''}


def get_desc_keys():
    # print("***desc dict keys****",desc_dict.keys())
    return list(desc_dict.keys())

def correct_date(date_string):
    try:
        matches = datefinder.find_dates(date_string)         
        match=list(matches)
        # print(match[0].strftime("%Y-%m-%d")) 
        return(match[0].strftime("%Y-%m-%d"))
    except:
        print("except correct date",date_string)
        return -2
def change_column_name(column_list):
    # print(df)
    column_list = [s.strip() for s in column_list]
    new_col_list = []
    # print(column_list)
    for item in column_list:        
        item=re.sub('[\(_\)*]',' ',item)
        item=re.sub('\s+',' ',item)
        item=item.strip()
        # print(item)
        flag = 0
        for k,v in header_dict.items():
            if item.lower() in v:
                flag = 1 ; new_col_list.append(k)
                continue
        if flag == 0:
            new_col_list.append(item)

    return new_col_list

def preprocess_amount(amount):
    if amount=='-' or amount=='' or amount=='--':
        amount='0.0'
    amount = re.sub('cr.','',amount.lower()).strip()
    amount = re.sub('[^0-9.-]','',amount).strip()
    return(amount)


def preprocess_date(date_text):
    if date_text != "":
        date_text=date_text.replace('\\','')
        date_text = re.sub('([a-zA-Z]) ([a-zA-Z]) ?',r'\1\2', date_text)
        date_text=re.sub(r'\\','',date_text)
        # print("before",date_text)
        date_text= re.sub(r"(/)\s+(\d)",r'\1\2',date_text)
        # print("after",date_text)
        # date_text= re.sub("(/) +([\d])", r'\1\2',date_text);

    return(date_text)

def transaction_type_description(description):
    description=re.sub('[^a-zA-Z]',' ',description)
    description=re.sub('\s+',' ',description)
    transaction_ref="Others"
    for key,value in desc_dict.items():
        if transaction_ref=="Others":
            search=re.findall(value,description,flags=re.IGNORECASE)
            if search:
                transaction_ref=key
    return(transaction_ref)

def guess_date(string):
    date_formats = ["%Y/%m/%d",   # 2017/5/23 or 2017/05/23
                    "%d/%m/%Y",   # 22/04/2015
                    "%Y%m%d",     # 20150504
                    "%d-%m-%Y",   # 22-04-2015
                    "%Y-%m-%d",   # 2015-04-23
                    "%d/%m/%y",   # 05/03/18
                    '%d %b %Y',   # 23 Apr 2020
                    '%d%b%Y',     # 23Apr2020
                    '%d%B%Y',     # 23April2020
                    '%d %b %y',   # 23 Apr 20
                    '%d %B %y',   # 23 April 20
                    '%d %B %Y',   # 23 April 2020
                    '%d-%b-%y',   # 23-Apr-20
                    '%d-%b-%Y']   # 23-Apr-2020
                    
    for fmt in date_formats:  
        try:
            return datetime.strptime(string.strip(), fmt).date().strftime("%Y-%m-%d")
        except:
            continue


def straight_through(result):
    try:
        for page_list in result:
            for table_list in page_list: 
                # print(table_list)
                if table_list['header']==1 or table_list['balance']==1 or table_list['date']==1 or table_list['reconcilation']==1:
                # if table_list['date']==1:
                    return 0
        return 1
    except:
        return 0
    # get_transaction_type(df,excel_file_path)


def get_blank_coordinates():
    col_dict_coordinates = {}
    col_dict_coordinates['width']=10
    col_dict_coordinates['top']=10
    col_dict_coordinates['left']=10
    col_dict_coordinates['height']=10
    global idd
    idd=idd+1
    col_dict_coordinates['id']=idd
    return col_dict_coordinates

def add_blank_col(row_list,text,length,index):
    lst = []
    for i in row_list:
        lst.append(int(i['columnNo']))
    # print("new list\n\n",lst,max(lst))

    missing_list = [x for x in range(index,length) if x not in lst] 
    for index in missing_list:
        # print("Index...",index)
        new_list={}
        if index==0:
            new_list[text]='Others'
        elif text=='text':
            new_list[text]='empty'+str(index)
        else:
            new_list[text]=''
        new_list['columnNo']=index
        new_list['coordinates']=get_blank_coordinates()
        row_list.insert(new_list['columnNo']-1,new_list)
    return(row_list)

def json_file_to_excel(json_file_path):
    with open(json_file_path, "r") as json_file:
        data=json.load(json_file)
    df_list_new,textfield_dict = json_to_excel(data)
    final_df = pd.concat(df_list_new,ignore_index=True)
    # final_df.to_excel("Excel.xlsx",header = True,index = False)


def balance_column_check(date_list,credit_list,debit_list,balance_list,error):
    error_balance_rows=[]
    try:
        # credit_list = [float((re.sub('[^0-9.-]','',x)).strip()) if x!="" else 0.0 for x in credit_list]
        # debit_list = [float((re.sub('[^0-9.-]','',x)).strip()) if x!="" else 0.0 for x in debit_list]
        # balance_list = [float((re.sub('[^0-9.-]','',x)).strip()) if x!="" else 0.0 for x in balance_list]
        credit_list = [float(x) for x in credit_list]
        debit_list = [float(x) for x in debit_list]
        balance_list = [float(x) for x in balance_list]
        print("length Date,C D B",len(date_list),len(credit_list),len(debit_list),len(balance_list))
        if len(credit_list)!=len(debit_list) and len(credit_list)!=len(balance_list) and len(debit_list)!=len(balance_list):
            print("Length Match Error\n")
            error['reconcilation']=1
        else:
            print("checking balance")
            for i in range(1,len(balance_list)):
                if balance_list[i-1]<balance_list[i]:
                    if abs(credit_list[i]-(balance_list[i]-balance_list[i-1]))>0.1:
                        print("Crediiiit",i)
                        error_balance_rows.append(i)
                elif balance_list[i]<balance_list[i-1]:
                    if abs(debit_list[i]-(balance_list[i-1]-balance_list[i]))>0.1:
                        print("Debiittt",i)
                        error_balance_rows.append(i)
        return (error,error_balance_rows)

    except:
        print("except balance")
        error['reconcilation']=1
        return (error,error_balance_rows)

def add_dictionary(value_dict,value_list):
    new_dict={}
    for values in value_list:
        new_dict[values]=value_dict[values]
    return new_dict
#
def validate_column_header(column_list,error_header):
    column_index={'Description':0,'Credit':0,'Debit':0,'Balance':0,'Date':0}
    try:
        desc_index=column_list.index('Description')
        column_index['Description']=desc_index
    except:
        error_header['Description']=1
    try:                    
        credit_index=column_list.index('Credit')
        column_index['Credit']=credit_index
    except:
        error_header['Credit']=1
    try:
        debit_index=column_list.index('Debit')
        column_index['Debit']=debit_index
    except:
        error_header['Debit']=1
    try:
        balance_index=column_list.index('Balance')
        column_index['Balance']=balance_index
    except:
        error_header['Balance']=1
    try:
        date_index=column_list.index('Date')
        column_index['Date']=date_index
    except:
        error_header['Date']=1
    return column_index


db_mix_list = ["Withdrawal Dr / Deposit Cr", "Debit/Credit"]
def debit_credit_mix(column_list, error_header):
    
    pass
    