# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 15:20:06 2021

@author: DELL
"""

def find_tags(B_tag,I_tag,tag,word):
  string=""
  for i in tag:
    if(i==B_tag):
      index= [index for index, element in enumerate(tag) if element ==I_tag]
      for j in index:
        string=string+" "+word[j]
      return(string)
  return(0)
result={}
def output(word,tag):
    IOB_tags=['B_ACC_NUMBER', 'I_ACC_NUMBER', 'B_ACC_HOLDER_NAME', 'I_ACC_HOLDER_NAME', 'B_IFSC_CODE','I_IFSC_CODE', 'B_EMAIL_ID','I_EMAIL_ID',  'B_ACC_OPEN_DATE', 'I_ACC_OPEN_DATE', 'B_JOINT_HOLDERS', 'I_JOINT_HOLDERS']
    classes=["Account_Number","Account_Holder_Name","IFSC_Code","Email_ID","Account_Open_Date","Joint_Holders"]
    i=0
 
    while(i<12):
      words=find_tags(IOB_tags[i],IOB_tags[i+1],tag,word)
      if(words!=0):
        result[classes[int(i/2)]]=words
       
      i=i+2
    return(result)
  
