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
from .bank_statement_functions import credit_db
from .bank_statement_functions.bank_statement import get_file_name
from .bank_statement_functions.combining_dataframes import combined_dataframe
from .bank_statement_functions.calculation_analysis import get_statement_analysis

CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config.update(
    UPLOADED_PATH=os.path.join(basedir, 'static', 'data', 'input'),
    UPLOADED_PATH_NEW=os.path.join(basedir, 'static', 'data', 'temp'))

@app.route('/')
def hello():
    return "Hello World!"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        
        data = request.get_json()
        if not data:
            data = {}
            new_data = request.form
            data['token'] = new_data['token']
        if data is None:
            print("USER Request has no body!")
            return jsonify({'message': 'Request has no body!'}), 201

        if 'token' in data:
            token = data['token']
        else:
            print("USER Token is missing!!")
            return jsonify({'message': 'Token is missing!'}), 201

        try:
            response = credit_db.get_token(data,'user_registration')
            if response == -2:
                print("USER Token is invalid!!")
                return jsonify({'message': 'Token is invalid'}), 201

            registered_user = response['emailid']
            secret_key = response['secretkey']

            datanew = jwt.decode(token, secret_key)
            current_user = datanew['public_id']

            if not current_user == registered_user:
                return jsonify({'message': 'Not Authorized!'}), 201
        except:
            print(traceback.print_exc())
            
            return jsonify({'message': 'Token is invalid'}), 201

        return f(current_user, *args, **kwargs)
    return decorated

########################################################################################################################

@app.route('/credit/user_register', methods=['POST'])
def register_user():
    data = request.get_json()
    print('User register data', data)
    if data is None:
        return jsonify({'message': 'Request has no body!'}), 201
    registration_type = 'user_registration'
    response = credit_db.register_user(data, registration_type)
    print('response',response)
    if response == -1:
        return jsonify({'message': 'User Details Missing!'}), 201
    elif response == -2:
        return jsonify({'message': 'User exists!'}), 201
    elif response == -4:
        return jsonify({'message': 'Mailing error!'}), 201
    return jsonify({'message': 'Registered Successfully!'}), 200

######################################################################################################

@app.route('/credit/user_activate', methods=['GET','POST'])
def activate_customer():
    data = request.args
    response = credit_db.user_activate(data)

    print('User Testing')

    if response == -2:
        return jsonify({'message': 'Invalid Company'}), 201
    elif response == -1:
        return jsonify({'message': 'Invalid User'}), 201
    elif response == -3:
        return jsonify({'message': 'Company Already Active'}), 201
    elif response == -4:
        return jsonify({'message': 'Admin Already Active'}), 201
    return jsonify({'message': 'Activated Successfully!'}), 200

########################################################################################################################

@app.route('/credit/user_login', methods=['POST'])
def login():
    data = request.get_json()
    print("login checking", data)

    if data is None:
        return jsonify({'message': 'Request has no body!'}), 201

    secret_key = data['emailid'] + data['password']

    print("secret_key,", secret_key)

    token = jwt.encode({'public_id': data['emailid'], 'exp': datetime.datetime.now() +
                        datetime.timedelta(minutes=600)}, secret_key)

    credit_db.update_token(data['emailid'], token.decode('UTF-8'))

    return jsonify({'token': token.decode('UTF-8')}), 200

########################################################################################################################

@app.route('/credit/logout', methods=['POST'])
@token_required
def logoutuser(current_user):
    try:
        emailid = current_user
        credit_db.logout_user(emailid)
    except:
        return jsonify({'message': 'Not successful!'}), 201

    return jsonify({'message': 'Logged out!'}), 200

#########################################################################################################################

@app.route('/credit/user_dashboard', methods=['POST'])
@token_required
def user_dashboard(current_user):
    try:
        print("Cheking User Dashboard  ")
        data = request.get_json()
        response = credit_db.user_dashboard_detail(current_user, data)
        
        if not response == -2:
            print("::::::::::::::: Checked User Dashboard")
            return jsonify({'result': response}), 200
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201

    return jsonify({'result': []}), 200

#########################################################################################################################

@app.route('/credit/delete_job_data', methods=['POST'])
@token_required
def delete_job_data(current_user):
    try:
        data = request.get_json()
        job_id = data['job_id']
        response = credit_db.delete_by_job_id(current_user,job_id)
        
        if not response == -2:
            return jsonify({'result': 'success'}), 200
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201

    return jsonify({'result': []}), 200

########################################################################################################################

@app.route('/credit/clear_documents', methods=['POST'])
@token_required
def clear_document(current_user):
    try:
        if request.method == 'POST':           
            folder_path = os.path.join(app.config['UPLOADED_PATH_NEW'],current_user)
            if not os.path.isdir(folder_path):
                os.makedirs(folder_path)
            uploaded_files = os.listdir(folder_path)
            if uploaded_files:
                for f in uploaded_files:
                    f = os.path.join(folder_path,f)
                    os.remove(f)
            return jsonify({'message': 'Cleared directory!'}), 200
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201

########################################################################################################################

@app.route('/credit/delete_documents', methods=['POST'])
@token_required
def delete_document(current_user):
    try:
        if request.method == 'POST': 
            data = request.get_json()
            file_name = data['file_name']
            file_path = os.getcwd() + file_name 
            folder_path = os.path.join(app.config['UPLOADED_PATH_NEW'],current_user)
            if not os.path.isdir(folder_path):
                os.makedirs(folder_path)
            uploaded_files = os.listdir(folder_path)
            for f in uploaded_files:
                f = os.path.join(folder_path,f)
                if f == file_path:
                    os.remove(f)
            return jsonify({'message': 'successful!'}), 200
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201
        
########################################################################################################################
"""
@app.route('/api/process_documents', methods=['POST'])
def process_document():
    if request.method == 'POST':    
        uploaded_files = request.files.getlist("file")
        print('>>>>>>>>>> ',uploaded_files,len(uploaded_files))
        folder_path = os.path.join(app.config['UPLOADED_PATH_NEW'])
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)
        for file2 in uploaded_files:
            file_name = file2.filename
            file2.save(os.path.join(folder_path, file_name))
            new_file_name1 = os.path.join(folder_path, file_name)
            new_file_name = new_file_name1.replace("'", "").replace(" ","_")
            os.rename(new_file_name1, new_file_name)
            break
        print('::::::::::::: file name :::::::::::::::::',new_file_name)

        try:
            file_path = new_file_name
            x = new_file_name
            x = x.split('/')[-1]
            pdf_file_name = x.split('.')[0]
            
            img_dir_path = "/home/credit/Credit-Testing/static/images"
            model_type = "stage_2"
            ocr_type = "google_ocr"
            password = ''
                
            if model_type=='stage_1':
                a=docModel_stage1.capture_object(file_path,img_dir_path,ocr_type,password)
                if a==0:
                    df = get_table_data(xml_file_name)
                    df.to_excel(excel_file_path)
                    return jsonify({'message': "Successfully captured", "excel_path" :excel_file_path }),200
                else:
                    return "Not Captured", 415
            else:              
                a=docModel_stage2.capture_object(file_path,img_dir_path,ocr_type,password)
                if a==0:
                    
                    xml_folder = img_dir_path + '/'+ pdf_file_name
                    print(xml_folder)
                    excel_file_path = get_table_data(xml_folder)
                    return jsonify({'message': "Successfully captured", "excel_path" :excel_file_path }),200
                else:
                    return "Not Captured", 415                
            
        except Exception as e: 
            print(traceback.print_exc())                                             
            return "Not Captured", 415

"""
##############################################################################################################
@app.route('/credit/upload_documents', methods=['POST'])
@token_required
def upload_document(current_user):
    try:
        if request.method == 'POST':           
            uploaded_files = request.files.getlist("file")
            print('#######################',uploaded_files,len(uploaded_files))

            folder_path = os.path.join(app.config['UPLOADED_PATH_NEW'],current_user)
            if not os.path.isdir(folder_path):
                os.makedirs(folder_path)
            counter = len(os.listdir(folder_path))+1
            for file2 in uploaded_files:
                file_name = file2.filename
                file_name = str(counter) + '_' + file_name
                file2.save(os.path.join(folder_path, file_name))
                new_file_name1 = os.path.join(folder_path, file_name)
                new_file_name = new_file_name1.replace("'", "").replace(" ","_")
                os.rename(new_file_name1, new_file_name)
                break
            new_file_name = new_file_name.split('bank_statement_analysis')[-1]
            print("##################",new_file_name)
            return jsonify({'message': 'Successful!','filename' :new_file_name }), 200
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201

########################################################################################################################

@app.route('/credit/process_documents', methods=['POST'])
@token_required
def process_document(emailid):

    temp_folder_path = os.path.join(app.config['UPLOADED_PATH_NEW'],emailid)
    try:
        if request.method == 'POST':
            data = request.form
            print( 'process_documentsdata',data)
            applicant_id = data['applicantid']

            ''' Check if entered applicant id is already exists or not'''
            application_id_resp = credit_db.get_application_id_detail(applicant_id,emailid)
            if application_id_resp != -2:
                return jsonify({'message': 'applicant id already exits'}), 201

            jobid_counter = credit_db.get_jobid(emailid)
            folder_name = "bank_statement_" + str(jobid_counter)

            folder_path = os.path.join(app.config['UPLOADED_PATH'], folder_name)
            if os.path.isdir(folder_path):
                shutil.rmtree(folder_path)
                
            os.makedirs(folder_path,mode=0o777)

            temp_files = os.listdir(temp_folder_path)
            for f in temp_files:
                f = os.path.join(temp_folder_path,f)
                shutil.move(f, folder_path)

            uploaded_files = os.listdir(folder_path)

            if len(uploaded_files)>1:
                new_file_name = get_file_name(uploaded_files,folder_path)
                file = os.stat(os.path.join(folder_path, new_file_name))
                file_size += file.st_size 
                pdf_count = 'multiple'

            else:
                for file2 in uploaded_files:
                    new_file_name = os.path.join(folder_path, file2)
                    file = os.stat(os.path.join(folder_path, file2))
                    new_file_name = new_file_name.replace("'", "")
                    file_size += file.st_size     
                    pdf_count = 'single'       

            file_size = 0
            if uploaded_files:
                file_size = file_size/1000
                job_id = "Job_" + str(jobid_counter)
                
                credit_db.insert_new_job(emailid, job_id, applicant_id, new_file_name)

                
                # output_dataframe, csv_path, bank_type, excel_path, transaction_data = combined_dataframe(bank_name, final_output_json, new_file_name)
                # calculation_response, calculation_csv_path,calculation_result_list = get_statement_analysis(excel_path, bank_name, bank_type, new_file_name, text, word_order)
                # new_file_name = new_file_name.split('bank_statement_analysis')[-1]
                # credit_db.get_single_records(emailid, job_id, new_file_name, output_dataframe,calculation_csv_path,
                #                                 excel_path, transaction_data, calculation_response,calculation_result_list)
                

            return jsonify({'message': 'Successful!', 'new_file_name': new_file_name, 'calculation_csv_path': calculation_csv_path, 'excel_path': excel_path,'job_id':job_id,'calculation_result_list':calculation_result_list}), 200
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Bank Name is not listed in processing bank list', 'job_id': job_id}), 201

############################################################################################################

@app.route('/credit/getdetailsbyid', methods=['POST'])
@token_required
def userGetDetailsByID(current_user):
    data = request.get_json()
    try:
        data = request.get_json()
        emailid = current_user

        response = credit_db.get_Details_By_ID(emailid, data['job_id'])
        print('Get Details By ID',response)

        if not response == -2:
            return jsonify({'result': response}), 200
    except:
        print(traceback.print_exc())
        return jsonify({'message': 'Not successful!'}), 201

    return jsonify({'result': []}), 200
