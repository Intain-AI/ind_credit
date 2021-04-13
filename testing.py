from pymongo import MongoClient
import traceback

from credit_app.bank_statement_functions import calculations





if __name__ == "__main__":
    uri = "mongodb+srv://12345:12345@cluster0.thhvq.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    mongo_db_client = MongoClient(uri)
    db = mongo_db_client["ind_credit_db"]
    collection_extracted = db['extracted_data']
    collection_validated = db["validated_data"]

    # icici = collection_extracted.find_one({"job_id":"IN_4"})
    # kotak = collection_extracted.find_one({"job_id":"IN_5"})
    bandhan = collection_extracted.find_one({"job_id":"IN_6"})

    data = bandhan["data"]
    resp = calculations.extraction_results(data)
    print(resp)