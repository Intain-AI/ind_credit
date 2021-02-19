import os

IND_EMAIL = "no-reply@in-d.ai"
IND_PASSWD = "Intain@123"
BASE_URL = os.environ.get('BASE_URL',"http://0.0.0.0:5004")
# BASE_URL = os.environ.get('BASE_URL',"http://35.209.125.251:3000")
# BASE_URL = os.environ.get('BASE_URL',"https://credit.in-d.ai/hdfc")

# Project_variables
IND_CREDIT_PROJECT_NAME = 'ind_credit'

# MongoDB variables
IND_CREDIT_MONGODB_PORT = 27017
IND_CREDIT_MONGODB_URL = 'localhost'
IND_CREDIT_MONGODB_NAME = 'ind_credit_db'

# Project variables
IND_CREDIT_ROOT_DIR=os.getcwd()
IND_CREDIT_TEMP_DIR=os.path.join('/tmp',IND_CREDIT_PROJECT_NAME)

# Google vision variables
IND_CREDIT_GOOGLE_APPLICATION_CREDENTIALS = os.path.join(IND_CREDIT_ROOT_DIR,'config/apikey.json')

# Upload dir variables
IND_CREDIT_UPLOAD_DIR_FLASK_REL='static/uploads'
IND_CREDIT_UPLOAD_DIR_ABS = os.path.join(IND_CREDIT_ROOT_DIR,'webserverflask',IND_CREDIT_UPLOAD_DIR_FLASK_REL)

#Template Folder
IND_CREDIT_TEMPLATES=os.path.join(IND_CREDIT_ROOT_DIR,'webserverflask/templates/')

# Required CSV files
IND_CREDIT_IFSC_CODE_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/IFSC_Code.xlsx')
IND_CREDIT_LOCALIZATION_BANK_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/localization_bank.csv')
# IND_CREDIT_IFSC_CODE_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/IFSC_Code.csv')
IND_CREDIT_FILE_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/coordinates.csv')
IND_CREDIT_TABLE_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/table.csv')
IND_CREDIT_PARA_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/para.csv')
IND_CREDIT_TXNDATA_JSON = os.path.join(IND_CREDIT_ROOT_DIR,'config','txndata.json')
IND_CREDIT_COORDINATE_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/coordinate.csv')
IND_CREDIT_TXNDATA_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config','txn_data.csv')
IND_CREDIT_DOCUMENT_HTML = os.path.join(IND_CREDIT_ROOT_DIR,'config/documentselection.html')

# Calculation CSV
IND_CREDIT_KEYWORDS_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/keywords.xlsx')
IND_CREDIT_BANK_TAGS_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/bank_taglines.xlsx')
# IND_BANK_STATEMENt_HEADERS_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/headers.csv')
IND_BANK_STATEMENt_HEADERS_CSV = os.path.join(IND_CREDIT_ROOT_DIR,'config/headers.csv')
IND_BANK_STATEMENt_FORMULA = os.path.join(IND_CREDIT_ROOT_DIR,'config/formula.ods')

IND_CREDIT_INTERFACE_GRAPH = os.path.join(IND_CREDIT_ROOT_DIR,'config/model_weights/frozen_inference_graph.pb')
IND_CREDIT_LABEL_MAP = os.path.join(IND_CREDIT_ROOT_DIR,'config/model_weights/trial_label_map.pbtxt')

IND_CREDIT_INTERFACE_GRAPH = os.path.join(IND_CREDIT_ROOT_DIR,'config/model_weights/frozen_inference_graph_payslip.pb')
IND_CREDIT_LABEL_MAP = os.path.join(IND_CREDIT_ROOT_DIR,'config/model_weights/objectdetection_payslip.pbtxt')
IND_CREDIT_ATTRIBUTE_JSON = os.path.join(IND_CREDIT_ROOT_DIR,'config','attribute_config.json')

