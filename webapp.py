from flask import Flask, jsonify, request
import traceback
from credit_app.bank_statement_functions import DocIdentifierProcessing 
app = Flask(__name__)

app.config.update(
    JSON_SORT_KEYS = False
)

#########Initialization of the models used identifying header,paragraph and table #########
docModel_stage1 = DocElementIdentifierV1()

######### Initialization of the models used for identifying logical cells and table #########
docModel_stage2 = DocElementIdentifierV2()

''' API for generating xml files from DocElementIdentifier.
    Required arguments are file_path (pdf or image file), password (if pdf file is password protected)else will be taken as None by default, 
    img_dir_path: path specified by user to store generated images and corresponding images.If not specified will be saved in default directory generated by Doc-Identifier,
    ocr_type to be specified be the user, modeltype also to be specified either as stage_1 or stage_2'''


@app.route("/api/capture_object", methods=['POST'])
def capture_object():
    content_type = request.content_type
    if 'json' in content_type:
        try:
            data = request.get_json()
            file_path = data['file_path']
            img_dir_path = data['img_dir_path']
            model_type=data['model_type']
            ocr_type = data['ocr_type']
            if 'resp_format' in data:
                resp_format=data['resp_format']
            else:
                resp_format='json'
            if 'password' in data:
                password = data['password']
            else:
                password = ''
            if model_type=='stage_1':
                response=docModel_stage1.capture_object(file_path,img_dir_path,ocr_type,password,resp_format)
                # if a==0:
                #     return "Successfully captured",200
                # else:
                #     return "Not Captured", 415
            else:                
                response=docModel_stage2.capture_object(file_path,img_dir_path,ocr_type,password,resp_format)
                # if a==0:
                #     return "Successfully captured",200
                # else:
                #     return "Not Captured", 415 
            return jsonify(eval(str(response))), 200              
             
            
        except Exception as e: 
            print(traceback.print_exc())                                             
            return jsonify({'message': 'Not captured'}), 415

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
    