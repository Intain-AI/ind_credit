import os
import re
import time
# from incomeanalysisnew import giveimage, giveimage1
# from IncomeAnalysis_utilityfunctionsnew import extractdoctype,extractbankname,extractpassbookname,get_borderdTable,get_borderdTable1
from PIL import Image
import PIL
import shutil
import traceback
# from decrypted_pdf import decrypt_pdf
# from document_type import get_document_type
from pdf2image import convert_from_path
# from tabula_pdf import get_table_data
# from Testing import get_table_coordinate,get_tabular_data
import pdftotext
import pandas as pd
from PyPDF2 import PdfFileMerger

########################################################################################

def get_file_name(file_list,folder_path):
    merger = PdfFileMerger()
    for pdf in file_list:
        print(">>>>$$$$$$$$$$$",pdf)
        file_name = os.path.join(folder_path,pdf)
        merger.append(file_name)
    file_path = os.path.join(folder_path,'merge_pdf.pdf')
    merger.write(file_path)
    merger.close()
    return file_path

##########################################################################################

def table_coordinate(documentType,bank_name,image_name,preprocess_list,page_index,number_of_pages):
    try:
        # print("++++++++++++ preprocess_list ++++++++++++",page_index,preprocess_list)
        if page_index == 0 or (page_index ==1 and not preprocess_list):
            outputDir = os.getcwd()
            start_time = time.time()
            left, top, width, height,columns_list = get_table_coordinate(image_name,page_index,preprocess_list)
            print("****** TABLE DETECTION TIME COMPLEXITY for page {} is {} *******".format(page_index,time.time()-start_time))
            income_preprocess_result = {}
            income_preprocess_result["left"] = left
            income_preprocess_result["top"] = top
            income_preprocess_result["width"] = width
            income_preprocess_result["height"] = height
            income_preprocess_result["documentType"] = documentType
            income_preprocess_result["bank_name"] = bank_name

            corrected_imageName = image_name.split('/')[-5:]
            corrected_imageName = "/".join(corrected_imageName)
            income_preprocess_result["corrected_imageName"] = corrected_imageName

            if not width:
                columns_list = []
                return preprocess_list, columns_list
            preprocess_list.append(income_preprocess_result.copy())

            return preprocess_list,columns_list


        elif 1 < page_index < number_of_pages-1 :
            first_image_value = preprocess_list[-1]
            for key, value in first_image_value.items():
                if key=='left':
                    inputleft = value
                if key == 'top':
                    inputtop = value
                if key == 'width':
                    inputwidth = value
                if key == 'height':
                    inputheight = value
                if key == 'documentType':
                    documentType = value
                if key =='bank_name':
                    bank_name = value
            new_income_preprocess_list = {}
            new_income_preprocess_list["left"] = inputleft
            new_income_preprocess_list["top"] = inputtop
            new_income_preprocess_list["width"] = inputwidth
            new_income_preprocess_list["height"] = inputheight
            new_income_preprocess_list["documentType"] = 'Bank Statement'
            new_income_preprocess_list["bank_name"] = bank_name
            new_image_name = image_name.split('/')[-5:]
            new_image_name = "/".join(new_image_name)
            new_income_preprocess_list["corrected_imageName"] = new_image_name
            if not inputwidth:
                columns_list = []
                return preprocess_list,columns_list
            preprocess_list.append(new_income_preprocess_list.copy())
            columns_list = []
            return preprocess_list,columns_list
        outputDir = os.getcwd()
        start_time = time.time()
        ######################  Table Detection ########################
        # corrected_imageName, (left, top, width, height) = get_borderdTable(image_name, outputDir)
        columns_list = []
        left, top, width, height,columns_list = get_table_coordinate(image_name,page_index,preprocess_list)

        print("****** TABLE DETECTION TIME COMPLEXITY for page {} is {} *******".format(page_index,time.time()-start_time))
        income_preprocess_result = {}
        income_preprocess_result["left"] = left
        income_preprocess_result["top"] = top
        income_preprocess_result["width"] = width
        income_preprocess_result["height"] = height
        income_preprocess_result["documentType"] = documentType
        income_preprocess_result["bank_name"] = bank_name

        corrected_imageName = image_name.split('/')[-5:]
        corrected_imageName = "/".join(corrected_imageName)
        income_preprocess_result["corrected_imageName"] = corrected_imageName

        if not width:
            return preprocess_list,columns_list
        preprocess_list.append(income_preprocess_result.copy())

        return preprocess_list,columns_list
    except:
        print(traceback.print_exc())
        preprocess_list = []
        columns_list = []
        return preprocess_list,columns_list

###########################################################################################

def get_bank_statement(file_path,doc_type,bank_name,readable_status):

    preprocess_list = []
    if file_path.endswith('.pdf') or file_path.endswith('.PDF'):
        if readable_status == 'readable':
            print('++++++++++++++ PDF file is readable +++++++++++++++++++')
            pages = convert_from_path(file_path,200)
            file_path = file_path[:-4]
            for page in pages:
                page.save("%s-page%d.jpg" % (file_path,pages.index(page)), "JPEG")
            print("+++++ Number of Pages in file : {} +++++".format(len(pages)))
            number_of_pages = len(pages)

            for i in range(0,number_of_pages):
                image_path = file_path + '-page'+ str(i) +'.jpg'
                img = Image.open(image_path)
                width, height = img.size
                # print("+++++++width, height +++++",width, height)
                if width>1800:
                    basewidth = 1800
                    img = Image.open(image_path)
                    wpercent = (basewidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    reduced_percentage = int(width)/1800
                    img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                    img.save(image_path)
                    img = Image.open(image_path)
                    width, height = img.size
                else:
                    reduced_percentage = 1
                outer_table_coordinate_list,columns_list = table_coordinate(doc_type,bank_name,image_path,preprocess_list,i,number_of_pages)
                # print('*************',outer_table_coordinate_list,columns_list)
                if i == 0  or (i ==1 and columns_list):
                    final_column_list = []
                    final_column_list.append(columns_list)
            reduced_percentage = 200/(72*reduced_percentage)
            # print("outer_table_coordinate_list,width,height,reduced_percentage,final_column_list[0]\n",outer_table_coordinate_list,width,height,readable_status,reduced_percentage,final_column_list[0])
            return outer_table_coordinate_list,width,height,reduced_percentage,final_column_list[0]

        else:
            print('+++++++++++++++++ PDF file is non-readable++++++++++++++++')
            pages = convert_from_path(file_path,250)
            file_path = file_path[:-4]
            for page in pages:
                page.save("%s-page%d.jpg" % (file_path,pages.index(page)), "JPEG")
            print("Number of Pages in file : ",len(pages))
            number_of_pages = len(pages)

            for i in range(0,number_of_pages):
                image_path = file_path + '-page'+ str(i) +'.jpg'
                img = Image.open(image_path)
                width, height = img.size
                if width>1800:
                    basewidth = 1800
                    img = Image.open(image_path)
                    wpercent = (basewidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                    img.save(image_path)

                outer_table_coordinate_list,columns_list = table_coordinate(doc_type,bank_name,image_path,preprocess_list,i,number_of_pages)
                if i == 0:
                    final_column_list = []
                    final_column_list.append(columns_list)
            return outer_table_coordinate_list,width,height,1,final_column_list[0]

    else:
        print('+++++++++++++++++ Image is non-readable +++++++++++++++++++')
        # doc_type,bank_name = get_document_type(file_path)

        img = Image.open(file_path)
        width, height = img.size
        # if width>5800:
        #     basewidth = 1800
        #     img = Image.open(file_path)
        #     wpercent = (basewidth / float(img.size[0]))
        #     hsize = int((float(img.size[1]) * float(wpercent)))
        #     img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
        #     img.save(file_path)
        out,columns_list = table_coordinate(doc_type,bank_name,file_path,preprocess_list,0,1)
        # readable_status = 'non-readable'
        reduced_percentage = 1

        return out,width,height,reduced_percentage,columns_list

###############################################################################################

def extraction_column(data):
    outputDir = os.getcwd()
    first_image_value = data[0]
    for key, value in first_image_value.items():
        if key=='left':
            inputleft = value
        if key == 'top':
            inputtop = value
        if key == 'width':
            inputwidth = value
        if key == 'height':
            inputheight = value
        if key == 'documentType':
            documentType = value
        # if key =='bank_name':
        #     bank_name = value
        if key =='corrected_imageName':
            income_document_image = value
            income_document_image= income_document_image.strip()

    final_df, columns_list = giveimage1(income_document_image, outputDir, documentType, inputleft, inputtop, inputwidth, inputheight)

    return columns_list

def get_columns_distance_values(columns):
    columns_distance_values = []
    for column_data in columns:
        for key2,value2 in column_data.items():
            if key2 == 'left':
                column_left = value2
                distance_value = float(column_left)
                columns_distance_values.append(distance_value)
    return columns_distance_values

def get_columns_coordinates(columns,columns_distance_values,inputleft,inputtop,inputwidth,inputheight):
    columns_distance_values.insert(0,0)
    columns_distance_values = sorted(columns_distance_values)
    final_column_coordinates = []
    inputtop = int(float(inputtop))
    for index,column_left in enumerate(columns_distance_values):
        columns_coordinates = []
        columns_coordinates.append(int(column_left))
        
        if index == len(columns_distance_values)-1:
            width = inputwidth
        else:
            width = columns_distance_values[index+1]
        columns_coordinates.append(int(float(width)))
        columns_coordinates.append(int(inputtop))
        columns_coordinates.append(int(float(inputheight))+int(float(inputtop)))
        final_column_coordinates.append(columns_coordinates)
    # print("final_column_coordinates",final_column_coordinates)
    return final_column_coordinates

def extraction_data(data,readable_status,reduced_percentage,pdf_file_path):

    # print("::::::::::::::::::LLLLLLLLLLLLLLLL\n",data)
    count = 0
    final_output = []
    # outputDir = os.getcwd()
    columns_distance = data[0]
    for key, value in columns_distance.items():
            if key == 'table_data':
                for item1 in value:
                    for key1,value1 in item1.items():
                        if key1 == 'colItem':
                            columns = value1

    input_pdf = []
    for item in data:
        for key, value in item.items():
            # if key == 'documentType':
            #     documentType = value
            if key == 'bank_name':
                bank_name = value
            if key == 'corrected_imageName':
                income_document_image = value
                income_document_image= income_document_image.strip()
            if key == 'table_data':
                for item1 in value:
                    for key3,value3 in item1.items():
                        if key3 == 'left':
                            inputleft = value3
                        if key3 == 'top':
                            inputtop = value3
                        if key3 == 'height':
                            inputheight = value3
                        if key3 == 'width':
                            inputwidth = value3


        columns_distance_values = get_columns_distance_values(columns)

        # print(">>>>>>>>",income_document_image, inputleft, inputtop, inputwidth, inputheight, documentType, bank_name,columns_distance_values)
        if readable_status == 'readable':    
            final_df = get_table_data(input_pdf,income_document_image, inputleft, inputtop, inputwidth, inputheight, bank_name,columns_distance_values,reduced_percentage,pdf_file_path)
        else:
            # print("+++++++++++++",columns,columns_distance_values,inputleft,inputtop,inputwidth,inputheight)
            columns_coordinates = get_columns_coordinates(columns,columns_distance_values,inputleft,inputtop,inputwidth,inputheight)

            # final_df = giveimage(income_document_image, outputDir, documentType, inputleft, inputtop, inputwidth, inputheight,columns_distance_values)
            table_cords = (int(float(inputleft)),int(float(inputwidth)), int(float(inputtop)), int(float(inputheight))+int(float(inputtop)))
            table_cords = list(table_cords)
            # print("+++++++++++++++++++",income_document_image,table_cords,columns_coordinates)
            final_df = get_tabular_data(income_document_image,table_cords,columns_coordinates)
            # final_df = pd.DataFrame()
        # print("this is the final purpose++++++++++++++++++\n", final_df)
        excel_data = final_df.to_json(orient='index')

        result = {}
        result["image_path"] = income_document_image
        result["page_num"] = count
        result["excel_data"] = excel_data
        count = count +1
        final_output.append(result)    
    return final_output

