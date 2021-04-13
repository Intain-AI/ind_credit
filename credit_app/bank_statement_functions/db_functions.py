from pymongo import MongoClient
import uuid
import traceback

def addRecord_Db(file_json, collection):
    '''
    Input
    file_json >> dict
    collection >> database collection
    
    Output
    fileId >> unique id assigned for each file.
    status >> 1 for success and 0 for failure
    '''
    if not isinstance(file_json, dict):
        raise TypeError(f"file_json must be a Dict!! found {type(file_json)}")

    try:
        query={}
        file_id = str(uuid.uuid4())
        query['uid']=str(file_id)
        collection.update_one(query,{'$set':file_json},upsert=True)
        return {"fileId":file_id, "status":1}
    except:
        print(traceback.print_exc())
        return {"fileId":"", "status":0}


def updateRecord_Db(uid, file_json, collection):
    '''
    Input
    uid >> String
    file_json >> dict
    collection >> database collection
    
    Output
    status 1 for success and 0 for failure
    '''
    if not isinstance(uid, str):
        raise TypeError(f"uid must be a string!! found {type(uid)}")

    if not isinstance(file_json, dict):
        raise TypeError(f"file_json must be a Dict {type(file_json)}")

    try:
        query = {}
        query["uid"] = uid
        collection.update_one(query,{'$set':file_json},upsert=True)
        return {"status":1}
    except:
        print(traceback.print_exc())
        return {"status":0}


def deleteRecord_Db(uid, collection):
    '''
    Input
    uid >> String
    collection >> database collection
    
    Output
    status 1 for success and 0 for failure
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


def getRecord_Db(uid, collection):
    '''
    Input
    uid >> String
    collection >> database collection
    
    Output
    data >> dict of data 
    status 1 for success and 0 for failure
    '''
    if not isinstance(uid, str):
        raise TypeError(f"uid must be a string!! found {type(uid)}")

    try:
        query = {}
        query["uid"] = uid
        data = collection.find_one(query)
        return {"data":data,"status":1}
    except:
        print(traceback.print_exc())
        return {"data":{},"status":0}