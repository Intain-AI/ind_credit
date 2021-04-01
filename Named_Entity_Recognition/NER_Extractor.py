
import json
import Features_For_CRF as Features
import pickle
from Functionalities import preprocess,process_input_file,find_coordinates

def output(word,tag,sentences,text_list):
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
           re.append(result)
   
   return(re)

def predict_input(sentences):
    X_test=[Features.sent_to_features(s,0) for s in sentences]
    with open("CRF_Classifier.clf", 'rb') as clf:
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

def main():
   f = open('E-SBI_2.json',) 
   data = json.load(f) 
   text_list,sentences,tokens=process_input_file(data)
   word,tag=predict_input(tokens)
   result=output(word,tag,sentences,text_list)
   print(result)
  
   
    
if __name__=="__main__":
    main()