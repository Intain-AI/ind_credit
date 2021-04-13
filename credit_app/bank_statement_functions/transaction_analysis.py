import pandas as pd
import numpy as np
import re
from datetime import datetime
import os,json,traceback
from .functions import desc_dict

def preprocessing(df):
    # print("++++++++++++++++++++++\n",df)
    df['Balance'] = df['Balance'].apply(lambda x:re.sub('[^0-9.]','',x))
    df['Balance'] = df['Balance'].apply(np.float64)
    return df

    # raise ValueError(string)

def get_correct_date(df):
    # df['Date'] = [guess_date(sample.strip()) for sample in samples]
    df.sort_values(by=['Date'], inplace=True)
    # print(df)
    return df

def get_salary_df(final_excel_path):
    try:
        transaction_df = pd.read_excel(final_excel_path, sheet_name='Transaction_data')
        salary_df=transaction_df[transaction_df['Transaction_Type'] == 'Salary']
        with pd.ExcelWriter(final_excel_path, engine='openpyxl', mode='a') as writer:  
            salary_df.to_excel(writer, sheet_name = 'Salary Calculations')
    except:
        print(traceback.print_exc())
        pass

def monthly_avg_bal(df,excel_file_path):
    df =preprocessing(df)
    
    # df['Date'] = df['Date'].apply(lambda x: datetime.strptime(str(x), '%d/%m/%y').date())
    
    df[["year", "month", "day"]] = df["Date"].apply(str).str.split("-", expand=True)
    # print("monthly average baala",df,type(df["Date"][0]))
    agg_date = df.groupby(['year','month','day']).nth(-1)
    df_new = agg_date.filter(['Date','Balance'])
    all_days = pd.date_range(df_new.Date.min(), df_new.Date.max(), freq='D')
    all_days=[i.strftime('%Y-%m-%d') for i in all_days]
    df_date = df_new.set_index('Date').reindex(all_days).fillna(method='ffill').rename_axis('Date').reset_index()
    df_date["Date"] = pd.to_datetime(df_date["Date"]).apply(lambda x: x.date())
    with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer:  
        df_date.to_excel(writer, sheet_name = 'EOD Balances')
    print(df_date)
    df_date[["year", "month", "day"]] = df_date["Date"].apply(str).str.split("-", expand=True)
    agg_date = df_date.groupby(['year','month'])['Balance'].mean()
    # print(agg_date.columns)
    with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer:  
        agg_date.to_excel(writer, sheet_name = 'Monthly Avg Balance')
    # print("agg_date\n",agg_date.columns)
    mab = agg_date.mean()
    return mab

def chart_calculations(df):
    # print("chart calculations\n\n",df)
    chart_dict={}
    key_list=[]
    for key in desc_dict:
        key_list.append(key)
    key_list.append('Others')
    try:
        for key in key_list:
            c=df[df['Transaction_Type']==key]
            chart_dict['No of'+' '+key+' '+'Transactions']=c.shape[0]
            credit_list=list(c['Credit'])

            amount_credited=sum(np.array(credit_list, dtype=np.float64, order='C'))
            debit_list=list(c['Debit'])
            amount_debited=sum(np.array( debit_list,dtype=np.float64, order='C'))
            chart_dict['Amount of'+' '+key+' '+'Credited']=amount_credited
            chart_dict['Amount of'+' '+key+' '+'Debited']=amount_debited
        return(chart_dict)
    except:
        print(traceback.print_exc())
        return {}



def get_transaction_analysis(df,final_excel_path,textfield_dict):
    # df = pd.read_excel(excel_file_path,sheet_name="Transaction_data",engine='openpyxl')
    # df = rename_header(df)
    # df = get_correct_date(df)
    df2 = df.copy(deep = True)
    mab = monthly_avg_bal(df2,final_excel_path)
    get_salary_df(final_excel_path)
    dict_values = credit_debit(df,final_excel_path)
    trans_type_dict=chart_calculations(df)
    # trans_type_dict = transaction_type_analysis(final_excel_path)
    cal_dict = {'Monthly Average Balance': mab}
    print('textfield_dict',textfield_dict)
    textfield_dict.update(cal_dict)
    textfield_dict.update(dict_values)
    textfield_dict.update(trans_type_dict)
    print(textfield_dict)
    cal_df = pd.DataFrame(textfield_dict,index=['values'])
    cal_df = cal_df.transpose()
    with pd.ExcelWriter(final_excel_path, engine='openpyxl', mode='a') as writer:  
        cal_df.to_excel(writer, sheet_name = 'Calculations')




# def transaction_type_analysis(excel_file_path):
    # transaction_df = pd.read_excel(final_excel_path, sheet_name='Transaction_data')
    # salary_df=transaction_df[transaction_df['Transaction_Type'] == 'Salary']
    # with pd.ExcelWriter(final_excel_path, engine='openpyxl', mode='a') as writer:  
        # salary_df.to_excel(writer, sheet_name = 'Salary Calculations')

def pie_chart(df,Type):
    type_df=df[(df[Type].notnull()) ]
    df_filter = type_df.filter(['Transaction_Type',Type])
    # df_filter[Type] = df_filter[Type].apply(lambda x:re.sub('[^0-9.]','',x))
    df_filter[Type] = df_filter[Type].apply(np.float64)
    df_group=df_filter.groupby(['Transaction_Type'])
    df_sum=df_group.sum()
    df_count=df_group.count()
    return(df_sum,df_count)



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
    no_credit_transactions=df_new.loc[df_new["Transaction Type"]=="Credit","Transaction Amount"].count()
    no_debit_transactions=df_new.loc[df_new["Transaction Type"]=="Debit","Transaction Amount"].count()

    with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer:  
        df_new.to_excel(writer, sheet_name = 'Credit Debit')
    dict_values={'Total Credited Amount': total_credited_amount,'Total Debited Amount': total_debited_amount,'No of Credit Transactions':no_credit_transactions,'No of Debit Transactions':no_debit_transactions,'Total Transactions':no_credit_transactions+no_debit_transactions}
    return dict_values