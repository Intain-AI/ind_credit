from pymongo import MongoClient
import traceback
import os,json
from flask import jsonify
from config import IND_EMAIL,IND_PASSWD,BASE_URL
from config import  IND_CREDIT_MONGODB_URL,IND_CREDIT_MONGODB_PORT,IND_CREDIT_MONGODB_NAME
import datetime
import time
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from uuid import uuid4


# from datetime import datetime
from pytz import timezone

uri = "mongodb://{}:{}/{}".format(IND_CREDIT_MONGODB_URL, IND_CREDIT_MONGODB_PORT,IND_CREDIT_MONGODB_NAME)
# uri = "mongodb+srv://12345:12345@cluster0.thhvq.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
mongo_db_client = MongoClient(uri)
db = mongo_db_client[IND_CREDIT_MONGODB_NAME]

collection_job = db['job_detail']
collection_token = db['token_detail']
collection_extracted = db['extracted_data']
collection_validated = db["validated_data"]

########################################################################################################################
def delete_null_job(request_email):
    
    collection_job.delete_many(
        {
            'emailid': request_email, 
            'job_status': 'NULL'
        })
    mongo_db_client.close()


#######################################################################################################################

def delete_by_job_id(request_email,job_id):
    resp = collection_job.delete_one({'job_id':job_id})
    mongo_db_client.close()
    return resp

########################################################################################################################


def userDashboardDetail(request_email):
    #pprint.pprint(request_data)

    job_response = collection_job.find(
        {
            'emailid': request_email
        }, {
            '_id': 0,
            "job_size" : 0,
            'document_name':0,
            'folder_path' :0,
            'json_file_path':0,
            'excel_file_path':0
        })

    if job_response:
        api_response = []
        for row in job_response:
            if row['job_status'] == 'NULL':
                row['job_status'] = 'In Process'

            api_response.append(row)
        mongo_db_client.close()
        return api_response
    else:
        mongo_db_client.close()
        return -2

########################################################################################################################
def ui_validation(request_email,job_id):
    #pprint.pprint(request_data)

    job_response = collection_job.find_one(
        {
            'emailid': request_email,
            'job_id':job_id
        }, {
            '_id': 0,
            "job_size" : 0,
            'document_name':0,
        })
    print(":::::::::::::::::;",job_response)
    if job_response:
        mongo_db_client.close()
        return job_response
    else:
        mongo_db_client.close()
        return -2

def review_document(request_email,job_id,filename):
    #pprint.pprint(request_data)

    job_response = collection_job.find_one(
        {
            'emailid': request_email,
            'job_id':job_id,
            'filename':filename
        }, {
            '_id': 0,
            "job_size" : 0,
            'document_name':0,
        })
    print(":::::::::::::::::;",job_response)
    if job_response:
        mongo_db_client.close()
        return job_response
    else:
        mongo_db_client.close()
        return -2
########################################################################################################################
def digitize_document(request_email,job_id):
    #pprint.pprint(request_data)

    job_response = collection_job.find_one(
        {
            'emailid': request_email,
            'job_id':job_id
        }, {
            '_id': 0,
            "job_size" : 0,
            'document_name':0,
        })
    
    if job_response:  
        mongo_db_client.close()
        return (job_response['folder_path'],job_response['excel_file_path'])
    else:
        mongo_db_client.close()
        return -2

########################################################################################################################
def get_excel(request_email,job_id):
    try:

        job_response = collection_job.find_one(
            {
                'emailid': request_email,
                'job_id':job_id
            }, {
                '_id': 0,
                "job_size" : 0,
                'document_name':0,
            })
        
        if job_response:  
            mongo_db_client.close()
            excel_file_path = job_response['final_excel_path']
            return (excel_file_path)
        else:
            mongo_db_client.close()
            return -2

    except:
        mongo_db_client.close()
        return -2


################################################################
def get_jobid(request_email):
    try:
        response = collection_job.count()
        mongo_db_client.close()
        return str(response)
    except:
        print(traceback.print_exc())
        return -2

########################################################################################################################
# def insert_new_job(emailid, job_id, applicant_id, new_file_name):
#     try:
#         format_date = "%Y-%m-%d %H:%M"
#         now_utc = datetime.datetime.now(timezone('UTC'))
#         now_asia = now_utc.astimezone(timezone('Asia/Kolkata'))
#         upload_date_time = now_asia.strftime(format_date)

#         job_details['emailid'] = emailid
#         job_details['job_id'] = job_id
#         job_details['upload_date_time'] = upload_date_time
#         job_details['job_status'] = 'Incomplete'
#         job_details['file_path'] = new_file_name
#         job_details['applicant_id'] = applicant_id
#         collection_job.insert_one(request_data)

#         mongo_db_client.close()
#         return 0
#     except:
#         print(traceback.print_exc())
#         return -2

########################################################################################################################
def update_job_details(excel_file_path,response,job_id,message):
    try:
        collection_job.update_one({'job_id': job_id}, {"$set":{'job_status':message,'excel_file_path':excel_file_path,'response':response}})
        mongo_db_client.close()
        return 
    except:
        print(traceback.print_exc())
        return -2

def insert_textfield(job_id,textfield_list):
    try:
        collection_job.update_one({'job_id': job_id}, {"$set":{'textfields':textfield_list}})
        mongo_db_client.close()
        return 
    except:
        print(traceback.print_exc())
        return -2

def get_textfields(job_id):
    #pprint.pprint(request_data)

    job_response = collection_job.find_one(
        {
            'job_id':job_id
        }, {
            '_id': 0,
            "job_size" : 0,
            'document_name':0,
        })
    print(":::::::::::::::::;",job_response)
    if job_response:
        mongo_db_client.close()
        return job_response['textfields']
    else:
        mongo_db_client.close()
        return -2

########################################################################################################################
def update_calculation_job(excel_file_path,job_id,final_excel_path):
    try:
        collection_job.update_one({'job_id': job_id}, {"$set":{'job_status': "Processed",'excel_file_path':excel_file_path,'final_excel_path':final_excel_path}})
        mongo_db_client.close()
        return 
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


def addRecord_Db(file_json,job_id,email_id):
    '''
    Input
    job_id >> Int
    file_json >> dict
    email_id >> string
    
    Output >> status 0 for success and -2 for failure
    '''
    # if not isinstance(file_json, dict):
        # raise TypeError(f"file_json must be a Dict!! found {type(file_json)}")

    try:
        query={}
        query['job_id']=job_id
        query['email_id']=email_id
        
        date_format = "%Y-%m-%d %H:%M"
        now_utc = datetime.datetime.now(timezone('UTC'))
        now_asia = now_utc.astimezone(timezone('Asia/Kolkata'))
        query['upload_dateTime'] = now_asia.strftime(date_format)
        
        collection_extracted.update_one(query,{'$set':{"data":file_json}},upsert=True)
        collection_validated.update_one(query,{'$set':{"data":file_json}},upsert=True)
        mongo_db_client.close()
        return 0
    except:
        print(traceback.print_exc())
        return -2


def updateValidatedData_Db(file_json,job_id,email_id):
    '''
    Input
    job_id >> Int
    file_json >> dict
    email_id >> string
    
    Output >> status 0 for success and -2 for failure
    '''

    if not isinstance(file_json, dict):
        raise TypeError(f"file_json must be a Dict {type(file_json)}")

    try:
        query={}
        query['job_id']=job_id
        query['email_id']=email_id

        date_format = "%Y-%m-%d %H:%M"
        now_utc = datetime.datetime.now(timezone('UTC'))
        now_asia = now_utc.astimezone(timezone('Asia/Kolkata'))
        updated_dateTime = now_asia.strftime(date_format)
        collection_validated.update_one(query,{'$set':{'data':file_json,'updated_dateTime':updated_dateTime}},upsert=True)
        mongo_db_client.close()
        return 0
    except:
        print(traceback.print_exc())
        return -2


def deleteRecord_Db(uid, collection):
    '''
    Input
    uid >> String
    collection >> database collection
    
    Output >> status 1 for success and 0 for failure
    '''
    if not isinstance(uid, str):
        raise TypeError(f"uid must be a string!! found {type(uid)}")

    try:
        query = {}
        query["uid"] = uid
        collection.delete_one(query)
        return {"status":1}
    except:
        print(traceback.print_exc())
        return {"status":0}


def getValidatedData_Db(email_id,job_id):
    '''
    Input
    uid >> String
    collection >> database collection
    
    Output
    data >> json of data 
    status 1 for success and 0 for failure
    '''
    try:
        query={}
        query['job_id']=job_id
        query['email_id']=email_id
        response = collection_validated.find_one(query)
        return {"data":response['data'],"status":1}

    except:
        print(traceback.print_exc())
        return {"data":{},"status":0}