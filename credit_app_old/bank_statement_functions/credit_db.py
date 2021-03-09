from pymongo import MongoClient
import traceback
import os,json
from flask import jsonify
from config import IND_EMAIL,IND_PASSWD,BASE_URL
from config import  IND_CREDIT_MONGODB_URL,IND_CREDIT_MONGODB_PORT,IND_CREDIT_MONGODB_NAME

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from calculation_analysis import get_statement_analysis
from uuid import uuid4
# from valid_format import get_valid_format
# from combining_dataframes import combined_dataframe

from datetime import datetime
from pytz import timezone

# from bank_statement import get_bank_statement,extraction_data,extraction_column,check_password_new,get_file_name,get_password_status
# from document_type import get_document_type

uri = "mongodb://{}:{}/{}".format(IND_CREDIT_MONGODB_URL, IND_CREDIT_MONGODB_PORT,IND_CREDIT_MONGODB_NAME)
mongo_db_client = MongoClient(uri)
db = mongo_db_client[IND_CREDIT_MONGODB_NAME]

collection_job = db['job_detail']
collection_user = db['user_detail']
collection_token = db['token_detail']
collection_analysis = db['analysis_detail']

########################################################################################################################
def register_user(request_data,registration_type):
    user_attributes = ['firstname','lastname','password','emailid','phone','companyname']
    for attribute in user_attributes:
        if attribute not in request_data:
            return -1
        

    collection = db['user_detail']

    resp = collection.find_one({'emailid':request_data['emailid'],'registration_type':registration_type})
    if not resp:
        secret_key = ""
        for attribute in user_attributes[:6]:
            secret_key = secret_key + request_data[attribute]
        request_data['secretkey'] = secret_key
        request_data['status']='Inactive'
        request_data['registration_type'] = registration_type
        collection.insert_one(request_data)

        resp = collection.find_one({'secretkey':secret_key,'emailid':request_data['emailid']})

        port = 465  # For SSL
        sender_email=IND_EMAIL
        receiver_email = request_data['emailid']
        
        activate_url = BASE_URL + "/activate_customer?emailid=" + receiver_email + "&secretkey=" + secret_key 
        message = MIMEMultipart("alternative")
        message["Subject"] = "IN-D Credit: Activation Required"
        message["From"] = IND_EMAIL
        message["To"] = receiver_email
        
        text = """\
        click to activate """ + activate_url
        
        htmltext = """\
        <html>
        <head></head>
        <body>
            <div class="container justify-content-center" style="margin: 50px 100px">
    
                <h3 style="font-size: 26px; color: #2b2b2b; text-align: center ">
                    Activate your IN-D Credit account
                </h3>
    
                <hr style="border-top: 1px solid #b7b9bb; width: 100%; margin-top: 30px">
    
                <p style="font-size: 18px; color: #4c4c4e; text-align: left;font-weight: bold; padding-top: 10px">
                    Hello , 
                </p>
    
                <p style="font-size: 16px; color:#777783; text-align: left; line-height: 23px">
                    To activate your IN-D Credit account simply click the button below. 
                    Once clicked your request will be processed and verified and you 
                    will be redirected to the IN-D Credit Web application.
                </p>
    
                <div class="wrapper" style="margin-top: 20px; margin-bottom: 20px; text-align: center">
                    <a href=" """ + activate_url + """ "><button style="background-color: #0085d8; border: 1px solid #0085d8; color: white; font-size: 14px; height: 35px; width: 200px; cursor: pointer;">
                        ACTIVATE ACCOUNT
                    </button></a> 
                </div>
    
                <p style="font-size: 16px; color:#777783; text-align: left; line-height: 23px">
                    You are receiving this email because you created an IN-D Credit account. 
                    If you believe you have received this email in error, please mail us 
                    to <a href="#">explore@in-d.ai</a> 
                </p>
    
                <hr style="border-top: 1px solid #b7b9bb; width: 100%; margin-top: 30px">
                
    
            </div>
        </body>
        </html>
        """
        
        mail_body=MIMEText(htmltext,"html")
        
        message.attach(mail_body)
        
        # Create a secure SSL context
        context = ssl.create_default_context()
        
        
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(IND_EMAIL, IND_PASSWD)
            server.sendmail(sender_email,receiver_email,message.as_string())
           
        
    else:
        mongo_db_client.close()  
        return -2

    mongo_db_client.close()
    return 1


########################################################################################################################

def user_activate(request_data):

    print(request_data)
    #secretkey=request_data['companyname'][0:8].replace(' ','')
    collection = db['user_detail']
    print(request_data['secretkey'])
    resp = collection.find_one({'secretkey':request_data['secretkey']})
    
    if not resp:
        print('Invalid Customer')
        mongo_db_client.close()
        return -2
    else:
        if resp['status'] != 'Active':

            resp = collection.find_one({'secretkey':request_data['secretkey'],'emailid':request_data['emailid'],})
            if not resp:
                mongo_db_client.close()
                return -1
            else:
                if resp['status'] != "Active":
                    print('Activating')
                    format_date = "%Y-%m-%d %H:%M"
                    now_utc = datetime.now(timezone('UTC'))
                    now_asia = now_utc.astimezone(timezone('Asia/Kolkata'))

                    resp = collection.update_one({'secretkey':request_data['secretkey']},{"$set":{'status': 'Active','reg_date_time':now_asia.strftime(format_date)}})
                    port = 465  # For SSL
                    sender_email = IND_EMAIL
                    receiver_email = request_data['emailid']
                    
                    login_url = BASE_URL
                    
                    message = MIMEMultipart("alternative")
                    message["Subject"] = "IN-D Credit: Welcome!!!!"
                    message["From"] = sender_email
                    message["To"] = receiver_email
                    htmltext = """
                    <html>
                    <head></head>
                    <body>
                        <div class="container justify-content-center" style="margin: 50px 100px">
                
                            <h3 style="font-size: 26px; color: #2b2b2b; text-align: center ">
                                IN-D Credit account activation confirmation
                            </h3>
                
                            <hr style="border-top: 1px solid #b7b9bb; width: 100%; margin-top: 30px">
                
                            <p style="font-size: 18px; color: #4c4c4e; text-align: left;font-weight: bold; padding-top: 10px">
                                Hello , 
                            </p>
                
                            <p style="font-size: 16px; color:#777783; text-align: left; line-height: 23px">
                                Your account has been actvated. You can now access the application with your credentials using the following link
                            </p>
                
                            <div class="wrapper" style="margin-top: 20px; margin-bottom: 20px; text-align: center">
                                <a href=" """ + login_url + """ "><button style="background-color: #0085d8; border: 1px solid #0085d8; color: white; font-size: 14px; height: 35px; width: 200px; cursor: pointer;">
                                    Click To Login
                                </button></a> 
                            </div>
                            
                             <p style="font-size: 16px; color:#777783; text-align: left; line-height: 23px">
                                Please make a note of the customer key """ + request_data['secretkey'] + """ for API access 
                            </p>
                
                            <p style="font-size: 16px; color:#777783; text-align: left; line-height: 23px">
                                You are receiving this email because you activated an IN-D Credit account. 
                                If you believe you have received this email in error, please mail us 
                                to <a href="#">explore@in-d.ai</a> 
                            </p>
                
                            <hr style="border-top: 1px solid #b7b9bb; width: 100%; margin-top: 30px">
                            
                
                        </div>
                    </body>
                    </html>
                    """
            
                    mail_body=MIMEText(htmltext,"html")
                    
                    message.attach(mail_body)
                    
                    # Create a secure SSL context
                    context = ssl.create_default_context()
                    
                                        
                    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                        server.login(IND_EMAIL, IND_PASSWD)
                        server.sendmail(sender_email,receiver_email,message.as_string())
                else:
                    mongo_db_client.close()
                    return -2
        else:
            print('already active')
            mongo_db_client.close()
            return -3
    mongo_db_client.close()
    return 1
  
########################################################################################################################
def login_user(request_data):
    login_attributes = ['emailid', 'password'] 

    for attribute in login_attributes:
        if attribute not in request_data:
            return -1,""
    collection = db['user_detail']

    resp = collection.find_one({'emailid': request_data['emailid'], 'password': request_data['password'],
                                'registration_type':'user_registration'})

    if resp:
        if resp['status'] == "Inactive":
            mongo_db_client.close()
            return -3,""
        else:  
            secret_key = resp['secretkey']
            first_name = resp['firstname']
    
    else:
        mongo_db_client.close()   
        return -2,""

    mongo_db_client.close()
    return first_name, secret_key

########################################################################################################################
def login_admin(request_data):
    login_attributes = ['emailid', 'password'] 

    for attribute in login_attributes:
        if attribute not in request_data:
            return -1,""


    collection = db['user_detail']


    resp = collection.find_one({'emailid': request_data['emailid'], 'password': request_data['password'],
                                'registration_type':'admin_registration'})

    if resp:
        if resp['status'] == "Inactive":
            mongo_db_client.close()
            return -3,""
        else:  
            secret_key = resp['secretkey']
            first_name = resp['firstname']
    
    else:
        mongo_db_client.close()   
        return -2,""

    mongo_db_client.close()
    return first_name, secret_key
########################################################################################################################
def update_token(request_email, request_token):

    collection = db['token_detail']

    resp = collection.find_one(({'emailid': request_email}))

    if resp:
        collection.update_one({'emailid': request_email}, {"$set":{'token': request_token}})
    else:
        collection.insert_one(({'emailid': request_email, 'token': request_token}))

    mongo_db_client.close()
    return 1

########################################################################################################################
def forget_password(request_data):
    if 'emailid' not in request_data:
        return -1
    resp = collection_user.find_one({'emailid': request_data['emailid']})

    if resp:
        secret_key = resp['secretkey']
    else:
        mongo_db_client.close()   
        return -2

    mongo_db_client.close()
    return secret_key

########################################################################################################################
def get_token_process_docs(request_data):

    resp = collection_token.find_one(({'token': request_data['token'],'registration_type':'user_registration'}))
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>",resp)
    if resp:
        email_id = resp['emailid']
        
        resp_new = collection_user.find_one(({'emailid': email_id}))
        secret_key = resp_new['secretkey']
    else:
        mongo_db_client.close()   
        return -2

    return {'emailid': email_id, 'secretkey': secret_key}

########################################################################################################################
def get_token(request_data,registration_type):

    collection = db['token_detail']

    resp = collection.find_one(({'token': request_data['token'],'registration_type':registration_type}))

    if resp:
        email_id = resp['emailid']
        resp_new = collection_user.find_one(({'emailid': email_id}))
        secret_key = resp_new['secretkey']
    else:
        mongo_db_client.close()   
        return -2

    mongo_db_client.close()
    return {'emailid': email_id, 'secretkey': secret_key}

#######################################################################################################################

def get_single_records(emailid,job_id,new_file_name,output_dataframe,calculation_csv_path_new,excel_path,transaction_data,calculation_response,calculation_result_list):
    collection_analysis.insert_one(({'emailid':emailid,'job_id': job_id, 'file_name': new_file_name, 'calculation_csv_path_new': calculation_csv_path_new,
                            'excel_path': excel_path,'calculation_response': str(calculation_response) ,
                            'calculation_result_list':calculation_result_list}))

    collection_job.update_one({'job_id': job_id}, {"$set":{'job_status': "Completed",'excel_path':excel_path,'calculation_csv':calculation_csv_path_new}})
    mongo_db_client.close()
    return 

########################################################################################################################
def logout_user(request_email):
    collection_token.delete_one({'emailid': request_email})
    mongo_db_client.close()

########################################################################################################################

def delete_by_job_id(request_email,job_id):
    resp = collection_job.delete_one({'job_id':job_id})
    mongo_db_client.close()
    return resp

########################################################################################################################

def get_company_name(request_email):

    company_name = collection_user.find_one({'emailid':request_email})
    company_name = company_name['companyname'] 
    mongo_db_client.close()
    return company_name

########################################################################################################################

def long_words(lst,dashboard):
    words = []
    for word in lst:
        if dashboard == 'user':
            word = {key: word[key] for key in word.keys() 
                    & {'bank_name','upload_date_time','job_id','job_status','applicant_id','excel_path'}} 
            words.append(word)
        elif dashboard == 'admin':
            word = {key: word[key] for key in word.keys() 
                    & {'bank_name','upload_date_time','job_id','job_status','emailid','applicant_id','excel_path','document_name'}} 
            words.append(word)
    return words

def user_dashboard_detail(request_email,data):
    response = collection_job.find({'emailid': request_email}, { '_id': 0})
    if response:
        api_response = long_words(response,'user')
        mongo_db_client.close()
        return api_response
    else:
        mongo_db_client.close()
        return -2



########################################################################################################################
def get_application_id_detail(applicant_id,emailid):

    response = collection_job.find_one(({'applicant_id':applicant_id,'emailid':emailid}))
    if response:
        mongo_db_client.close()
        return response
    else:
        mongo_db_client.close()
        return -2
########################################################################################################################
def get_Details_By_ID(request_email, request_jobid):

    response = collection_analysis.find_one({'emailid': request_email, 'job_id': request_jobid}, {'emailid': 0, '_id': 0, 'job_id': 0})
    if response:
        mongo_db_client.close()
        return response
    else:
        mongo_db_client.close()
        return -2

########################################################################################################################

def get_localization_password_status(request_data):
    response = collection_job.find_one({'job_id': request_data['job_id']})

    if response:
        # file_path = response['file_path'] 
        # password = response['password']
        # bank_name = response['bank_name']
        localization_status = response['localization_status']
        readable_status = response['readable_status']
        # try:
        #     response,file_path = check_password_new(file_path)
        #     if response == False:
        #         if password == "undefined" or not password:
        #             status = False
        #         else:
        #             status = get_password_status(password,file_path)
        #         if status == False:
        #             return jsonify({'message': 'File is password protected. Please enter correct password'}),401
        # except:
        #     print(traceback.print_exc())
        #     return jsonify({'message': 'Wrong PDF file Password Entered'}), 401
        # text,word_order = get_document_type(file_path) 
        # localization_status,readable_status = get_localization_status_new(bank_name,file_path)
        collection.update_one({'job_id': request_data['job_id']}, {"$set": {'doc_type': 'Bank Statement'}})
        mongo_db_client.close()
        return [localization_status,readable_status]
    else:
        mongo_db_client.close()
        return -2

########################################################################################################################
def get_localization_details(request_data):
    response = collection_job.find_one({'job_id': request_data['job_id'],'job_status': 'Incomplete'})

    if response:
        file_path = response['file_path']
        doc_type = response['doc_type']
        bank_name = response['bank_name']
        readable_status = response['readable_status']
        print("-------- Input File Name = {} -------".format(file_path))

        try:        
            table_coordinate_list,width, height,reduced_percentage,columns_list = get_bank_statement(file_path,doc_type,bank_name,readable_status)
            NewList1=[]
            for ind_, temp in enumerate(table_coordinate_list):
                keys_needed = ['left', 'top', 'width', 'height']
                table__ = {k:temp[k] for k in keys_needed}
                major_table = {k:temp[k] for k in temp if k not in keys_needed}
                if ind_ == 0:
                    table__['colItem'] = columns_list
                major_table['table_data'] = [table__]
                NewList1.append(major_table)

            table_coordinate_list = NewList1
            collection.update_one({'job_id': request_data['job_id']}, {"$set": {'table_coordinate_list': table_coordinate_list,'width':width,
                                'height':height,'reduced_percentage':reduced_percentage,'columns_list':columns_list}})
            mongo_db_client.close()
            return [table_coordinate_list,width,height]
        except:
            print(traceback.print_exc())
            return -2
    else:
        mongo_db_client.close()
        return -2    

#############################################################################################################################

def get_digitization_details(request_jobid,table_coords):

    response = collection_job.find_one({'job_id': request_jobid})
    if response:
        # data_input = response['table_coordinate_list']
        data_input = table_coords
        file_path = response['file_path']
        readable_status = response['readable_status']
        reduced_percentage = response['reduced_percentage']
        data = get_valid_format(data_input)
        try:
            final_output = extraction_data(data,readable_status,reduced_percentage,file_path)
            collection.update_one({'job_id': request_jobid}, {"$set": {'table_data': final_output}})
            mongo_db_client.close()
            return final_output
        except:
            print(traceback.print_exc())
            return -2
    else:
        mongo_db_client.close()
        return -2  

#########################################################################################################################
def save_digitized_data(request_jobid):
    response = collection_job.find_one({'job_id': request_jobid})

    if response:
        file_path = response['file_path']
        bank_name = response['bank_name']
        table_data = response['table_data']
        
        try:
            output_dataframe,csv_path,bank_type,excel_path,transaction_data = combined_dataframe(bank_name,table_data,file_path)
            final_combined = output_dataframe.to_json(orient='records')
            collection.update_one({'job_id': request_jobid}, {"$set": {'final_combined': final_combined,'csv_path':csv_path,'bank_type':bank_type,'excel_path':excel_path,'transaction_data':transaction_data}})
            mongo_db_client.close()
            return final_combined
        except:
            print(traceback.print_exc())
            return -2
    else:
        mongo_db_client.close()
        return -2  

#########################################################################################################################
def get_calculation_data(request_jobid):

    response = collection_job.find_one({'job_id': request_jobid})

    if response:
        file_path = response['file_path']
        bank_name = response['bank_name']
        bank_type = response['bank_type']
        text = response['text']
        word_order = response['word_order']
        excel_path = response['excel_path']
        emailid = response['emailid']
        transaction_data = response['transaction_data']

        try:
            calculation_response,calculation_csv_path_new,calculation_result_list = get_statement_analysis(excel_path,bank_name,bank_type,file_path,text,word_order)

            response = collection_analysis.find_one({'job_id': request_jobid})

            if not response:
                collection_analysis.insert_one(({'emailid':emailid,'job_id':request_jobid ,'excel_path': excel_path,'file_name':file_path,
                                        'calculation_csv_path_new':calculation_csv_path_new,'calculation_result_list':calculation_result_list,
                                        'calculation_response':str(calculation_response)}))
            else:
                collection_analysis.update_one({'job_id': request_jobid}, {"$set":{'emailid':emailid,'job_id':request_jobid ,'excel_path': excel_path,'file_name':file_path,
                                        'calculation_csv_path_new':calculation_csv_path_new,'calculation_result_list':calculation_result_list,
                                        'calculation_response':str(calculation_response)}})

            collection_job.update_one({'job_id': request_jobid}, {"$set":{'job_status': "Completed",'calculation_csv':calculation_csv_path_new}})
            mongo_db_client.close()
            return [calculation_response,calculation_csv_path_new,calculation_result_list]
        except:
            print(traceback.print_exc())
            return -2
    else:
        mongo_db_client.close()
        return -2  
 


########################################################################################################################

def get_jobid(request_email):
    try:
        response = collection_job.count()
        mongo_db_client.close()
        return response
    except:
        print(traceback.print_exc())
        return -2

########################################################################################################################
def insert_new_job(emailid, job_id, applicant_id, new_file_name):
    try:
        format_date = "%Y-%m-%d %H:%M"
        now_utc = datetime.datetime.now(timezone('UTC'))
        now_asia = now_utc.astimezone(timezone('Asia/Kolkata'))
        upload_date_time = now_asia.strftime(format_date)

        job_details['emailid'] = emailid
        job_details['job_id'] = job_id
        job_details['upload_date_time'] = upload_date_time
        job_details['job_status'] = 'Incomplete'
        job_details['file_path'] = new_file_name
        job_details['applicant_id'] = applicant_id
        collection_job.insert_one(request_data)

        mongo_db_client.close()
        return 0
    except:
        print(traceback.print_exc())
        return -2
    
########################################################################################################################
def insert_job(request_data):
    try:
        collection_job.insert_one(request_data)
        mongo_db_client.close()
        return 0
    except:
        print(traceback.print_exc())
        return -2

########################################################################################################################
def update_jobstatus(request_email, request_jobid, request_status):
    try:
        collection_job.update_one({'emailid': request_email, "job_id": request_jobid}, {"$set": {'job_status': request_status}})
        mongo_db_client.close()
        return 0
    except:
        print(traceback.print_exc())
        return -2
