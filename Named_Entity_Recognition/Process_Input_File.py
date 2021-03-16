# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 10:48:30 2021

@author: DELL
"""

import pandas as pd
import numpy as np
import glob
import pickle
import json
from XML_Dataframe import xml_dataframe
from Vision_OCR import visionocr
import Features_For_CRF as Features

folder_path="D:/Intain_Technologies_sem/NER/Named Entity Recognition/Test_File"
xml_files = glob.glob(folder_path+'/*.xml') 
logical_cells=pd.DataFrame()
for xml_file_path in xml_files:
    df=xml_dataframe(xml_file_path)
    jpg_file=xml_file_path.split('.')[0]+'.jpg'
    try:
        df_ocr=visionocr(jpg_file)
        for index in range(len(df)):
            x=np.where((df_ocr['x1']<=df['xmax'][index]) & (df_ocr['x0']>=df['xmin'][index]) & (df_ocr['y2']<=df['ymax'][index]) & (df_ocr['y0']>=df['ymin'][index]))
            logical_cell_text=' '.join(df_ocr.loc[x[0].tolist()]['Token'])
            df.at[index,'sentence']=logical_cell_text
        logical_cells=logical_cells.append(df)
        print("finished",jpg_file)
    except:
        print(xml_file_path)
logical_cells.to_excel('logical_cell.xlsx', engine='xlsxwriter')
df = pd.read_excel("logical_cell.xlsx")
df = df.assign(sentence=df['sentence'].str.split(' ')).explode('sentence')
with pd.ExcelWriter('logical_cell.xlsx', engine='openpyxl', mode='a') as writer:  
    df.to_excel(writer, sheet_name = 'split')
df=pd.read_excel("logical_cell.xlsx",sheet_name="split")

sentences= Features.getsentence(df,0)
X_test=[Features.sent2features(s,0) for s in sentences]
with open("CRF_classifier.clf", 'rb') as clf:
        crf_classifier = pickle.load(clf)
prediction=crf_classifier.predict(X_test)
'''
words=[]
for i in range(len(sentences)):
    for j in range(len(sentences[i])):
        words.append(sentences[i][j])
      '''
tag=[]
word=[]
for i in range(len(sentences)):
    for j in range(len(sentences[i])):
      if(prediction[i][j]!='O'):
        word.append(sentences[i][j])
        tag.append(prediction[i][j])
def display(B_tag,I_tag):
  string=""
  #print(B_tag,I_tag)
  for i in tag:
    if(i==B_tag):
      index= [index for index, element in enumerate(tag) if element ==I_tag]
   #   print(index)
      for j in index:
        string=string+" "+word[j]
      return(string)
  return(0)
fields=['B_ACC_NUMBER', 'I_ACC_NUMBER', 'B_ACC_HOLDER_NAME', 'I_ACC_HOLDER_NAME', 'B_IFSC_CODE','I_IFSC_CODE', 'B_EMAIL_ID','I_EMAIL_ID',  'B_ACC_OPEN_DATE', 'I_ACC_OPEN_DATE', 'B_JOINT_HOLDERS', 'I_JOINT_HOLDERS']
classes=classes=["Account Number","Account Holder Name","IFSC Code","Email ID","Account Open Date","Joint Holders"]
i=0
keys=[]
values=[]
while(i<12):
  words=display(fields[i],fields[i+1])
  if(words!=0):
    keys.append(classes[int(i/2)])
    values.append(words)
  i=i+2



print(json.dumps([{'key':i, 'value': j} for i,j in zip(keys, values)]))
