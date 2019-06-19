import json
from flask import Response, request, jsonify, json
import requests

db = {}
def func():
   global db
   r = requests.put("http://127.0.0.1:8083/key-value-store-view",json={'socket-address': '10.10.0.6:8080'}, timeout=1)
   
   # print("CONTENT **********")
   # print(r.content)
   # print("JSON ************")
   # print(r.json())

   potential_data = r.json()

   print("POTENTIAL DATA********")
   print(potential_data)
   #jsobj = json.loads(potential_data)
   #jsobj = json.loads(str(potential_data))
   print('\n\n')
   print(potential_data['buff_req'])
   print(type(potential_data['buff_req']))
   print('\n\n')
   pot_db = potential_data['db']
   pot_exec_req = [ v for v in potential_data['exec_req'].values()]
   pot_buff_req = [tuple(tup) for tup in json.loads(jsobj['buff_req']).values()]

   print(pot_db)
   print("POT_EXEC_REQ")
   print(pot_exec_req)
   print("POT_BUFF_REQ")
   print(pot_buff_req)
   db = pot_db
   print(db)
   
func()
print("db after func() = " + str(db))
data = db.get("x")
if data is not None:
   value = data[0]
   cmd = data[1]
   req_id = data[2]
   print("value = " + str(value) + ", cmd = " + str(cmd) + ", req_id = " + str(req_id))
