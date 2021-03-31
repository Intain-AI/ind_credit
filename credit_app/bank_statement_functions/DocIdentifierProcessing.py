import sys
import os
import io
import pandas as pd
import traceback
from dicttoxml import dicttoxml
sys.path.insert(1,'/config/yolov5') # path of yolov5 folder which is inside config folder

from doc_identifier import Doc_Element_Identifier
from doc_identifier.FunctionLibrary import skewcorrect
from doc_identifier.FunctionLibrary import orientation_correction
from ocr_package import OCR #IND-OCR
import os
import warnings
warnings.simplefilter("ignore")

def get_ocr_data(ocr_type, fileName):
    try:
        config_folder_path='ocr_config'
        obj=OCR.OCR_extraction(ocr_type, config_folder_path)
        df, textlist, json= obj.get_text(fileName)
        # if not df.empty:
        df = df.to_json()
        resp = {"df":df, "textlist":textlist, "json":json}
        return {"data":resp, "status":1, "message":"OCR Completed"}
    except:
        if os.path.isfile(fileName):
            os.remove(fileName)
        return {"status":0,"message":"error doing ocr"}

class DocElementIdentifierV1:
    def __init__(self):
        self.model1 = Doc_Element_Identifier.XML_generator_stage1(config_path='./config')
            
    def capture_object(self, file_path, img_dir_path,ocr_type, password='',resp_format='json'):
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
                df_ocr=pd.DataFrame.from_dict(eval(ocr_response['data']['df']))
                if not df_ocr.empty:
                    json_data, id=self.model1.xmlgenerator_fornonreadable(img_path,img_dir_path,df_ocr,img_name, id)
                else:
                    print('The page is blank.')
                    json_data = {}
                if not bool(json_data):
                    json_data = {'id':id, 'image_size':{'height':0, 'width':0}, 'digitized_details': {'logical_cells':[], 'table_cells':[]}}
                page_wise_data[page]= json_data                
              
            else:
                df_ocr= all_page_ocr_df[all_page_ocr_df['pageno']==int(pageno)]
                if df_ocr.empty:
                    columns=['token','x1','y1','x2','y2','x3','y3','x4','y4']
                    skewcorrect(img_path)
                    ocr_response = get_ocr_data(ocr_type, img_path)
                    
                    df_ocr=pd.DataFrame.from_dict(eval(ocr_response['data']['df']))
                    df_ocr.columns = columns
                if not df_ocr.empty:    
                    
                    json_data, id = self.model1.xmlgenerator_forreadable(img_path,img_dir_path,df_ocr, id) 
                else:
                    print('The page is blank.')
                    json_data = {}
                if not bool(json_data):
                    json_data = {'id':id, 'image_size':{'height':0, 'width':0}, 'digitized_details': {'logical_cells':[], 'table_cells':[]}}
                
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
                orientation_correction(img_path)
                skewcorrect(img_path)
                ocr_response = get_ocr_data(ocr_type, img_path)
                df_ocr=pd.DataFrame.from_dict(eval(ocr_response['data']['df']))
                if not df_ocr.empty:
                    json_data, id=self.model2.xmlgenerator_fornonreadable(img_path,img_dir_path,df_ocr,img_name, id)
                else:
                    print('The page is blank.')
                    json_data = {}
                if not bool(json_data):
                    json_data = {'id':id, 'image_size':{'height':0, 'width':0}, 'digitized_details': {'logical_cells':[], 'table_cells':[]}}
                page_wise_data[page]= json_data                
              
            else:
                df_ocr= all_page_ocr_df[all_page_ocr_df['pageno']==int(pageno)]
                if df_ocr.empty:
                    columns=['token','x1','y1','x2','y2','x3','y3','x4','y4']
                    skewcorrect(img_path)
                    ocr_response = get_ocr_data(ocr_type, img_path)
                    df_ocr=pd.DataFrame.from_dict(eval(ocr_response['data']['df']))
                    df_ocr.columns = columns
                if not df_ocr.empty:    
                    
                    json_data, id = self.model2.xmlgenerator_forreadable(img_path,img_dir_path,df_ocr, id) 
                else:
                    print('The page is blank.')
                    json_data = {}
                if not bool(json_data):
                    json_data = {'id':id, 'image_size':{'height':0, 'width':0}, 'digitized_details': {'logical_cells':[], 'table_cells':[]}}
                
                page_wise_data[page]= json_data
            id+=1
        response['result'] = page_wise_data   
        if resp_format=='xml':
            return dicttoxml(response,attr_type=False)
        else:
            return response




    
