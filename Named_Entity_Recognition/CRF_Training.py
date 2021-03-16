# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 10:38:20 2021

@author: DELL
"""
import Features_For_CRF as Features
import pandas as pd
from sklearn_crfsuite import CRF
import pickle
try:
    data=pd.read_csv("Logical_cells.csv")
    sentences= Features.getsentence(data,1)
    X_train= [Features.sent_to_features(s,1) for s in sentences]
    Y_train= [Features.sent_to_labels(s) for s in sentences]
    crf = CRF(algorithm='lbfgs',c1=0.1,c2=0.1,max_iterations=100,all_possible_transitions=False)
    crf_model=crf.fit(X_train,Y_train)
    pickle.dump(crf_model, open('CRF_classifier.clf', 'wb'))
    
except:
    print("Training data not found!")
