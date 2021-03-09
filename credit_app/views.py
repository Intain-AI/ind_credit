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
import pandas as pd
import shutil
import glob
import json

from .bank_statement_functions.indone import verify_token,indone_auth
from .bank_statement_functions.DocIdentifierProcessing import *
from .bank_statement_functions import credit_db
from .bank_statement_functions.combining_dataframes import combined_dataframe
from .bank_statement_functions.calculation_analysis import get_statement_analysis
from .bank_statement_functions.table_reconstruction import get_table_data,analysis 
from .bank_statement_functions.calculations import json_to_excel,extraction_results,get_desc_keys
CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config.update(
    UPLOADED_PATH=os.path.join(basedir, 'static', 'data', 'input'),
    UPLOADED_PATH_NEW=os.path.join(basedir, 'static', 'data', 'temp'),
    JSON_SORT_KEYS = False)

######### Initialization of the models used for identifying logical cells and table #########
docModel_stage2 = DocElementIdentifierV2()

#########################################################################################################

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
        
        if not response == -2:
            return jsonify({'result': dashboard_response}), 200
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201
    return jsonify({'result': []}), 200


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
            print('file_name',file_name, end=", ")
            files_sent.save(os.path.join(folder_path, file_name))
            file_stat = os.stat(os.path.join(folder_path, file_name))
            file_path = folder_path + '/' + file_name
            total_file_size += file_stat.st_size / 1000
        print("file_path*********",file_path)
        date_format = "%Y-%m-%d %H:%M"
        now_utc = datetime.datetime.now(timezone('UTC'))
        now_asia = now_utc.astimezone(timezone('Asia/Kolkata'))
        job_details['upload_date_time'] = now_asia.strftime(date_format)
        job_details['emailid'] = emailid
        job_details['job_id'] = jobid_counter
        job_details['document_name'] = folder_name
        job_details['folder_path'] = file_path.split('.')[0]+'/'
        # job_details['file_path'] = file_path
        job_details['job_size'] = str(total_file_size) + " kB"
        job_details['job_status'] = 'Processing'
        job_details['channel'] = 'Web App'
        job_details['reviewed_by'] = "-"
        job_details['batch_id'] = 'IN_' + jobid_counter
        credit_db.insert_job(job_details)

        try:
            start_time = time.time()
            pdf_file_name = file_name.split('/')[-1].split('.')[0]
            model_type = "stage_2" ; ocr_type = "google_ocr" ; password = ''  
            response = docModel_stage2.capture_object(file_path,folder_path,ocr_type,password)
            # print("RRRRRRRRRR",response)
            if response:                
                xml_folder = folder_path + '/'+ pdf_file_name
                pdf_file_name = xml_folder.split('/')[-1]
                excel_file_path = xml_folder + '/' + pdf_file_name +'.xlsx'

                json_file_path = xml_folder + '/' + pdf_file_name +'.json'
                with open ("SSSSSS.json", 'w') as file:
                    file.write(json.dumps(eval(str(response)), indent=3))
                extraction_results(response,json_file_path)
                # excel_file_path,json_file_path = get_table_data(xml_folder,response)
                excel_file_path = excel_file_path.split('credit_app')[-1]
                print(">>>>>>>>>>",json_file_path)
                credit_db.update_job_details(excel_file_path,json_file_path,jobid_counter)
            print(f'\n ++++++ Time Complexity for {pdf_file_name} is {time.time() - start_time} +++++++\n')
            return jsonify({'message':'Successful!','batch_id': 'IN_' + jobid_counter}), 200

        except Exception as e: 
            print(traceback.print_exc())       
            return jsonify({'message': 'Upload Not successful!'}), 401
    except Exception as e:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 401

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
            job_response = credit_db.ui_validation(current_user,data['batch_id'])
            desc_list=get_desc_keys()
            print("*****",desc_list)
            desc_list.append("Others")
            print(desc_list)
            if job_response != -2:      
                image_folder_path=job_response['folder_path'].split('credit_app')[1]
                no_images = len(glob.glob(job_response['folder_path']+'/*.jpg'))
                # print()
                json_file_path=job_response['json_file_path'].split('credit_app')[1]
                return jsonify({'message': 'Successful!','description_type':desc_list,'json_file_path':json_file_path,'image_folder_path':image_folder_path,"image_count":no_images }), 200
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
            
            batch_id = data['batch_id']
            folder_path,excel_file_path = credit_db.digitize_document(current_user,batch_id,data['response'])
            print('excel_file_path',excel_file_path)            
            df_list_new,textfield_dict = json_to_excel(data['response'])
            # print('df_list_new',df_list_new)
            final_excel_path=analysis(excel_file_path,df_list_new,textfield_dict)
            print("****************** Digitize completed")
            final_excel_path = final_excel_path.split('credit_app')[1]
            credit_db.update_calculation_job(excel_file_path,batch_id,final_excel_path)
            return jsonify({'message': 'Successful!'}) ,200
            # return jsonify({'message': 'Successful!','final_file_path':final_excel_path}), 200

    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201
