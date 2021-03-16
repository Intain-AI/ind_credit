# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 10:27:12 2021

@author: DELL
"""
import re

def getsentence(data,flag):
    if(flag==1):
        agg_func = lambda s: [(w,t) for w, t in zip(s['sentence'].values.tolist(),s['Annotation'].values.tolist())]
    else:
        agg_func=lambda s:s['sentence'].values.tolist()
    grouped = data.groupby('Unnamed: 0').apply(agg_func)
    sentences = [s for s in grouped]
    return(sentences)          

   
def word_to_features(sent, i,f):
    if(f==1):
        word = str(sent[i][0])
    if(f==0):
        word = str(sent[i])

    features = {
        'bias': 1.0,
        'word.lower()': word.lower() if word.isalpha() else word,
        'word.isupper()': word.isupper(),
        'word.istitle()': word.istitle(),
        'word.isdigit()': word.isdigit(),
        'word.isalnum()': word.isalnum(),
        'word.isifsc()': bool(re.match("^[A-Z]{4}0[A-Z0-9]{6}$",word)),
        'word.isemail()': bool(re.match("^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$",word)),
        'word.digitcount()': len([x for x in word if x.isdigit()]),
        'word.isdate()':"True" if re.search(r'\d{2}/\d{2}/\d{4}', word)==None else "False",
        

    }
   
    if i > 0:
        word1 = str(sent[i-1][0])
       
        features.update({
            '-1:word.lower()': word1.lower() if word1.isalpha() else word1,
            '-1:word.istitle()': word1.istitle(),
            '-1:word.isupper()': word1.isupper(),
           
        })
    else:
        features['BOS'] = True
  

    if i < len(sent)-1:
        word1 = str(sent[i+1][0])
       
        features.update({
            '+1:word.lower()': word1.lower() if word1.isalpha() else word1,
            '+1:word.istitle()': word1.istitle(),
            '+1:word.isupper()': word1.isupper(),
        
        })
    else:
        features['EOS'] = True

    return features


def sent_to_features(sent,f):
    return [word_to_features(sent, i,f) for i in range(len(sent))]

def sent_to_labels(sent):
    return [label for token,label in sent]

