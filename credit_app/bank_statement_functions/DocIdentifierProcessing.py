import sys
import os
import io
import pandas as pd
import traceback
from dicttoxml import dicttoxml
sys.path.insert(1,'/config/yolov5') # path of yolov5 folder which is inside config folder

from doc_identifier import Doc_Element_Identifier
from doc_identifier.FunctionLibrary import skewcorrect
from ocr_package import OCR #IND-OCR
import os

def get_ocr_data(ocr_type, fileName):
    try:
        config_folder_path='ocr_config'
        obj=OCR.OCR_extraction(ocr_type, config_folder_path)
        df, textlist, json= obj.get_text(fileName)
        if not df.empty:
            df = df.to_json()
        resp = {"df":df, "textlist":textlist, "json":json}
        return {"data":resp, "status":1, "message":"OCR Completed"}
    except:
        if os.path.isfile(fileName):
            os.remove(fileName)
        return {"status":0,"message":"error doing ocr"}

# file_path='/home/jyoti/Desktop/Expense Claims - Ramco Systems.zip (Unzipped Files)/RAMCOINVOICES/12211_FinMasterRole_6_1515152575355.pdf'
class DocElementIdentifierV1:
    def __init__(self):
        self.model1 = Doc_Element_Identifier.XML_generator_stage1(config_path='./config')
            
    def capture_object(self, file_path, img_dir_path,ocr_type, password='',resp_format='json'):
        password=b""
        all_page_ocr_df, img_list, img_dir_path = self.model1.final_XML_generator(filepath=file_path,password=password,out_dir=img_dir_path)   
        response = {}
        page_wise_data = {}
        filename = os.path.basename(file_path)
        id = 0
        response['filename'] = filename         
        for pageno, img_name in enumerate(img_list):
            img_path = os.path.join(img_dir_path,img_name)
            page = os.path.splitext(os.path.basename(img_path))[0]
            pageno = page.split('_')[-1]
            if all_page_ocr_df.empty:
                skewcorrect(img_path)
                ocr_response = get_ocr_data(ocr_type, img_path)
                json_data, id=self.model1.xmlgenerator_fornonreadable(img_path,img_dir_path,ocr_response,img_name, id)
                page_wise_data[page]= json_data                
                # a=self.model1.xmlgenerator_fornonreadable(img_path,img_dir_path,response,img_name)
                # return a
            else:
                json_data, id = self.model1.xmlgenerator_forreadable(img_path,img_dir_path,all_page_ocr_df,pageno, id) 
                page_wise_data[page]= json_data
            id+=1
            response['result'] = page_wise_data   
        if resp_format=='xml':
            return dicttoxml(response,attr_type=False)
        else:
            return response                     

class DocElementIdentifierV2:
    def __init__(self):
        self.model2 = Doc_Element_Identifier.XML_generator_stage2(config_path='./config')
            
    def capture_object(self, file_path, img_dir_path,ocr_type, password='',resp_format='json'):
        password=b""
        all_page_ocr_df, img_list, img_dir_path = self.model2.final_XML_generator(filepath=file_path,password=password,out_dir=img_dir_path)   
        response = {}
        page_wise_data = {}
        filename = os.path.basename(file_path)
        id = 0
        response['filename'] = filename         
        for pageno, img_name in enumerate(img_list):
            img_path = os.path.join(img_dir_path,img_name)
            page = os.path.splitext(os.path.basename(img_path))[0]
            pageno = page.split('_')[-1]
            if all_page_ocr_df.empty:
                skewcorrect(img_path)
                ocr_response = get_ocr_data(ocr_type, img_path)
                json_data, id=self.model2.xmlgenerator_fornonreadable(img_path,img_dir_path,ocr_response,img_name, id)
                page_wise_data[page]= json_data                
                # a=self.model2.xmlgenerator_fornonreadable(img_path,img_dir_path,response,img_name)
                # return a
            else:
                json_data, id = self.model2.xmlgenerator_forreadable(img_path,img_dir_path,all_page_ocr_df,pageno, id) 
                page_wise_data[page]= json_data
            id+=1

            response['result'] = page_wise_data 
        if resp_format=='xml':
            return dicttoxml(response,attr_type=False)
        else:
            return response


