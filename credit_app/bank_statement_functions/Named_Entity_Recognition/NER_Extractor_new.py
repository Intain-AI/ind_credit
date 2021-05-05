import json
from .Features_For_CRF import sent_to_features
import pickle
from .Functionalities import preprocess,process_input_file,find_coordinates,date_coordinates,account_holder_coordinates,rule_based_coordinates
import traceback
import re
import datefinder
import os
import pandas as pd
date_regex=r'\d{2}\s{0,3}[/-]\s{0,3}\d{2}\s{0,3}[/-]\s{0,3}\d{2,4}'
def assign_value(IOB_tags,classes,label,tag,i,id,logical_id,coordinates,word):
    result={}
    ind=IOB_tags.index(tag[i])
    key=classes[ind]
    l=label[ind] 
    result["coordinates"]=coordinates
    result["label"]=l
    result["value"]=word
    result["varname"]=key    
    result["logical_cell_position"]=logical_id
    result['confidence_score']=100
    result['confidence_score_green']=85
    return(result)
def nerOutput(word,tag,sentences,text_list):
    try:
           IOB_tags=['B_ACC_NUMBER','B_ACC_HOLDER_NAME','B_IFSC_CODE','B_ACC_OPEN_DATE']
           classes=["account_number","account_holder_name","ifsc_code","ac_open_date","joint_holders"]
           label=["Account Number","Account Holder","IFSC Code","Account Open Date","Type of Account"]
           res=[]
           idd=-1
           regex_ifsc = "^[A-Z]{4}0[A-Z0-9]{6}$"
           regex_date=r'\d{2}\s{0,3}[/-]\s{0,3}\d{2}\s{0,3}[/-]\s{0,3}\d{2,4}'          
           extracted_fields=[]       
           while(tag.count("B_ACC_OPEN_DATE")>1):
            i=tag.index("B_ACC_OPEN_DATE")
            del tag[i]
            del word[i]      
           for i in range(len(tag)):
               word[i]=word[i].strip()
               word[i]=preprocess(word[i])
               #print("word",word[i])
               id,logical_id,coordinates=find_coordinates(sentences,text_list,word[i])
              
               if(tag[i]=="B_ACC_NUMBER"):
                   if(word[i].isdigit()):
                       print("acc no",coordinates)
                       result=assign_value(IOB_tags,classes,label,tag,i,id,logical_id,coordinates,word[i])
                       idd=idd+1
                       result['order_id']=idd
                       res.append(result)
               if(tag[i]=="B_ACC_HOLDER_NAME"):
                   idd=idd+1
                   result={}
                   ind=IOB_tags.index(tag[i])
                   key=classes[ind]
                   l=label[ind]     
                   s=""
                   s=s+word[i]
                   for j in range(len(tag)):
                       if(tag[j]=="I_ACC_HOLDER_NAME"):
                           s=s+" "+word[j]
                   result["coordinates"]=coordinates
                   result["label"]=l
                   result["value"]=s
                   result["varname"]=key    
                   result["logical_cell_position"]=logical_id
                   result['confidence_score']=100
                   result['confidence_score_green']=85
                   result['order_id']=idd
                   res.append(result)
               if(tag[i]=="B_IFSC_CODE"):           
                   p = re.compile(regex_ifsc)
                   if(word[i].isalnum()):
                       result=assign_value(IOB_tags,classes,label,tag,i,id,logical_id,coordinates,word[i])
                       idd=idd+1
                       result['order_id']=idd
                       res.append(result)
               if(tag[i]=="B_ACC_OPEN_DATE"):
                   p = re.compile(regex_date)
                   if(re.search(p,word[i])):
                       result=assign_value(IOB_tags,classes,label,tag,i,id,logical_id,coordinates,word[i])
                       idd=idd+1
                       result['order_id']=idd
                       res.append(result)
           for i in range(len(res)):
               extracted_fields.append(res[i]['label'])
           #print("EXTRACTED FIELDS")
           #print(extracted_fields)
           for i in label:
               result={}
               if i not in extracted_fields:
                   ind=label.index(i)
                   result['label']=i
                   result['value']='NA'
                   result["varname"]=classes[ind]
                   result["coordinates"]={"top":10,"left":10,"width":10,"height":10}
                   result['confidence_score']=100
                   result['confidence_score_green']=85
                   idd=idd+1
                   result['order_id']=idd
                   res.append(result)
           #print(len(res))
           return(res)            
   
    except:
        print(traceback.print_exc())
        return []


def correct_date(date_string):
    try:
        matches = datefinder.find_dates(date_string)         
        match=list(matches)
        # print(match[0].strftime("%Y-%m-%d"))   
        return (match[0].strftime("%Y-%m-%d"))
    except:
        return 'NA'
def predict_input(sentences):
    try:
        X_test=[sent_to_features(s,0) for s in sentences]
        with open("credit_app/bank_statement_functions/Named_Entity_Recognition/CRF_model.clf", 'rb') as clf:
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

def ruleBasedNER(result,text_list,data,sentences):
    text=""
    # print("Result",result)
    for i in text_list:
        text=text+' '+(i['text'])
    text=text.lower().replace('(cid:9)','').replace('\\n',' ')
    text=re.sub('[^a-zA-Z0-9/-]',' ',text)
    text=re.sub('\s+',' ',text)
    # print("\ntextttt\n",text)
    Name = ['mr','ms','dear','mrs','name','holder']
    acc_no_list=['account no','account number','account summary','a/c']
    account_opening_date_list=['open date','account statement','transaction period','transaction date','period','between','from']
    months=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec','march','january','february','september']
    month_string='|'.join(months)
    words=text.split()
    dict_bank={}
    for result_dict in result:
        dict_bank[result_dict['varname']]=result_dict['value']
    # print(dict_bank)
    if dict_bank['account_holder_name'].lower()=='name' or dict_bank['account_holder_name'].lower()=='mr' or dict_bank['account_holder_name'].lower()=='mr.' or dict_bank['account_holder_name'].lower()=='mrs.' or dict_bank['account_holder_name'].lower()=='open':
        dict_bank['account_holder_name']='NA'
    if dict_bank['ac_open_date'].lower() in ['a/c','number','open','date','joint']:
        dict_bank['ac_open_date']='NA'
    if dict_bank['ifsc_code'].lower()=='ifsc':
        dict_bank['ifsc_code']='NA'
    if dict_bank['account_number'].lower() in ['a/c','number','account']:
        dict_bank['account_number']='NA'
    ifsc_list  = re.findall(r'[a-zA-Z]{4}[0o][0-9]{6}',text)
    if ifsc_list and dict_bank['ifsc_code']=='NA':
        dict_bank['ifsc_code']=ifsc_list[0].upper()  
    if dict_bank['account_number']=='NA':
        for acc_no_key in acc_no_list:
            z = re.search(acc_no_key, text)
            if z and dict_bank['account_number']=='NA':
                # print("acc no",z)
                search_index=z.start()
                acc_no=re.findall('[0-9]{10,17}',text[search_index:search_index+200])
                if acc_no:
                    dict_bank['account_number']=acc_no[0]

    if dict_bank['ac_open_date']=='NA':
        for element in account_opening_date_list:
            z = re.search(element, text)
            if z and dict_bank['ac_open_date']=='NA':
                # print("acc opening date",z)
                search_index=z.start()
                date_text=text[search_index:search_index+200]
                month_list=re.findall(month_string,date_text)
                # print(date_text)
                if dict_bank['ac_open_date']=='NA':
                    date_search=re.findall(date_regex,date_text)
                    if date_search:
                        # print("date regex",date_search)
                        dict_bank['ac_open_date']=date_search[0]                      
                if month_list and dict_bank['ac_open_date']=='NA':
                    for j in month_list:
                        if dict_bank['ac_open_date']=='NA' and j in words:
                            # print(j,month_list)
                            dates=words[words.index(j)-1:words.index(j)+2]
                            # print(dates)
                            dict_bank['ac_open_date']=' '.join(dates)
    if dict_bank['joint_holders']=='NA':
        joint_index=text.find('joint')
        if joint_index!=-1:
            dict_bank['joint_holders']='Joint Account'
        else:
             dict_bank['joint_holders']='Individual Account'
    
    if dict_bank['account_holder_name']=='NA':
        for element in Name:
            z = re.search(element, text)
            if z and dict_bank['account_holder_name']=='NA':
                # print("account_holder_name",z)
                search_index=z.end()
                person_name=''.join(text[search_index+1:search_index+15])
                # month_list=re.findall(month_string,date_text)
                dict_bank['account_holder_name']=person_name

    for index,word in enumerate(words):
        # print("word",word)
        if word.lower() in Name and dict_bank['account_holder_name']=='NA':
            person_name=words[index+1:index+3]
            person_name=' '.join(person_name)
            # print("person name",person_name)
            if 'branch' not in person_name:
                dict_bank['account_holder_name']=person_name.title()
        if word.lower()[:3] in months and dict_bank['ac_open_date']=='NA':
            date=words[index-1:index+2]
            # print("date final",date)
            dict_bank['ac_open_date']=' '.join(date)
    if dict_bank['ac_open_date']=='NA':
        # print("date full text")
        date_search=re.findall(date_regex,text)
        if date_search:
            # print(date_search)
            dict_bank['ac_open_date']=date_search[0]                      
        else:
            date=correct_date(text)
            dict_bank['ac_open_date']=date
    if dict_bank['account_number']=='NA':
        acc_no=re.findall('[0-9]{10,17}',text)
        if acc_no:
            dict_bank['account_number']=acc_no[0]

 
    #finding coordinates for fields extracted using rule based approach 
    r=rule_based_coordinates(result,dict_bank,sentences,text_list,data)
    return r
def nerMain(data):
    try:
        text_list,sentences,tokens=process_input_file(data)
        word,tag=predict_input(tokens)
        # print(word,tag)
        result=nerOutput(word,tag,sentences,text_list)
        # print("neroutput",result)
        dict_bank={}
        for result_dict in result:
            dict_bank[result_dict['varname']]=result_dict['value']
        # print("NER Output",dict_bank)
        #print(result)
        final_result=ruleBasedNER(result,text_list,text_list,sentences)
        return final_result
    except:
        print(traceback.print_exc())
        return {}

if __name__=="__main__":
    # f = open('/home/credit/ind_credit/credit_app/static/data/input/bank_statement_2/E-HDFC_67/E-HDFC_67.json')
    # df=pd.DataFrame()
    json_dir="/home/credit/JSON_files/"
    for file in os.listdir(json_dir):
    # file="E-SBI_88.pdf.json"
        print(file)
        f = open(json_dir+file) 
        json_data = json.load(f) 
        # text_list,sentences,tokens=process_input_file(json_data)
        # word,tag=predict_input(tokens)
        # result=output(word,tag,sentences,text_list,text_list)
        result = nerMain(json_data)
        print("\n\n",result)
        # dict_bank={}
        # for result_dict in result:
        #     dict_bank[result_dict['varname']]=result_dict['value']
        #     dict_bank['file_name']=file
        # print(dict_bank)
        #     df=df.append(dict_bank,ignore_index=True)
        #     # print(df)
        # df.to_excel("NER_resp.xlsx")
        # print(resp)