import pandas as pd
# import config.config as project_configs
import re
import os
import traceback
# from process_BS import BS_attributes
# from average_balance import get_monthly_avg_bal
# keywords_file = project_configs.INTAIN_BANK_STATEMENT_KEYWORDS_CSV
# headers_file = project_configs.INTAIN_BANK_STATEMENt_HEADERS_CSV

class StatementAnalyser():
    '''
    TODO
    1. Add logic for KOTAK bank flow
    2. Add code to pickup data within specific timeframe
    3. Add as much keywords for other banks and diff type of transactions
    4. Add remaining formula to the existing ones
    5. Fetch bank name from statement itself instead of passing it separately
    6. Test with more samples
    '''

    def __init__(self,headers_path,keywords_path):
        '''
        Initialize the header names and description for various banks
        Accepts file paths for headers and keywords
        '''        
        header_data = pd.read_csv(headers_path)
        self.header_names = header_data.set_index('bank').to_dict('index')
        desc_data = pd.read_excel(keywords_path)
        self.desc = desc_data.set_index('bank').fillna('').to_dict('index')

    def analyse(self,bank_name,file_path,pdf_file_path,text,word_order):
        '''
        Accepts name of bank ('ICICI','CANARA',etc..) and file_path of statement(should be csv, xls or xlsx format)
        Returns a dictionary with various calculations that can be parsed later
        '''
        if file_path.endswith('csv'):
            statement = pd.read_csv(file_path)
        else:
            try:
                statement = pd.read_excel(file_path,sheet_name='transaction_data')
            except:
                file_path = os.getcwd() + file_path 
                statement = pd.read_excel(file_path,sheet_name='transaction_data')
        try:
            headers = self.header_names[bank_name]
        except:
            print(traceback.print_exc())
            bank_name = 'Unknown Bank'
            headers = self.header_names[bank_name]

        keywords = self.desc[bank_name]
        statement_copy = statement.copy()
        # insert two columns with NA filled
        statement_copy['type'] = 'NA'
        statement_copy['flow'] = 'NA'
        # print(statement_copy)
        for key in keywords:
            check = keywords[key]
            if check:
                statement_copy.loc[statement_copy[headers['desc']].str.contains(check.replace(',','|'),case=False,na=False) 
                                   & statement_copy['type'].str.contains('NA'),'type'] = key  

        statement_copy[[headers['credit'],headers['debit'],headers['balance']]] = \
            statement_copy[[headers['credit'],headers['debit'],headers['balance']]].replace(',','',regex=True).fillna(0.0)
     
        statement_copy[headers['debit']] = statement_copy[headers['debit']].apply(str).str.extract(r'([-]{0,1}[\d\.\d]+)', expand=False)
        statement_copy[headers['credit']] = statement_copy[headers['credit']].apply(str).str.extract(r'([\d\.\d]+)', expand=False)
        statement_copy[headers['balance']] = statement_copy[headers['balance']].apply(str).str.extract(r'([-]{0,1}[\d\.\d]+)', expand=False)

        # print(statement_copy)
        statement_copy[[headers['credit'],headers['debit'],headers['balance']]] = \
            statement_copy[[headers['credit'],headers['debit'],headers['balance']]].fillna(0.0).astype(float)
     

        statement_copy['flow'] = statement_copy[[headers['debit'],headers['credit']]].apply(lambda x: 'C' if x[0]<x[1] else 'D',axis=1)
        statement_copy.loc[statement_copy['type'].str.contains('NA') & statement_copy['flow'].str.contains('D'),'type'] = 'MRNT'

        trans_dict = {}
        print("+++++++++++++++++++++ statement_copy ++++++++++++++++++++++++\n",statement_copy)

        for t_type in keywords.keys():
            filtered = statement_copy[statement_copy['type'].str.contains('^'+t_type+'$',regex=True)].fillna(0.0)
            if len(filtered.index):
                credit = filtered[filtered['flow'].str.contains('C')][headers['credit']]
                trans_dict[t_type+'_C_SUM'] = round(credit.sum(),2)
                trans_dict[t_type+'_C_NUM'] = credit.shape[0]

                debit = filtered[filtered['flow'].str.contains('D')][headers['debit']]
                trans_dict[t_type+'_D_SUM'] = round(debit.sum(),2)
                trans_dict[t_type+'_D_NUM'] = debit.shape[0]

            else:
                trans_dict[t_type+'_C_SUM'] = 'NA'
                trans_dict[t_type+'_C_NUM'] = 'NA'
                trans_dict[t_type+'_D_SUM'] = 'NA'
                trans_dict[t_type+'_D_NUM'] = 'NA'

        #special case for merchant purchases
        filtered = statement_copy[statement_copy['type'].str.contains('^MRNT$',regex=True)].fillna(0.0)
        merchant_debit = filtered[filtered['flow'].str.contains('D')][headers['debit']]
        trans_dict['MRNT_D_SUM'] = round(merchant_debit.sum(),2)
        trans_dict['MRNT_D_NUM'] = merchant_debit.shape[0]

        trans_dict['NUM'] = statement_copy.shape[0]

        flow_count = statement_copy['flow'].value_counts()
        trans_dict['C_NUM'] = flow_count['C']
        trans_dict['D_NUM'] = flow_count['D']
        trans_dict['D_SUM'] = statement_copy[headers['debit']].sum()
        trans_dict['C_SUM'] = statement_copy[headers['credit']].sum()
        trans_dict['MAXB'] = statement_copy[headers['balance']].max()
        trans_dict['MINB'] = statement_copy[headers['balance']].min()

        if bank_name == 'RBL BANK' or bank_name == 'KOTAK MAHINDRA BANK 8' or bank_name == 'ANDHRA BANK':
            opening_credit = statement_copy[headers['credit']].iloc[-1]
            opening_debit = statement_copy[headers['debit']].iloc[-1]        
            opening_balance = statement_copy[headers['balance']].iloc[-1]
            trans_dict['CLOSEB'] = statement_copy[headers['balance']].iloc[0]
            try:
                statement_start_date = statement_copy[headers['txndate']].iloc[-1]
                statement_end_date = statement_copy[headers['txndate']].iloc[0]
            except:
                print(traceback.print_exc())
                statement_start_date = ''
                statement_end_date = ''
        else:
            opening_credit = statement_copy[headers['credit']].iloc[0]
            opening_debit = statement_copy[headers['debit']].iloc[0]        
            opening_balance = statement_copy[headers['balance']].iloc[0]
            trans_dict['CLOSEB'] = statement_copy[headers['balance']].iloc[-1]
            try:
                statement_start_date = statement_copy[headers['txndate']].iloc[0]
                statement_end_date = statement_copy[headers['txndate']].iloc[-1]
            except:
                print(traceback.print_exc())
                statement_start_date = ''
                statement_end_date = ''
        trans_dict['STATEMENT_START_DATE'] = statement_start_date
        trans_dict['STATEMENT_END_DATE'] = statement_end_date

        print(">>>>>>>",statement_start_date,statement_end_date)
        if opening_credit > opening_debit:
            trans_dict['OPENB'] = opening_balance - opening_credit
        else:
            trans_dict['OPENB'] = opening_balance + opening_debit
        
        try:
            if pdf_file_path.endswith('.pdf') or pdf_file_path.endswith('.PDF'):
                new_image_name = pdf_file_path.split('.')[:-1]
                new_image_name = ".".join(new_image_name)
                new_image_name = new_image_name +  '-page100.jpg'
                bank_attributes = BS_attributes(new_image_name,text,word_order)
                trans_dict.update(bank_attributes)
            else:
                bank_attributes = BS_attributes(new_image_name,text,word_order)
                trans_dict.update(bank_attributes)        
        except:
            print(traceback.print_exc())
            pass
        
        return trans_dict

    def parse_analysis(self,trans_dict,bank_name):
        '''
        Accepts the dictionary from analyser
        Returns parsed understandable analysis
        '''

        final_result = {}

        try:
            final_result['01. Account Holder'] = trans_dict['Name']
        except:
            print(traceback.print_exc())
            final_result['01. Account Holder'] = "Not Available"

        try:
            # if bank_name == 'HDFC BANK':
            #     final_result['02. Account Number'] = '22225555888845'
            # else:
            final_result['02. Account Number'] = trans_dict['Account']
        except:
            print(traceback.print_exc())
            final_result['02. Account Number'] = "Not Available"
        

        try:
            dates = trans_dict['Date']
            start_date = dates.split('to')[0]
            end_date = dates.split('to')[-1]
            if trans_dict['STATEMENT_START_DATE'] and str(trans_dict['STATEMENT_START_DATE']) !='nan' :
                print("XXXXXXX",trans_dict['STATEMENT_START_DATE'])
                final_result['03. Statement Start Date'] = trans_dict['STATEMENT_START_DATE']
            else:
                final_result['03. Statement Start Date'] = start_date.strip()

            if trans_dict['STATEMENT_END_DATE']  and str(trans_dict['STATEMENT_END_DATE']) !='nan' :
                final_result['04. Statement End Date'] = trans_dict['STATEMENT_END_DATE']
            else:               
                final_result['04. Statement End Date'] = end_date.strip()

        except:
            final_result['03. Statement Start Date'] = "Not Available"
            final_result['04. Statement End Date'] = "Not Available"
            print(traceback.print_exc())
            pass

        new_bank_name = ''.join([i for i in bank_name if not i.isdigit()])
        final_result['05. Bank Name'] = new_bank_name
        final_result['06. Total number of transactions'] = trans_dict['NUM']

        final_result['07. Minimum balance'] = trans_dict['MINB']
        final_result['08. Maximum balance'] = trans_dict['MAXB']

        final_result['09. Opening Balance'] = round(trans_dict['OPENB'],2)
        final_result['10. Closing Balance'] = trans_dict['CLOSEB']

        final_result['11. Number of credit transactions'] = int(trans_dict['C_NUM'])
        final_result['12. Number of debit transactions'] = int(trans_dict['D_NUM'])

        final_result['13. Total amount credited'] = round(trans_dict['C_SUM'], 2)
        final_result['14. Total amount debited'] = round(trans_dict['D_SUM'], 2)

        final_result['15. Number of cash deposit transactions'] = trans_dict['CASH_C_NUM']
        final_result['16. Total amount of cash deposited'] = trans_dict['CASH_C_SUM']

        final_result['17. Number of cash withdrawal transactions'] = trans_dict['CASH_D_NUM']
        final_result['18. Total amount of cash withdrawed'] = trans_dict['CASH_D_SUM']

        final_result['19. Number of UPI credit transactions'] = trans_dict['UPI_C_NUM']
        final_result['20. Total amount credited through UPI'] = trans_dict['UPI_C_SUM']

        final_result['21. Number of UPI debit transactions'] = trans_dict['UPI_D_NUM']
        final_result['22. Total amount debited through UPI'] = trans_dict['UPI_D_SUM']

        final_result['23. Number of net banking credit transactions'] = trans_dict['NETB_C_NUM']
        final_result['24. Total amount credited through net banking'] = trans_dict['NETB_C_SUM']

        final_result['25. Number of net banking debit transactions'] = trans_dict['NETB_D_NUM']
        final_result['26. Total amount debited through net banking'] = trans_dict['NETB_D_SUM']

        final_result['27. Number of Mobile banking debit transactions'] = trans_dict['MOBB_D_NUM']
        final_result['28. Total amount debited through Mobile banking'] = trans_dict['MOBB_D_SUM']

        final_result['29. Number of Mobile banking Credit transactions'] = trans_dict['MOBB_C_NUM']
        final_result['30. Total amount credited through Mobile banking'] = trans_dict['MOBB_C_SUM']

        final_result['31. Number of salary credit transactions'] = trans_dict['SAL_C_NUM']
        final_result['32. Total amount credited through salary'] = trans_dict['SAL_C_SUM']

        final_result['33. Number of international credit transactions'] = trans_dict['INTL_C_NUM']
        final_result['34. Total amount credited through international transactions'] = trans_dict['INTL_C_SUM']

        final_result['35. Number of international debit transactions'] = trans_dict['INTL_D_NUM']
        final_result['36. Total amount debited through international transactions'] = trans_dict['INTL_D_SUM']

        final_result['37. Number of debit transactions through cheque'] = trans_dict['CHQ_D_NUM']
        final_result['38. Total amount debited through cheque'] = trans_dict['CHQ_D_SUM']

        final_result['39. Number of credit transactions through cheque'] = trans_dict['CHQ_C_NUM']
        final_result['40. Total amount credited through cheque'] = trans_dict['CHQ_C_SUM']
        
        final_result['41. Number of debit transaction through outward cheque'] = trans_dict['CHQB_D_NUM']
        final_result['42. Total amount of debit transaction through outward cheque'] = trans_dict['CHQB_D_SUM']

        final_result['43. Number of of refund transactions'] = trans_dict['REF_C_NUM']
        final_result['44. Total amount of refund'] = trans_dict['REF_C_SUM']

        final_result['45. Number of bank interest transactions'] = trans_dict['BINT_C_NUM']
        final_result['46. Total amount of bank interest'] =  trans_dict['BINT_C_SUM']

        final_result['47. Number of debit card transactions'] = trans_dict['DEBT_D_NUM']
        final_result['48. Total amount spent through debit card'] = trans_dict['DEBT_D_SUM']

        final_result['49. Number of auto-debit transactions'] = trans_dict['ADBT_D_NUM']
        final_result['50. Total amount of auto-debit payments'] = trans_dict['ADBT_D_SUM']

        final_result['51. Number of bill payment transactions'] = trans_dict['BPAY_D_NUM']
        final_result['52. Total amount spent for bill payments'] = trans_dict['BPAY_D_SUM']

        final_result['53. Number of bank charge payments'] = trans_dict['BCHG_D_NUM']
        final_result['54. Total amount of bank charge payments'] = trans_dict['BCHG_D_SUM']

        final_result['55. Number of auto-debit bounce'] = trans_dict['ADBB_C_NUM']
        final_result['56. Total amount of auto-debit bounce'] = trans_dict['ADBB_C_SUM']
     
        final_result['57. Number of Demand Draft credit transactions'] = trans_dict['DD_C_NUM']
        final_result['58. Total amount of credited by using Demand Draft'] = trans_dict['DD_C_SUM']

        final_result['59. Number of Demand Draft Debit transactions'] = trans_dict['DD_D_NUM']
        final_result['60. Total amount of Debited by using Demand Draft'] = trans_dict['DD_D_SUM']

        final_result['61. Number of investment cashin transactions'] = trans_dict['INVC_C_NUM']
        final_result['62. Total amount of investment cashin'] = trans_dict['INVC_C_SUM']

        final_result['63. Number of payment gateway purchase transactions'] = trans_dict['PGTW_D_NUM']
        final_result['64. Total amount spent through payment gateways'] = trans_dict['PGTW_D_SUM']

        final_result['65. Number of merchant outlet transactions'] = trans_dict['MRNT_D_NUM']
        final_result['66. Total amount spent at merchant outlets'] = trans_dict['MRNT_D_SUM']



        
        for x, y in final_result.items():
            if final_result[x] == 'NA':
                final_result[x] = 0
            elif str(final_result[x]) == 'nan':
                final_result[x] = 'Not Available'
        final_result_list = get_final_dict(final_result)
        
        return final_result,final_result_list


'''
Driver function to test the functionality
'''
def get_final_dict(input_dict):
    final_result_list = []
    final_result_id = {}
    count = 1
    for key,val in input_dict.items():
        new_key = re.sub('[^A-Za-z]+', ' ', key)
        # print(key,val)
        new_key = new_key.strip()
        final_result_id = {}
        final_result_id['id'] = count
        final_result_id['name'] = new_key
        final_result_id['value'] = val
        count += 1
        final_result_list.append(final_result_id)
    return final_result_list

    
def get_statement_analysis(csv_file_path,original_bank_name,bank_name,pdf_file_path,text,word_order):

    analyser = StatementAnalyser(headers_file,keywords_file)
    final_result = analyser.analyse(bank_name,csv_file_path,pdf_file_path,text,word_order)
    final_final_result,final_result_list = analyser.parse_analysis(final_result,bank_name)

    calculation_csv = pdf_file_path.split('.')[:-1]
    calculation_csv_path = ".".join(calculation_csv) + '_calculations.xlsx'
    
    key,val,values = [],[],[]
    for name,cal in final_final_result.items():
        name = re.sub('[^A-Za-z]+', ' ', name)
        key.append(name.strip())
        val.append(cal)
    values.append(key); values.append(val)
    df2 = pd.DataFrame(values,index=['Item', 'Details']).transpose()
    csv_file_path = os.getcwd() + csv_file_path
    df3 = pd.DataFrame()
    df3 = get_monthly_avg_bal(csv_file_path,bank_name)
    df4 = pd.DataFrame()
    with pd.ExcelWriter(csv_file_path, engine="openpyxl", mode="a") as writer:
        df2.to_excel(writer,sheet_name = 'calculations and ratios',index=False)
        df3.to_excel(writer,sheet_name = 'EOD Balances',index=False)
        df3.to_excel(writer,sheet_name = 'Summary',index=False)
    calculation_csv_path = csv_file_path.split('bank_statement_analysis')[-1]
    
    return final_final_result,calculation_csv_path,final_result_list

if __name__ == '__main__':
    # final_result = {'01. Account Holder': 'C RADHIKA', '02. Account Number': '166010100050598', '03. Statement Start Date': '15/10/2018', '04. Statement End Date': '07/02/2018', '05. Bank Name': 'ANDHRA BANK', '06. Total number of transactions': 77, '07. Minimum balance': 0.0, '08. Maximum balance': 21607.0, '09. Opening Balance': 14678.0, '10. Closing Balance': 19054.0, '11. Number of credit transactions': 20, '12. Number of debit transactions': 57, '13. Total amount credited': 174064.0, '14. Total amount debited': 167728.5, '15. Number of cash deposit transactions': 0, '16. Total amount of cash deposited': 0.0, '17. Number of cash withdrawal transactions': 29, '18. Total amount of cash withdrawed': 138996.0, '19. Number of UPI credit transactions': 2, '20. Total amount credited through UPI': 4700.0, '21. Number of UPI debit transactions': 0, '22. Total amount debited through UPI': 0.0, '23. Number of net banking credit transactions': 5, '24. Total amount credited through net banking': 9700.0, '25. Number of net banking debit transactions': 1, '26. Total amount debited through net banking': 8002.5, '27. Number of Mobile banking debit transactions': 0, '28. Total amount debited through Mobile banking': 0, '29. Number of Mobile banking Credit transactions': 0, '30. Total amount credited through Mobile banking': 0, '31. Number of salary credit transactions': 9, '32. Total amount credited through salary': 149603.0, '33. Number of international credit transactions': 0, '34. Total amount credited through international transactions': 0, '35. Number of international debit transactions': 0, '36. Total amount debited through international transactions': 0, '37. Number of debit transactions through cheque': 0, '38. Total amount debited through cheque': 0, '39. Number of credit transactions through cheque': 0, '40. Total amount credited through cheque': 0, '41. Number of debit transaction through outward cheque': 0, '42. Total amount of debit transaction through outward cheque': 0, '43. Number of of refund transactions': 0, '44. Total amount of refund': 0, '45. Number of bank interest transactions': 0, '46. Total amount of bank interest': 0, '47. Number of debit card transactions': 11, '48. Total amount spent through debit card': 7361.0, '49. Number of auto-debit transactions': 0, '50. Total amount of auto-debit payments': 0, '51. Number of bill payment transactions': 0, '52. Total amount spent for bill payments': 0, '53. Number of bank charge payments': 7, '54. Total amount of bank charge payments': 755.0, '55. Number of auto-debit bounce': 0, '56. Total amount of auto-debit bounce': 0, '57. Number of Demand Draft credit transactions': 0, '58. Total amount of credited by using Demand Draft': 0, '59. Number of Demand Draft Debit transactions': 0, '60. Total amount of Debited by using Demand Draft': 0, '61. Number of investment cashin transactions': 0, '62. Total amount of investment cashin': 0, '63. Number of payment gateway purchase transactions': 0, '64. Total amount spent through payment gateways': 0, '65. Number of merchant outlet transactions': 9, '66. Total amount spent at merchant outlets': 12614.0}
    
    final_dict = get_final_dict(final_result)
    print(final_dict)