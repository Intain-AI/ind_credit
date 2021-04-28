from credit_app import app
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import jwt
from pytz import timezone
import datetime
import time
from functools import wraps
import traceback
import config
import os
import shutil
import pandas as pd
import shutil
import glob
import json
import requests
import re
import numpy as np
from zipfile import ZipFile
from os.path import basename

from .bank_statement_functions.indone import verify_token,indone_auth
from .bank_statement_functions.DocIdentifierProcessing import *
from .bank_statement_functions import credit_db
# from .bank_statement_functions.combining_dataframes import combined_dataframe
# from .bank_statement_functions.calculation_analysis import get_statement_analysis
from .bank_statement_functions.table_reconstruction import get_table_data,analysis 
from .bank_statement_functions.calculations import json_to_excel,extraction_results
from .bank_statement_functions.functions import get_desc_keys,straight_through
from .bank_statement_functions import transaction_analysis
from .bank_statement_functions.extracted_fields_df import jsonDict

CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config.update(
    UPLOADED_PATH=os.path.join(basedir, 'static', 'data', 'input'),
    UPLOADED_PATH_NEW=os.path.join(basedir, 'static', 'data', 'temp'),
    JSON_SORT_KEYS = False)
url_upload = "http://0.0.0.0:5004/credit/upload_document"
url_digitize = "http://0.0.0.0:5004/credit/digitize_document"

######### Initialization of the models used for identifying logical cells and table #########
docModel_stage2 = DocElementIdentifierV2()

#########################################################################################################
@app.route('/credit/api_check',methods=['GET'])
def api_check():
    print("working")
    return jsonify({"message":"Successful"}),200

@app.route('/credit/user_dashboard', methods=['POST'])
def user_dashboard():
    try:
        # Validating Token
        response, status,_ = verify_token(request)
        if status != 1:
            return jsonify(response), status
        print("Cheking User Dashboard  ")
        current_user = response['user_email']
        dashboard_response = credit_db.userDashboardDetail(current_user)
        dashboard_response=sorted(dashboard_response, key = lambda i: i['upload_date_time'],reverse=True)


        if not response == -2:
            return jsonify({'result': dashboard_response}), 200
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201
    return jsonify({'result': []}), 200
###########################################################
@app.route("/credit/docelement_document", methods=['POST'])
def docelement_upload_document():

    try:
        # Validating Token
        response, status,_ = verify_token(request)
        if status != 1:
            return jsonify(response), status
        print("Cheking User Dashboard  ")
        current_user = response['user_email']
        data = request.get_json()
        # print("dataaa",data)
        file_path = data['file_path']
        img_dir_path = data['img_dir_path']
        model_type = "stage_2" ; ocr_type = "google_ocr" ; password = ""
        print(password,type(password))
        password = ''
        print("filees\n",file_path,img_dir_path,ocr_type,password)
        response = docModel_stage2.capture_object(file_path,img_dir_path,ocr_type,password)

        return jsonify(eval(str(response))), 200              
             
            
    except Exception as e: 
        print(traceback.print_exc())                                             
        return jsonify({'message': 'Not captured'}), 415

###############################################################################################



###############################################################################################



@app.route("/credit/upload_document", methods=['POST'])
def credit_upload_document():

    extraction_service_id = "711eb617-dc63-4e8c-93c7-506227c2e650"
    response, status, token = indone_auth(extraction_service_id, request)

    if status != 1 :
        return jsonify(response), 401
    emailid = response['user_email']
    single_uploads = []
    try:
        file_path = ""    
        file_name = "" 
        credit_db.delete_null_job(emailid)
        freq = request.files
        freq = list(freq._iter_hashitems())
        job_details = {}
        jobid_counter = credit_db.get_jobid(emailid)
        folder_name = "bank_statement_" + jobid_counter
        folder_path = os.path.join(app.config['UPLOADED_PATH'], folder_name)
        print(folder_path)
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path)
        
        total_file_size = 0
        print("UPLOADED FILES : ", end="")
        for file_ind, (_, files_sent) in enumerate(freq):
            file_name = files_sent.filename
            file_name = file_name.encode('ascii', 'ignore').decode()
            file_name = file_name.replace(" ", "").replace("'", "")
            if not file_name:
                return jsonify({'message': 'No File Found'}), 400

            files_sent.save(os.path.join(folder_path, file_name))
            file_stat = os.stat(os.path.join(folder_path, file_name))
            file_path = folder_path + '/' + file_name
            total_file_size += file_stat.st_size / 1000
            job_details['filename'] = file_name


        job_id='IN_' + jobid_counter
        date_format = "%Y-%m-%d %H:%M"
        now_utc = datetime.datetime.now(timezone('UTC'))
        now_asia = now_utc.astimezone(timezone('Asia/Kolkata'))
        job_details['upload_date_time'] = now_asia.strftime(date_format)
        job_details['emailid'] = emailid
        # job_details['job_id'] = jobid_counter
        job_details['document_name'] = folder_name
        job_details['folder_path'] = file_path.split('.')[0]+'/'
        # job_details['file_path'] = file_path
        job_details['job_size'] = str(total_file_size) + " kB"
        job_details['job_status'] = 'Processing'
        job_details['channel'] = 'Web App'
        job_details['reviewed_by'] = "-"
        job_details['job_id'] = job_id
        credit_db.insert_job(job_details)

        try:
            start_time = time.time()
            pdf_file_name = file_name.split('/')[-1].split('.')[0]
            model_type = "stage_2" ; ocr_type = "google_ocr" ; password = '' 
            print(file_path,folder_path) 
            response = docModel_stage2.capture_object(file_path,folder_path,ocr_type,password)
            if response:                                    
                xml_folder = folder_path + '/'+ pdf_file_name
                pdf_file_name = xml_folder.split('/')[-1]
                excel_file_path = xml_folder + '/' + pdf_file_name +'.xlsx'
                excel_file_path = excel_file_path.split('credit_app')[-1]
                straight_flag=0
                try:
                    error_response, textfield_list, extracted_data = extraction_results(response)
                    df,extracted_data,date_rows,balance_rows,correct=jsonDict(extracted_data)
                    print(date_rows,balance_rows)
                    print(basedir+"/static/data/input/Response.json")
                    with open (basedir+"/static/data/input/Response.json", 'w') as file:
                        file.write(json.dumps(eval(str(extracted_data)), indent=3))
                    extracted_data1 = json.load(open (basedir+"/static/data/input/Response.json"))

                    # extracted_data=json.dumps(eval(str(extracted_data)),indent=3)
                    add_record_status = credit_db.addRecord_Db(extracted_data1,job_id,emailid)
                    if add_record_status == -2:
                        credit_db.update_job_details(excel_file_path,error_response,job_id,"Failed")
                        credit_db.insert_textfield(job_id,{})
                        credit_db.addRecord_Db({},job_id,emailid)
                        return jsonify({'message': 'Not successful!','straight_through':0}), 400
                    credit_db.update_job_details(excel_file_path,error_response,job_id,"To be Reviewed")
                    if error_response!= -2:
                        print("upload response",error_response)    
                        straight_response=straight_through(error_response)
                        textfield_values={}
                        for i in textfield_list:
                            textfield_values[i['label']]=i['value']
                        print("textfield_values\n",textfield_values)
                        credit_db.insert_textfield(job_id,textfield_values)

                        # Straight Through Processing
                        # if straight_response:
                        if len(balance_rows)==0 and len(date_rows)==0 and correct:
                            straight_flag=1
                            data_ = {"job_id":job_details['job_id'], "response":extracted_data1}
                            auth_headers = request.headers.get('Authorization')
                            response_ = requests.post(url_digitize, headers={"Authorization":auth_headers,'Content-Type':'application/json'}, data=json.dumps(data_))
                            if response_.status_code != 200:
                                return response_.json(), response_.status_code
                            else:
                                credit_db.update_job_details(excel_file_path,error_response,job_id,"Straight Through Processed")

                        print(f'\n ++++++ Time Complexity for {pdf_file_name} is {time.time() - start_time} +++++++\n')
                        return jsonify({'message':'Successful!','straight_through':straight_flag,'job_id': job_id}), 200
                    else:
                        credit_db.update_job_details(excel_file_path,error_response,job_id,"Failed")
                        credit_db.insert_textfield(job_id,{})
                        print(f'\n ++++++ Time Complexity for {pdf_file_name} is {time.time() - start_time} +++++++\n')
                        return jsonify({'message':'Not Successful!','straight_through':0,'job_id': job_id}), 400
                except Exception as e: 
                    print(traceback.print_exc())       
                    excel_file_path="NA"
                    credit_db.insert_textfield(job_id,{})

                    credit_db.update_job_details(excel_file_path,"extraction failed",job_id,"Failed")

                    return jsonify({'message': 'Upload Not successful!','straight_through':0,'job_id':job_id}), 400
            else:
                credit_db.insert_textfield(job_id,{})
                return jsonify({'message': 'Upload Not successful!','straight_through':0,'job_id': job_id}), 400
        except Exception as e: 
            print(traceback.print_exc())       
            excel_file_path="NA"
            credit_db.insert_textfield(job_id,{})

            credit_db.update_job_details(excel_file_path,"something failed",jobid_counter,"Failed")
            
            return jsonify({'message': 'Upload Not successful!','straight_through':0,'job_id':job_id}), 400
    except Exception as e:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!','straight_through':0}), 401

##############################################################################################

@app.route('/credit/ui_validation', methods=['POST'])
def ui_validation():
    data = request.get_json()
    try:
        if request.method == 'POST':           
            response, status,_ = verify_token(request)
            if status != 1:
                return jsonify(response), status
            current_user = response['user_email']
            job_response = credit_db.ui_validation(current_user,data['job_id'])
            desc_list=get_desc_keys()
            desc_list.append("Others")
            # print(desc_list)
            if job_response != -2:      
                image_folder_path=job_response['folder_path'].split('credit_app')[1]
                no_images = len(glob.glob(job_response['folder_path']+'/*.jpg'))
                return jsonify({'message': 'Successful!','description_type':desc_list,'filename':[job_response['filename']],'json_ref':[data['job_id']],'images_folder_path':[image_folder_path]  ,"images_count":[no_images] }), 200
            else:
                return jsonify({'message': 'Not successful!'}), 201
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201

########################################################################################################

@app.route("/credit/review", methods=['POST'])
def credit_review_document():
    data = request.get_json()
    try:
        if request.method == 'POST':           
            response, status,_ = verify_token(request)
            if status != 1:
                return jsonify(response), status
            current_user = response['user_email']
            
            job_id = data['job_id']
            # job_response = credit_db.review_document(current_user,data['job_id'],data['filename'])
            job_response = credit_db.getValidatedData_Db(current_user,data['job_id'])
            # print(job_response['status'])
            # print(job_response)

            # print()
            if job_response['status']==1:
                return jsonify({'message': 'Successful!','data':job_response['data'] }), 200
            else:
                return jsonify({'message': 'Not successful!'}), 201
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201

########################################################################################################


@app.route("/credit/digitize_document", methods=['POST'])
def credit_digitize_document():
    data = request.get_json()
    try:
        if request.method == 'POST':           
            response, status,_ = verify_token(request)
            if status != 1:
                return jsonify(response), status
            current_user = response['user_email']
            
            job_id = data['job_id']
            folder_path,excel_file_path = credit_db.digitize_document(current_user,job_id)
            print('excel_file_path',excel_file_path)  
            response=credit_db.updateValidatedData_Db(data['response'],job_id,current_user)          
            if response==0:
                df_list_new,textfield_dict = json_to_excel(data['response'])
                # print('df_list_new',df_list_new)
                final_excel_path=analysis(excel_file_path,df_list_new,textfield_dict)
                print("****************** Digitize completed")
                final_excel_path = final_excel_path.split('credit_app')[1]
                credit_db.update_calculation_job(excel_file_path,job_id,final_excel_path)
                # return jsonify({'message': 'Successful!'}) ,200
                return jsonify({'message': 'Successful!','final_file_path':final_excel_path}), 200
            else:
                return jsonify({'message': 'Not successful!'}), 201
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201

########################################################################################################

@app.route('/credit/zip_batch',methods=['POST'])
def zip_batch():
    data = request.get_json()
    try:
        if request.method == 'POST': 
            response, status,_ = verify_token(request)
            if status != 1:
                return jsonify(response), status
            current_user = response['user_email']
            complete_file_list=[]
            job_ids=data['job_id_list']
            for job_id in job_ids:
                excel_path=credit_db.get_excel(current_user,job_id)
                complete_file_list.append(os.getcwd() + "/credit_app" +excel_path)
            with ZipFile(basedir+"/static/data/input/Consolidated_excel.zip",'w') as zip:
                for file in complete_file_list:
                    print(file)
                    zip.write(file,basename(file))
            return jsonify({"message":"Successful","Zip_file":"/static/data/input/Consolidated_excel.zip"}),200
    except:
        print(traceback.print_exc())
        return jsonify({"message":"Unsuccessful, Cannot Create Zip File"}),201
########################################################################################################

@app.route("/credit/graphs", methods=['POST'])
def credit_graphs():
    data = request.get_json()
    try:
        if request.method == 'POST':           
            response, status,_ = verify_token(request)
            if status != 1:
                return jsonify(response), status
            current_user = response['user_email']
            
            job_id = data['job_id']
            excel_path=credit_db.get_excel(current_user,job_id)
            complete_file = os.getcwd() + "/credit_app" +excel_path
            print(complete_file)
            df=pd.read_excel(complete_file,sheet_name="Transaction_data")
            credit_sum,credit_count=transaction_analysis.pie_chart(df,"Credit")
            debit_sum,debit_count=transaction_analysis.pie_chart(df,"Debit")
            credit_list = [{"name":k, "value":v} for k, v in credit_sum.to_dict()['Credit'].items()] 
            debit_list = [{"name":k, "value":v} for k, v in debit_sum.to_dict()['Debit'].items()] 
            debit_count_list = [{"name":k, "value":v} for k, v in debit_count.to_dict()['Debit'].items()] 
            credit_count_list = [{"name":k, "value":v} for k, v in credit_count.to_dict()['Credit'].items()] 
            calculation_sheet=pd.read_excel(complete_file,sheet_name="Calculations")
            calculation_sheet=calculation_sheet.fillna(0)
            card_values=dict(calculation_sheet.values)
            card_list = [{"name":k, "value":v} for k, v in card_values.items()] 

            return jsonify({
                'Credit':credit_list,
                'Debit':debit_list,
                'Cards':card_list,
                'Transactions':[{"Debit":debit_count_list,"Credit":credit_count_list}]
            }), 200
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201

########################################################################################################

@app.route("/credit/e2EProcessing", methods=['POST'])
def credit_e2EProcessing():


    auth_headers = request.headers.get('Authorization')
    if request.method == 'POST':           
        response, status,_ = verify_token(request)
    if status != 1:
        return jsonify(response), status
    current_user = response['user_email']

    file = request.files["file"]
    fileData = {'file':(file.filename, file.stream, file.content_type, file.headers)}
    
    response = requests.post(url_upload, headers={"Authorization":auth_headers}, files=fileData)
    if response.status_code != 200:
        if "job_id" in response.json():
            textfields=credit_db.get_textfields(response.json()["job_id"])
            print(textfields)
            if textfields!=-2:
                textfields["Processing Type"] = "Manual Intervention Required"
                textfields["Type of Account"] = "Individual Account"
                return textfields
            else:
                return response.json(), response.status_code
        else:
            return response.json(), response.status_code

    
    job_id = response.json()["job_id"]

    if response.status_code==200 and response.json()['straight_through']==1:
        # current_user = response['user_email']
        excel_path=credit_db.get_excel(current_user,job_id)
        complete_file = os.getcwd() + "/credit_app" +excel_path
        try:
            balance_sheet = pd.read_excel(complete_file, sheet_name = "Salary Calculations")
            salary = balance_sheet["Balance"].apply(np.float64).mean()
        except:
            salary = 0

        calculation_sheet = pd.read_excel(complete_file, sheet_name = "Calculations")
        final1=dict(calculation_sheet.values)
        # final={}
        keys_to_extract = ['Account Holder', "Account Number","IFSC Code","Account Opening Date","Monthly Average Balance","Type of Account"]

        final = {key: final1[key] for key in keys_to_extract}

        # final[]=final1['Account Holder']
        # final = calculation_sheet.to_dict(orient='records')[0]
        final["Average Salary"] = salary
        final["Processing Type"] = "Straight Through Processed"    
        # final = calculation_sheet.to_dict(orient='records')[0]
        # final["Total Salary"] = salary

        return jsonify(final), 200


    else:
        textfields=credit_db.get_textfields(job_id)
        print(textfields)
        textfields["Processing Type"] = "Manual Intervention Required"
        return textfields
    
    
