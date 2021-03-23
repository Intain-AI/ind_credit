from flask import request,jsonify,make_response
from functools import wraps
import requests
import jwt
import traceback
import os

INDONE_URL="https://one.in-d.ai"
BASE_URL = os.getenv("INDONE_URL")
print(BASE_URL)
VERIFY_URL = str(BASE_URL)+'api/credits/verify/' 
LOG_URL = BASE_URL+'api/credits/log/'
VERIFY_URL_ADMIN = str(BASE_URL)+'api/credits/admin_verify/' 
LOG_URL_ADMIN = BASE_URL+'api/credits/admin_log/'
API_TOKEN_URL = BASE_URL+'api/keys/token/' 

VERIFYING_KEY = '''
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA0ghIvDcuO7DIIXqyhYET
QP9/TeNHx+p4scaZ14F8WS4vV/wHMvp//WqKvZOZT7aQh8ihMfZXR2MZ63+yIJ7D
xIIG6ojJmwrQbk9DOIv3NCIBAG84+jKz6IFano5z2D1kx/DxDRFEdjyPwHMbVxEH
p41Z+hu2LcYNYHzmgsOsNmSYTwwGcaQdLl9+P488HLaXZoicq6cj41FKIynti0E6
H50+4ZstKzklwXj05aOxE9HPPVLGzSZxsOYcfKp4UR+f6iJIkPy8Jj7w3xd2/SVM
3RuxfIwuDREvX5EhmM2cKYBAf4Bp7OSUMecSM2nXsjDmfRhNHpP7IfqOk//BCsgC
l1Jh4hl5mPlOwaVSZ9EJSuQa8FzAmkTS8moK9BcGzc6r5NUYUBTbKRcNaxUnwhBC
ByvdswpRT4w8g6w0iclWNyCB1qMwZiqfUn94h5bC852oU25LTQn2V4ZJopuoVr62
FKC/xkq2Lhvfjq4Qzmr5nhEHPJRlt/9YPXXMeTjYKmc09o2h+dLshhWuSeKyOwcL
tj+Rip7lTTh7N090W2HBCss6CgwAER5NT+AOyzTajIDpbd6Zs3OHg/VJRTpn2vgf
0uo8htoGGulemwD/x4nXkVhYGdRxSqgYa4Vzip7+4afoDR+5bB9maXFhPuFYs19d
3Qkg79xUu6CHYj4B/tTsqpMCAwEAAQ==
-----END PUBLIC KEY-----
'''

# to just verify the token
def verify_token(request):
    try:
        auth_headers = request.headers.get('Authorization')

        if not auth_headers:
            apikey = request.headers.get('x-api-key')
            if not apikey:
                return {'message':'authorization headers or api key not given'},401, "_"

            response = requests.get(
                API_TOKEN_URL,headers={"x-api-key": apikey})

            status_code = response.status_code
            if status_code != 201:
                return response.json(),status_code, "_"

            token = response.json().get('access')

            if not token:
                return {'message':'unable to auth the request'} , 401, "_"

            auth_headers = 'Bearer '+token
        
        token_split = auth_headers.split()
        if 'Bearer' != token_split[0]:
            return {'message':'bearer token not given'}, 401, "_"
        
        try:
            user_data = jwt.decode(token_split[1], VERIFYING_KEY, algorithms=['RS256'])
            return user_data, 1, token_split[1]
        except:
            print(traceback.print_exc())
            return {"message":"invalid token"}, 401, "_"
    except:
        print(traceback.print_exc())
        return {"message":"invalid token"}, 401, "_"
    
    

# to verify and check if credits are left
def indone_auth(service_id, request): 

    auth_headers = request.headers.get('Authorization')

    if not auth_headers:
        apikey = request.headers.get('x-api-key')
        if not apikey:
            return {'message':'authorization headers or api key not given'},401, "_"

        response = requests.get(
            API_TOKEN_URL,headers={"x-api-key": apikey})

        status_code = response.status_code
        if status_code != 201:
            return response.json(),status_code, "_"

        token = response.json().get('access')

        if not token:
            return {'message':'unable to auth the request'} , 401, "_"

        auth_headers = 'Bearer '+token
    
    token_split = auth_headers.split()
    if 'Bearer' != token_split[0]:
        return {'message':'bearer token not given'}, 401, "_"

    response = requests.post(
        VERIFY_URL,
        json={
            "service_id":service_id
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": auth_headers
        }
    )
    # print(response.text)
    try:
        status_code = response.status_code
        if status_code != 200:
            user_data = jwt.decode(token_split[1], VERIFYING_KEY, algorithms=['RS256'])
            return response.json(),2, user_data

        user_data = jwt.decode(token_split[1], VERIFYING_KEY, algorithms=['RS256'])
        
        return user_data, 1, token_split[1]
    except:
        print(traceback.print_exc())
        return {"message":"invalid token"}, 401, "_"

# to log the usage
def log_usage(service_id, token):
    #post function run
    auth_headers = 'Bearer '+token

    response = requests.post(
        LOG_URL,
        json={
            "service_id":service_id
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": auth_headers
        }
    )
    if response.status_code != 200:
        print("Alert: ",response.json())
        pass



# to verify and check if credits are left
def indone_auth_admin(service_id, email): 

    response = requests.post(
        VERIFY_URL_ADMIN,
        json={
            "service_id":service_id,
            "email":email
        },
        headers={
            "Content-Type": "application/json"
        }
    )
    # print(response.text)
    status_code = response.status_code
    if status_code != 200:
        return response.json(),2
    return True, 1


# to log the usage
def log_usage_admin(service_id, email):
    #post function run

    response = requests.post(
        LOG_URL_ADMIN,
        json={
            "service_id":service_id,
            "email":email
        },
        headers={
            "Content-Type": "application/json"
        }
    )
    if response.status_code != 200:
        print("Alert: ",response.json())
        pass
