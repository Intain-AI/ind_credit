
import json
import Features_For_CRF as Features
import pickle
from Functionalities import preprocess,process_input_file,find_coordinates
import re
import pandas as pd
import os
def output(word,tag,sentences,text_list,data):
   IOB_tags=['B_ACC_NUMBER','B_ACC_HOLDER_NAME','B_IFSC_CODE','B_ACC_OPEN_DATE']
   classes=["account_number","account_holder_name","ifsc_code","ac_open_date","type_of_account"]
   label=["Account Number","Account Holder","IFSC Code","Account Open Date","Joint Holders"]
   res=[]
  
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
       print(word[i])
       id,logical_id,coordinates=find_coordinates(sentences,text_list,word[i])
       result={}
       if(tag[i]=="B_ACC_NUMBER"):
           ind=IOB_tags.index(tag[i])
           key=classes[ind]
           l=label[ind]
       
           if(word[i].isdigit()):
               result["coordinates"]=coordinates
               result["label"]=l
               result["value"]=word[i]
               result["varname"]=key    
               result["logical_cell_position"]=logical_id
               res.append(result)
       if(tag[i]=="B_ACC_HOLDER_NAME"):
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
           res.append(result)
       if(tag[i]=="B_IFSC_CODE"):
        
           ind=IOB_tags.index(tag[i])
           key=classes[ind]
           l=label[ind]
       
           p = re.compile(regex_ifsc)
           if(word[i].isalnum()):
               result["coordinates"]=coordinates
               result["label"]=l
               result["value"]=word[i]
               result["varname"]=key    
               result["logical_cell_position"]=logical_id
               res.append(result)
       if(tag[i]=="B_ACC_OPEN_DATE"):
           p = re.compile(regex_date)
           ind=IOB_tags.index(tag[i])
           key=classes[ind]
           l=label[ind]
       
           if(re.search(p,word[i])):
               result["coordinates"]=coordinates
               result["label"]=l
               result["value"]=word[i]
               result["varname"]=key    
               result["logical_cell_position"]=logical_id
               res.append(result)
   for i in range(len(res)):
       extracted_fields.append(res[i]['label'])
       
   text=""
    # print("Result",result)
   for i in text_list:
        text=text+' '+(i['text'])
   text=text.lower().replace('(cid:9)','').replace('\\n',' ')
   text=re.sub('[^a-zA-Z0-9/-]',' ',text)
   ifsc_listtext=re.sub('\s+',' ',text)
   print("\ntextttt\n",text)
   Name = ['mr','ms','dear','mrs','name','holder']
   acc_no_list=['account no','account number','account summary','a/c']
   account_opening_date_list=['open date','account statement','transaction period','transaction date','period','between','from']
   months=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec','march','january','february','september']
   month_string='|'.join(months)
   words=text.split()
  
   for i in label:
       result={}
       if i not in extracted_fields:
           print("unextracted fields",i)
           if(i=="IFSC Code"):
               text_ifsc=text
               ifsc_list  = re.findall(r'[a-zA-Z]{4}[0o][0-9]{6}',text_ifsc)
               print("ifsc_list",ifsc_list)
               if len(ifsc_list)>=1:
                    ifsc=ifsc_list[0].upper()  
                    ifsc=ifsc.strip()
                    print(ifsc)
                    id,logical_id,coordinates=find_coordinates(sentences,text_list,ifsc)
                    ind=label.index(i)
                    result["coordinates"]=coordinates
                    result['label']=i
                    result['value']=ifsc
                    result["varname"]=classes[ind]
                    result["logical_cell_position"]=logical_id
                    res.append(result)
           if(i=="Account Holder"):
                person_name=''
                text_name=text
                for element in Name:
                    z = re.search(element, text_name)
                    if(z):
                        search_index=z.end()
                        person_name=''.join(text[search_index+1:search_index+15])
                        print("person name",person_name)
                #id,logical_id,coordinates=find_coordinates(sentences,text_list,ifsc)
                ind=label.index(i)
                coordinates={}
                if person_name!='':
                    temp=person_name.split(' ')
                    text_name=text
                    for t in temp:
                        for i in range(0,len(data)):
                            for j in range(0,len(data[i]['token'])):
                                text_name=data[i]['token'][j]['text']
                                text_name=text_name.strip()
                                text_name=preprocess(text_name)
                                #print(text)
                                if (t).lower()==text_name.lower():
                                    top = data[i]['token'][j]['top']
                                    left = data[i]['token'][j]['left']
                                    width = data[i]['token'][j]['width']
                                    height = data[i]['token'][j]['height']
                                    #coordinates={"top":top,"left":left,"width":width,"height":height}
                                    coordinates[str(t)]=[left,height,top,width]
                    print(coordinates)
                    result['label']=i
                    result['value']=person_name
                    result["varname"]=classes[ind]
                    res.append(result)
           if(i=="Account Number"):
               text_number=text
               for acc_no_key in acc_no_list:
                   z = re.search(acc_no_key, text_number)
                   if(z):
                        search_index=z.start()
                        acc_no=re.findall('[0-9]{10,17}',text_number[search_index:search_index+200])
                        print(acc_no[0])
                        id,logical_id,coordinates=find_coordinates(sentences,text_list,acc_no[0])
                        ind=label.index(i)
                        result["coordinates"]=coordinates
                        result['label']=i
                        result['value']=acc_no[0]
                        result["varname"]=classes[ind]
                        result["logical_cell_position"]=logical_id
                        res.append(result)
           if(i=="Joint Holders"):
               ind=label.index(i)
               result['label']=i
               joint_index=text.find('joint')
               if joint_index!=-1:
                   result['value']='Joint Account'
               else:
                   result['value']='Individual Account'
               result["varname"]=classes[ind]  
               res.append(result)
   print(len(res))
   return(res)
   
    
      
      

def predict_input(sentences):
    X_test=[Features.sent_to_features(s,0) for s in sentences]
    with open("CRF_model.clf", 'rb') as clf:
        crf_classifier = pickle.load(clf)
    
    prediction=crf_classifier.predict(X_test)
    tag=[]
    word=[]
    print(prediction)
    for i in range(len(sentences)):
        for j in range(len(sentences[i])):
          if(prediction[i][j]!='O'):
            word.append(sentences[i][j])
            tag.append(prediction[i][j])
   
    return(word,tag)

def main():
   
       f = open('E-ALLHABAD_5.json',) 
       data = json.load(f) 
       text_list,sentences,tokens=process_input_file(data)
       word,tag=predict_input(tokens)
       result=output(word,tag,sentences,text_list,text_list)
       print(result)
    
if __name__=="__main__":
    # f = open('/home/credit/ind_credit/credit_app/static/data/input/bank_statement_2/E-HDFC_67/E-HDFC_67.json')
    df=pd.DataFrame()
    json_dir="/home/credit/JSON_files/"
    for file in os.listdir(json_dir):
    # file="bob_pre1.pdf.json"
        print(file)
        f = open(json_dir+file) 
        json_data = json.load(f) 
        text_list,sentences,tokens=process_input_file(json_data)
        word,tag=predict_input(tokens)
        result=output(word,tag,sentences,text_list,text_list)
        print(result)
        dict_bank={}
        for result_dict in result:
            dict_bank[result_dict['varname']]=result_dict['value']
            dict_bank['file_name']=file
        print(dict_bank)
        df=df.append(dict_bank,ignore_index=True)
        # print(df)
    df.to_excel("NER_resp.xlsx")
    # print(resp)