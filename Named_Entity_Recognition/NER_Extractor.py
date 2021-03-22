# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 15:14:28 2021

@author: DELL
"""
import json
from Output_of_NER import output
import Features_For_CRF as Features
import pickle

def predict_input(sentences):
    X_test=[Features.sent_to_features(s,0) for s in sentences]
    with open("CRF_classifier.clf", 'rb') as clf:
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
   f = open('E-HDFC_17.json',) 
   data = json.load(f) 
  
   for value in data['result'].items():
        text_list=data['result']['Page_1']['digitized_details']['logical_cells']
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

   f.close() 
  
   word,tag=predict_input(sent)
   result=output(word,tag)
   print(result)
    
if __name__=="__main__":
    main()