import json
from flask import Response, request, jsonify, json
import requests

exec_req = [0]


exec_req_str = json.dumps({i:n for i,n in enumerate(exec_req)})
print(exec_req_str)
print(type(exec_req_str))