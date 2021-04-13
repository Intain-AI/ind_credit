
import json
from .Features_For_CRF import sent_to_features
import pickle
from .Functionalities import preprocess,process_input_file,find_coordinates
import traceback
import re
import datefinder

def nerOutput(word,tag,sentences,text_list):
    try:
        IOB_tags=['B_ACC_NUMBER', 'I_ACC_NUMBER', 'B_ACC_HOLDER_NAME', 'I_ACC_HOLDER_NAME', 'B_IFSC_CODE','I_IFSC_CODE', 'B_ACC_OPEN_DATE', 'I_ACC_OPEN_DATE', 'B_JOINT_HOLDERS', 'I_JOINT_HOLDERS']
        classes=["account_number","account_holder_name","ifsc_code","ac_open_date","joint_holders"]
        label=["Account Number","Account Holder","IFSC Code","Account Opening Date","Type of Account"]

        re=[]
        extracted_fields=[]
        for i in range(len(tag)):
            # print(tag[i])
            result={}
            if tag[i] in IOB_tags:
                ind=IOB_tags.index(tag[i])
                key=classes[int(ind/2)]
                l=label[int(ind/2)]
                id,logical_id,coordinates=find_coordinates(sentences,text_list,word[i])
                result["coordinates"]=coordinates
                result["label"]=l
                result["value"]=word[i]
                result["varname"]=key    
                result["logical_cell_position"]=logical_id
                # if result['varname'] 
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

def correct_date(date_string):
    try:
        matches = datefinder.find_dates(date_string)         
        match=list(matches)
        print(match[0].strftime("%Y-%m-%d"))   
        return (match[0].strftime("%Y-%m-%d"))
    except:
        return 'NA'
def predict_input(sentences):
    try:
        X_test=[sent_to_features(s,0) for s in sentences]
        with open("credit_app/bank_statement_functions/Named_Entity_Recognition/CRF_Classifier.clf", 'rb') as clf:
        # with open("CRF_Classifier.clf", 'rb') as clf:
            crf_classifier = pickle.load(clf)
        prediction=crf_classifier.predict(X_test)
        tag=[]
        word=[]
    
        for i in range(len(sentences)):
            for j in range(len(sentences[i])):
                if prediction[i][j]!='O' and prediction[i][j] not in tag:
                    word.append(sentences[i][j])
                    tag.append(prediction[i][j])

        return(word,tag)
    except:
        print(traceback.print_exc())
        return ([],[])

def ruleBasedNER(result,text_list):
    text=""
    print("Result",result)
    for i in text_list:
        text=text+' '+(i['text'])
    # print("\n\n\ntextttt",text)
    text=text.lower().replace('(cid:9)','').replace('\\n',' ')
    text=re.sub('[^a-zA-Z0-9/-]',' ',text)
    text=re.sub('\s+',' ',text)
    Name = ['mr','ms','dear','mrs','name']
    acc_no_list=['account no','account number']
    months=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec','march','january','february','september']
    words=text.split()
    dict_bank={}
    for result_dict in result:
        dict_bank[result_dict['varname']]=result_dict['value']
    # print(dict_bank)
    for word in words:
        if word.lower() in Name and dict_bank['account_holder_name']=='NA':
            person_name=words[words.index(word)+1:words.index(word)+3]
            dict_bank['account_holder_name']=(' '.join(person_name)).title()
        if word.lower()[:3] in months and dict_bank['ac_open_date']=='NA':
            date=words[words.index(word)-1:words.index(word)+2]
            dict_bank['ac_open_date']=' '.join(date)
        month_string='|'.join(months)
    i=text.find('account statement')
    if i!=-1:
        print(text[i:i+200])
        date=correct_date(text[i:i+200])
        if date=='NA':
            month_list=re.findall(month_string,text[i:i+200].lower())
            print("*******month list",month_list,text[i:i+200].lower())
            if month_list and dict_bank['ac_open_date']=='NA':
                for j in month_list:
                    # print(j)
                    if dict_bank['ac_open_date']=='NA':
                        try:
                            dates=words[words.index(month_list[j])-1:words.index(month_list[j])+2]
                            print(dates)
                            dict_bank['ac_open_date']=' '.join(dates)
                        except:
                            pass
        else:
            dict_bank['ac_open_date']=date
    ifsc_list  = re.findall(r'[a-zA-Z]{4}[0o][0-9]{6}',text)
    if ifsc_list:
        dict_bank['ifsc_code']=ifsc_list[0].upper()  
    for word in acc_no_list:
        if dict_bank['account_number']=='NA':
            i=text.lower().find(word)
            if i!=-1:
                acc_no=re.findall('[0-9]{11,17}',text[i:i+200])
                if acc_no:
                    # print(acc_no[0])  
                    dict_bank['account_number']=acc_no[0]
    if dict_bank['joint_holders']=='NA':
        dict_bank['joint_holders']='Individual Account'
    if dict_bank['ac_open_date']=='NA':
        date=correct_date(text)
        dict_bank['ac_open_date']=date
    print(dict_bank)
    for result_dict in result:
        result_dict['value']=dict_bank[result_dict['varname']]
    return result
def nerMain(data):
    try:
        text_list,sentences,tokens=process_input_file(data)
        word,tag=predict_input(tokens)
        # print(word,tag)
        result=nerOutput(word,tag,sentences,text_list)
        final_result=ruleBasedNER(result,text_list)
        return final_result
    except:
        print(traceback.print_exc())
        return {}

    
if __name__=="__main__":
    # f = open('/home/credit/ind_credit/credit_app/static/data/input/bank_statement_2/E-HDFC_67/E-HDFC_67.json')
    f = open('/home/credit/ind_credit/Response.json') 
    json_data = json.load(f) 
    resp = nerMain(json_data)
    print(resp)