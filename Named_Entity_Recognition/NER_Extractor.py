
import json
import Features_For_CRF as Features
import pickle
def output(word,tag):
   IOB_tags=['B_ACC_NUMBER', 'I_ACC_NUMBER', 'B_ACC_HOLDER_NAME', 'I_ACC_HOLDER_NAME', 'B_IFSC_CODE','I_IFSC_CODE', 'B_EMAIL_ID','I_EMAIL_ID',  'B_ACC_OPEN_DATE', 'I_ACC_OPEN_DATE', 'B_JOINT_HOLDERS', 'I_JOINT_HOLDERS']
   classes=["Account_Number","Account_Holder_Name","IFSC_Code","Email_ID","Account_Open_Date","Joint_Holders"]
   result={}
   for i in range(len(tag)):
       ind=IOB_tags.index(tag[i])
       key=classes[int(ind/2)]
       result[key]=word[i]
   return(result)
def predict_input(sentences):
    X_test=[Features.sent_to_features(s,0) for s in sentences]
    with open("/home/credit/ind_credit/Named_Entity_Recognition/CRF_Classifier.clf", 'rb') as clf:
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
    f = open('/home/credit/ind_credit/credit_app/static/data/input/bank_statement_232/E-HDFC_1/E-HDFC_1.json',) 
    data = json.load(f) 
    for value in data['result'].items():
        text_list=data['result']['Page_1']['digitized_details']['logical_cells']
    sentences=[]
    for i in range(len(text_list)):
        sentences.append(text_list[i]["token"])
    sent=[]
    for i in range(len(sentences)):
        tokens=[]
        for j in range(len(sentences[i])):
            tokens.append(sentences[i][j]['text'])
        sent.append(tokens)
    print(sent)


  
    word,tag=predict_input(sent)
    result=output(word,tag)
    print(result)
   
    
if __name__=="__main__":
    main()