import pandas as pd
import numpy as np
import re
from datetime import datetime
import os,json,traceback
from .response import textfield_list
from .Named_Entity_Recognition.NER_Extractor import nerMain


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

def get_transaction_type(df,excel_file_path):
    df_new=df.filter(['Date','Description','Balance'])
    df_new['Transaction Type']="Others"
    df_new['Description']=df_new['Description'].apply(lambda x:re.sub('[^a-zA-Z]',' ',x))

    df_new.loc[df_new['Description'].str.contains(salary,flags=re.IGNORECASE)==True,'Transaction Type']='Salary'
    df_new.loc[df_new['Description'].str.contains(payment_gateway,flags=re.IGNORECASE)==True,'Transaction Type']='Payment Gateway'
    df_new.loc[df_new['Description'].str.contains(auto_debit,flags=re.IGNORECASE)==True,'Transaction Type']='Auto Debit'
    df_new.loc[df_new['Description'].str.contains(atm,flags=re.IGNORECASE)==True,'Transaction Type']='ATM'
    df_new.loc[df_new['Description'].str.contains(cheque,flags=re.IGNORECASE)==True,'Transaction Type']='Cheque Transaction'
    df_new.loc[df_new['Description'].str.contains(net_banking,flags=re.IGNORECASE)==True,'Transaction Type']='Net Banking'
    df_new.loc[df_new['Description'].str.contains(card_transactions,flags=re.IGNORECASE)==True,'Transaction Type']='Card Transactions'
    df_new.loc[df_new['Description'].str.contains(bank_charges,flags=re.IGNORECASE)==True,'Transaction Type']='Bank Charges'
    df_new.loc[df_new['Description'].str.contains(bank_credit,flags=re.IGNORECASE)==True,'Transaction Type']='Bank Credit'
    df_new.loc[df_new['Description'].str.contains(bill_pay,flags=re.IGNORECASE)==True,'Transaction Type']='Bill Pay'
    df_new.loc[df_new['Description'].str.contains(loan,flags=re.IGNORECASE)==True,'Transaction Type']='Loan'

    # df_new.to_excel('Transaction Type.xlsx',engine='xlsxwriter')
    with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer:  
        df_new.to_excel(writer, sheet_name = 'Transaction Type')

# *****Not being Used****
# def rename_header(df):
#     # print(df)
#     column_list = list(df.columns)
#     column_list = [s.strip() for s in column_list]
#     new_col_list = []
#     for item in column_list:
#         flag = 0
#         for k,v in header_dict.items():
#             if item.lower() in v:
#                 flag = 1 ; new_col_list.append(k)
#                 continue
#         if flag == 0:
#             new_col_list.append(item)
#     df.columns = new_col_list
    # return df

# IFSC_FILE="/home/credit/ind_credit/project_config/IFSC_Code.xlsx"
# def get_bank_name(text):
#     ifsc_list  = re.findall(r'[a-zA-Z]{4}[0o][0-9]{6}',text)
#     df = pd.read_excel(IFSC_FILE)
#     new_bank_name = ''
#     if ifsc_list: 
#         bank_name = ifsc_list[0]
#         IFSC = bank_name[0:4]
#         for index, row in df.iterrows():
#             x = row['IFSC_CODE']
#             x = x.lower()
#             if x == IFSC:
#                 new_bank_name = row['Bank_Name']
#                 print('------bank name from IFSC------',new_bank_name)
#                 return new_bank_name,IFSC

def get_logical_text(data):
    dict_bank={'account_holder_name':'NA','ifsc_code':'NA','ac_open_date':'NA','account_number':'NA','email_id':'NA'}
    text=""
    for key,value in data['result'].items():
        text_list=data['result'][key]['digitized_details']['logical_cells']
        for i in text_list:
            text=text+' '+(i['text'])
    # print("textttt",text)
    text=text.lower().replace('(cid:9)','').replace('\\n',' ')
    text=re.sub('[^a-zA-Z0-9/-]',' ',text)
    text=re.sub('\s+',' ',text)
    Name = ['mr','ms','dear','mrs','name']
    acc_no_list=['account no','account number']
    months=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec','march','january','february','september']
    words=text.split()
    for word in words:
        if word.lower() in Name and dict_bank['account_holder_name']=='NA':
            person_name=words[words.index(word)+1:words.index(word)+3]
            dict_bank['account_holder_name']=(' '.join(person_name)).title()
        # if word.lower()[:3] in months and dict_bank['ac_open_date']=='NA':
        #     date=words[words.index(word)-1:words.index(word)+2]
        #     dict_bank['ac_open_date']=' '.join(date)
        month_string='|'.join(months)
    i=text.find('account statement')
    if i!=-1:
        month_list=re.findall(month_string,text[i:i+200].lower())
        print("*******month list",month_list,text[i:i+200].lower())
        if month_list and dict_bank['ac_open_date']=='NA':
            for j in month_list:
                print(j)
                if dict_bank['ac_open_date']=='NA':
                    try:
                        dates=words[words.index(month_list[j])-1:words.index(month_list[j])+2]
                        print(dates)
                        dict_bank['ac_open_date']=' '.join(dates)
                    except:
                        pass
    ifsc_list  = re.findall(r'[a-zA-Z]{4}[0o][0-9]{6}',text)
    if ifsc_list:
        dict_bank['ifsc_code']=ifsc_list[0].upper()  
    for word in acc_no_list:
        if dict_bank['account_number']=='NA':
            i=text.lower().find(word)
            if i!=-1:
                acc_no=re.findall('[0-9]{11,17}',text[i:i+200])
                if acc_no:
                    # print(acc_no[0])  
                    dict_bank['account_number']=acc_no[0]
    return dict_bank