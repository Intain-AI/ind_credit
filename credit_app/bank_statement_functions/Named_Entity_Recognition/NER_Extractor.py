
import json
from .Features_For_CRF import sent_to_features
import pickle
from .Functionalities import preprocess,process_input_file,find_coordinates
import traceback

def nerOutput(word,tag,sentences,text_list):
    try:
        IOB_tags=['B_ACC_NUMBER', 'I_ACC_NUMBER', 'B_ACC_HOLDER_NAME', 'I_ACC_HOLDER_NAME', 'B_IFSC_CODE','I_IFSC_CODE', 'B_EMAIL_ID','I_EMAIL_ID',  'B_ACC_OPEN_DATE', 'I_ACC_OPEN_DATE', 'B_JOINT_HOLDERS', 'I_JOINT_HOLDERS']
        classes=["account_number","account_holder_name","ifsc_code","email_id","ac_open_date","joint_holders"]
        label=["Account Number","Account Holder","IFSC Code","Email ID","Account Open Date","Joint Holders"]

        re=[]
        extracted_fields=[]
        for i in range(len(tag)):
            result={}
            ind=IOB_tags.index(tag[i])
            key=classes[int(ind/2)]
            l=label[int(ind/2)]
            id,logical_id,coordinates=find_coordinates(sentences,text_list,word[i])
            result["coordinates"]=coordinates
            result["label"]=l
            result["value"]=word[i]
            result["varname"]=key    
            result["logical_cell_position"]=logical_id
            re.append(result)

        for i in range(len(re)):
            extracted_fields.append(re[i]['label'])
            
        for i in label:
            result={}
            if i not in extracted_fields:
                ind=label.index(i)
                result['label']=i
                result['value']='NA'
                result["varname"]=classes[ind]
                result["coordinates"]={"top":10,"left":10,"width":10,"height":10}
                result["logical_cell_position"]=0
                re.append(result)
        return re
    except:
        print(traceback.print_exc())
        return []

def predict_input(sentences):
    try:
        X_test=[sent_to_features(s,0) for s in sentences]
        with open("credit_app/bank_statement_functions/Named_Entity_Recognition/CRF_Classifier.clf", 'rb') as clf:
            crf_classifier = pickle.load(clf)
        prediction=crf_classifier.predict(X_test)
        tag=[]
        word=[]
    
        for i in range(len(sentences)):
            for j in range(len(sentences[i])):
                if(prediction[i][j]!='O'):
                    word.append(sentences[i][j])
                    tag.append(prediction[i][j])

        return(word,tag)
    except:
        print(traceback.print_exc())
        return ([],[])

def nerMain(data):
    try:
        text_list,sentences,tokens=process_input_file(data)
        word,tag=predict_input(tokens)
        result=nerOutput(word,tag,sentences,text_list)
        return result
    except:
        print(traceback.print_exc())
        return {}

    
if __name__=="__main__":
    # f = open('/home/credit/ind_credit/credit_app/static/data/input/bank_statement_2/E-HDFC_67/E-HDFC_67.json')
    f = open('/home/credit/ind_credit/credit_app/static/data/input/bank_statement_2/E-HDFC_67/E-HDFC_67.json') 
    json_data = json.load(f) 
    resp = nerMain(json_data)
    print(resp)