import pytest
import requests
import json
from genericMethods import readConfigIni

strAPIURL= conn_str=readConfigIni('APIURL')
def test_getRequest():
    strAPIEndPoint=readConfigIni('getRequest')
    resp=requests.get(strAPIURL+strAPIEndPoint)
    code=resp.status_code
    json_response=resp.json()
    assert json_response['total']==12

def test_postRequest():
    strAPIEndPoint=readConfigIni('postRequest')
    data=open('payloads/createUser.json', "r").read()
    finalRequest=strAPIURL+strAPIEndPoint
    resp=requests.post(finalRequest, data=json.loads(data))
    code=resp.status_code
    json_response=resp.json()
    assert json_response['job']=='TestLead'

