import pandas as pd
import numpy as np
import re
from datetime import datetime
import os,json,traceback
from .response import textfield_list
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
header_dict = {'Description': ['description','narration','naration','particular','particulars','transaction remarks','remarks','details'],
'Date':['date','bate','tran date','txn date','(cid:9)txn date','txn. date','transaction date','post date','post dt'],
'Debit':['debit','debits','withdrawalamt.','dr','dr amount','withdrawal','amount dr','withdrawal amt','withdrawal amt.','withdrawals','withdrawal(dr)'],
'Credit': ['credit','credits','depositamt.','deposit amt.','cr amount','cr','deposit','amount cr','credit amt','deposits','deposit(cr)'],
'Balance':['closingbalance','balance','closing balance','balace','closing bal','balance amt','balance(inr)']}

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

def get_desc_keys():
    # print("***desc dict keys****",desc_dict.keys())
    return list(desc_dict.keys())
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
    months=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
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
        # print("*******month list",month_list)
        if month_list and dict_bank['ac_open_date']=='NA':
            dates=words[words.index(month_list[0])-1:words.index(month_list[0])+2]
            dict_bank['ac_open_date']=' '.join(dates)
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
            return datetime.strptime(string, fmt).date()
        except:
            continue
    # raise ValueError(string)

def get_correct_date(df):
    # print("$$$$$$$$\n",df)
    samples = df['Date'].tolist()
    df['Date'] = [guess_date(sample.strip()) for sample in samples]
    df.sort_values(by=['Date'], inplace=True)
    # print(df)
    return df

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

def change_column_name(column_list):
    # print(df)
    column_list = [s.strip() for s in column_list]
    new_col_list = []
    print(column_list)
    for item in column_list:        
        item=re.sub('\s+',' ',item)
        print(item)
        flag = 0
        for k,v in header_dict.items():
            if item.lower() in v:
                flag = 1 ; new_col_list.append(k)
                continue
        if flag == 0:
            new_col_list.append(item)

    return new_col_list

def preprocessing(df):
    # print("++++++++++++++++++++++\n",df)
    df['Balance'] = df['Balance'].apply(lambda x:re.sub('[^0-9.]','',x))
    df['Balance'] = df['Balance'].apply(np.float64)
    return df

def preprocess_date(date_text):
    if date_text != "":
        date_text=date_text.replace('\\','')
        # date_text=re.sub(r'\\','',date_text)
    return(date_text)

def credit_debit(df,excel_file_path):
    df =preprocessing(df)
    df_new=df.filter(['Date','Description','Balance'])

    df_new["Transaction Type"]="Credit"
    df_new["Transaction Amount"]=0

    for index,row in df_new.iterrows():
        if index>0:
            if row['Balance']<df_new.loc[index-1,'Balance']:
                debited_amount=df.loc[index-1,'Balance']-row['Balance']
                df_new.loc[index,"Transaction Type"]="Debit"
                df_new.loc[index,"Transaction Amount"]=debited_amount
            elif row['Balance']>df_new.loc[index-1,'Balance']:
                credited_amount=row['Balance']-df.loc[index-1,'Balance']
                df_new.loc[index,"Transaction Type"]="Credit"
                df_new.loc[index,"Transaction Amount"]=credited_amount

    total_credited_amount=df_new.loc[df_new["Transaction Type"]=="Credit","Transaction Amount"].sum()
    total_debited_amount=df_new.loc[df_new["Transaction Type"]=="Debit","Transaction Amount"].sum()

    with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer:  
        df_new.to_excel(writer, sheet_name = 'Credit Debit')
    # print('df_new++++++++++++\n',df_new)
    return df_new,total_credited_amount,total_debited_amount


def monthly_avg_bal(df,excel_file_path):
    df =preprocessing(df)
    
    # df['Date'] = df['Date'].apply(lambda x: datetime.strptime(str(x), '%d/%m/%y').date())
    
    df[["year", "month", "day"]] = df["Date"].apply(str).str.split("-", expand=True)

    agg_date = df.groupby(['year','month','day']).nth(-1)

    df_new = agg_date.filter(['Date','Balance'])
    
    all_days = pd.date_range(df_new.Date.min(), df_new.Date.max(), freq='D')
    df_date = df_new.set_index('Date').reindex(all_days).fillna(method='ffill').rename_axis('Date').reset_index()

    df_date["Date"] = pd.to_datetime(df_date["Date"]).apply(lambda x: x.date())

    with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer:  
        df_date.to_excel(writer, sheet_name = 'EOD Balances')

    df_date[["year", "month", "day"]] = df_date["Date"].apply(str).str.split("-", expand=True)
    agg_date = df_date.groupby(['year','month'])['Balance'].mean()
    # print(agg_date.columns)
    with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer:  
        agg_date.to_excel(writer, sheet_name = 'Monthly Avg Balance')
    # print("agg_date\n",agg_date.columns)
    mab = agg_date.mean()
    # print("MAB....",mab)
    return mab

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

def get_salary_df(final_excel_path):
    try:
        transaction_df = pd.read_excel(final_excel_path, sheet_name='Transaction_data')
        salary_df=transaction_df[transaction_df['Transaction_Type'] == 'Salary']
        with pd.ExcelWriter(final_excel_path, engine='openpyxl', mode='a') as writer:  
            salary_df.to_excel(writer, sheet_name = 'Salary Calculations')
    except:
        print(traceback.print_exc())
        pass

def get_transaction_analysis(df,final_excel_path,textfield_dict):
    # df = pd.read_excel(excel_file_path,sheet_name="Transaction_data",engine='openpyxl')
    # df = rename_header(df)
    df = get_correct_date(df)
    df2 = df.copy(deep = True)
    mab = monthly_avg_bal(df2,final_excel_path)
    get_salary_df(final_excel_path)
    df_new,total_credited_amount,total_debited_amount = credit_debit(df,final_excel_path)
    cal_dict = {'Monthly Average Balance': mab,'Total Credited Amount': total_credited_amount,
                'Total Debited Amount': total_debited_amount}
    print('textfield_dict',textfield_dict)
    textfield_dict.update(cal_dict)
    cal_df = pd.DataFrame(textfield_dict,index=['values'])
    cal_df = cal_df.transpose()
    with pd.ExcelWriter(final_excel_path, engine='openpyxl', mode='a') as writer:  
        cal_df.to_excel(writer, sheet_name = 'Calculations')

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
    final_df.to_excel("Excel.xlsx",header = True,index = False)


def balance_column_check(credit_list,debit_list,balance_list,error):
    credit_list = [float((re.sub('[^0-9.-]','',x)).strip()) if x!="" else 0.0 for x in credit_list]
    debit_list = [float((re.sub('[^0-9.-]','',x)).strip()) if x!="" else 0.0 for x in debit_list]
    balance_list = [float((re.sub('[^0-9.-]','',x)).strip()) if x!="" else 0.0 for x in balance_list]
    
    for i in range(1,len(balance_list)):
        if balance_list[i-1]<balance_list[i]:
            if abs(credit_list[i]-(balance_list[i]-balance_list[i-1]))>0.1:
                print("Crediiiit",i)
                error.append(i)
        elif balance_list[i]<balance_list[i-1]:
            if abs(debit_list[i]-(balance_list[i-1]-balance_list[i]))>0.1:
                print("Debiittt",i)
                error.append(i)
    return(error)

def add_dictionary(value_dict,value_list):
    new_dict={}
    for values in value_list:
        new_dict[values]=value_dict[values]
    return new_dict
#

def extraction_results(data,json_file_path):
    # with open(input_json, "r") as json_file:
    #     data=json.load(json_file)
    dict_bank=get_logical_text(data)
    others_error={}
    print(dict_bank)
    column_list=[]

    for key,value in data['result'].items():
        tabledata=[]
        error_key=[]
        others_error_key=[]
        digitized_details=data['result'][key]['digitized_details']
        #     print(data['result'][key])
        for tables in digitized_details['table_cells']:
            others_error=[]
            error=[]
            credit_list=[]
            debit_list=[]
            balance_list=[]
            
            # row_list=[]
            if key == 'Page_1':
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
                try:
                    desc_index=column_list.index('Description')
                    credit_index=column_list.index('Credit')
                    debit_index=column_list.index('Debit')
                    balance_index=column_list.index('Balance')
                    date_index=column_list.index('Date')
                except:
                    print("Headers Not Found\n")
                # print(desc_index)
                # tabledata.append('columns':column_list)
            row_list1=[]
            # print("***************",desc_index)
            row_coordinates_list=[]
          
            for index in range(1,len(tables['rows'])):  
                row_list=[]              
                # for rows in tables['rows']:
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
                # col_dict['word']=transaction_type_description(desc)
                # print(type(columns['width']),type(columns['top']),type(columns['id']))
                for i,cols in enumerate(row_list):
                    if cols['columnNo'] == desc_index:
                        desc = cols['word']
                        col_dict['word']=transaction_type_description(desc)
                        # print("Description Type", desc,col_dict['word'])
                        col_dict_coordinates = get_blank_coordinates()
                        col_dict['columnNo']=0
                        col_dict['token']=[]
                        col_dict['coordinates']=col_dict_coordinates
                        if (col_dict['word']=='Others'):
                            others_error.append(index)
                        row_list.append(col_dict)
                # [x for x in range(lst[0], lst[-1]+1) if x not in lst] 
                row_list = sorted(row_list, key = lambda i: i['columnNo'])
                # print("roooooow_list\n",row_list)
                row_list=add_blank_col(row_list,'word',len(column_list),0)
                row_list = sorted(row_list, key = lambda i: i['columnNo'])
                for index,cols in enumerate(row_list):
                    if cols['columnNo']==credit_index:
                        credit_list.append(cols['word'])
                    if cols['columnNo']==debit_index:
                        debit_list.append(cols['word'])
                    if cols['columnNo']==balance_index:
                        balance_list.append(cols['word'])
                    if cols['columnNo']==date_index:
                        cols['word']=preprocess_date(cols['word'])

                row_list1.append(row_list)
            print(credit_list,debit_list,balance_list)
            # error=balance_column_check(credit_list,debit_list,balance_list,error)
            # print("errrrroorrrr",error)
            others_error_key.append(others_error)
            # error_key.append(error)
            
            print("others_error",others_error_key)
            
            tabledata.append({'columns':column_list,'data':row_list1,"row_coordinates":row_coordinates_list,"column_coordinates":tables['column_cords']})

        extraction_results={}
        extraction_results["tabledata"]=tabledata
        if key == 'Page_1':
            textfield = {}
            for attr in textfield_list:
                attr['value']=dict_bank[attr['varname']]            
            textfield["textfield"] = textfield_list
            fields = []
            fields.append(textfield)
        else:
            textfield = {}
            textfield["textfield"] = []
            fields = []
            fields.append(textfield)

        extraction_results["fields"]=fields
        data['result'][key]['extraction_results']=extraction_results
        data['result'][key]['error']=error_key
        data['result'][key]['others_error']=others_error_key
        
    with open (json_file_path, 'w') as file:
        file.write(json.dumps(eval(str(data)), indent=3))
    json_file_to_excel(json_file_path)

def json_to_excel(response):
    data = response.copy()
    # excel_file_path =  os.getcwd()+'/credit_app'+ excel_file_path
    # with open(response, "r") as json_file:
    #     data=json.load(json_file)
    df_list_new = []

    for key,value in data['result'].items():
        tabledata=[]
        # print(key)
        extracted_details=data['result'][key]['extraction_results']['tabledata']
        extracted_fields =data['result'][key]['extraction_results']['fields']
    #     print(extracted_details)
        try:
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
            df.to_excel('SSSSSSS.xlsx')
            def trim(x):
                if x.dtype == object: x = x.str.strip().replace('\s+', ' ',regex=True)
                return(x)
            df = df.apply(trim)
            df_list_new.append(df)
            

        except:
            print(traceback.print_exc())
            pass
        

        if key == 'Page_1':
            textfield_dict = {}
            for index in extracted_fields[0]['textfield']:
                print('+++++++++++++++++++',index['label'],index['value'])
                textfield_dict[index['label']]  = index['value']




    return df_list_new,textfield_dict
