# Assignment 2B: Refactoring database lookups, etc. from 2A into
# a separate module
from flask import Response, request, jsonify, json
import global_vars
import requests
import os
import time
import threading
import random
import collections
from shard import *

# import global variables

from view import removeView

# helper func to do a custom GET request for the entire database
'''
def getStateFromReplica(replica):
   state_req = requests.get("http://" + replica + "/key-value-store/everything", timeout=1)
   jsobj = r.json()
   pot_db = json.loads(jsobj['db'])
   pot_exec_req = [int(n) for n in jsobj['exec_req'].split(',')]
   pot_buff_req = [tuple(tup) for tup in json.loads(jsobj['buff_req']).values()]
   global db
   global exec_req
   global buff_req
   db = pot_db
   exec_req = pot_exec_req
   buff_req = pot_buff_req
   return db
'''
#only happens once when process starts


def repPutBroad(key, value, cmd, req_id):
   #for replica in VIEW:
   # broadcast only to members of its own shard
   myshard = global_vars.shard_members[str(global_vars.shard_id)]
   
   for replica in myshard:
      if replica != global_vars.MY_ADDRESS:
         try:
            respFrom = requests.put('http://'+replica+'/key-value-store/'+key,
                                    json={'value': value, 'causal-metadata': cmd, 'version': req_id}, timeout=1)
         except Exception:
            # both replicas are removed for some reason. Called twice?
            removeView(replica, True)
   #return respFrom

#respFrom = requests.put("http://"+replica+"/key-value-store-view", '{"socket-address":'+ip+'}',timeout=1)

# If a request is known to be valid and causally able to be
# executed, performs the database entry and version # generation.
# returns either an Added successfully or Updated successfully response
def exec_known_valid_request(key, val, cmd):
   req_id = global_vars.counter
   global_vars.counter += global_vars.counter_offset

   if cmd == '':
      new_cmd = cmd
   else:
      new_cmd = cmd + ','
   new_cmd += str(req_id)

   #cmd = new_cmd
   #tup = (val, cmd, req_id)
   tup = (val, new_cmd, req_id)

   if key in global_vars.db.keys():
      response = Response(
         '{"message":"Updated successfully","version":' + str(req_id) + ', "causal-metadata":' + str(new_cmd)+ ', "shard-id": ' + '"' + str(global_vars.shard_id) + '"' + '}\n', status = 200)
   else:
      response = Response(
         '{"message":"Added successfully","version":' + str(req_id) + ', "causal-metadata":' + str(new_cmd)+', "shard-id": ' + '"' + str(global_vars.shard_id) + '"' + '}\n', status = 201)

   # deliver request
   global_vars.db[key] = tup
   global_vars.exec_req.append(req_id)
   # broadcast to other replicas?
   repPutBroad(key, val, cmd, req_id)
   
   return response

# the same as exec_known_valid_request, except it only does database
# entry operations
def exec_buffered_request(key, val, cmd, req_id):
    tup = (val, cmd, req_id)
    # deliver request
    global_vars.db[key] = tup
    global_vars.exec_req.append(req_id)
    # broadcast to other replicas?
    #repPutBroad(key, val, new_cmd, req_id)
    repPutBroad(key, val, cmd, req_id)

# Checks if any requests in the buffer can be executed
# If it finds one, it is executed and returns True
# If no requests in the buffer can be executed, returns False


def checkBuffer():
    for r in global_vars.buff_req:
        key = r[0]
        val = r[1]
        cmd = r[2]
        req_id = r[3]
        can_execute = True
        for v in cmd:  # for each version # in cmd
            if v not in global_vars.exec_req:
                can_execute = False
                break
        if can_execute:
            # remove this request from the buffer
            # and execute it
            global_vars.buff_req.remove(r)
            exec_buffered_request(key, val, cmd, req_id)
            return True

    return False


def getRequest2(key):
   # Define default response data
   resp_data={
      "error":"Database is empty",
      "message":"Error in GET"
   }
   status = 404
   # If db not empty change the error
   if global_vars.db:
      resp_data['error'] = 'Key does not exist'
   # Try to find data for given key
   data = global_vars.db.get(key)
   # If we find data for the key
   if data != None:
      resp_data['message'] = 'Retrieved successfully'
      resp_data['version'] = data[2] #req_id
      resp_data['causal-metadata'] = data[1] #cmd
      resp_data['value'] = data[0]
      resp_data['shard-id'] = global_vars.shard_id
      del resp_data['error']
      status = 200
   return Response(json.dumps(resp_data),status=status)



# Assumes PUT requests enter info into the database in this format:
# 'key': (value, [dependency-list], id#)
# ex: db = {'x': ("A", [], 0), 'y': ("B", [0], 2)}
def getRequest(key):

    # special case to serve the entire database
    if(key == "everything"):
      data={
         "message":"Replica added successfully to the view",
         "db":json.dumps(global_vars.db),
         "exec_req":",".join([str(n) for n in global_vars.exec_req]),
         "buff_req":json.dumps({i:tup for i, tup in enumerate(global_vars.buff_req)}),
         "pot_data": "None" if global_vars.potential_data == None else json.dumps(global_vars.potential_data),
         "pot_db": "None" if global_vars.pot_db == None else json.dumps(global_vars.pot_db)
      }
      response = Response(json.dumps(data)+'\n', status=250)
      return response

    # retrieve key from store
    data = global_vars.db.get(key)
    # existing key response
    if data is not None:
        # convert value to json object for response
        value = data[0]
        cmd = data[1]
        req_id = data[2]
        json_response = '{"message":"Retrieved successfully", "version": ' + str(req_id) + ', "causal-metadata": ' + str(cmd) + ', "value": "' + str(value) + ', "shard-id": ' + '"' + str(global_vars.shard_id) + '"' + '}\n'
        code = 200
    # non-existing key response
    else:
        # set error message in json
        # check if db is empty or if it just can't find the key
        if not global_vars.db:
           json_response = '{"error":"Database is empty","message":"Error in GET"}\n'
           code = 404
        else:
           json_response = '{"error":"Key does not exist","message":"Error in GET"}\n'
           code = 404

    response = Response(json_response, status=code,
                        mimetype='application/json')
    return response

def shouldBuffer(cmd_list, exec_req):
    buffer = False
    #if cmd_list != [''] or (not cmd_list):
    if (not cmd_list) or (cmd_list == ['']) or (cmd_list == [""]):
      return False
    else:
        for v in cmd_list:
            if int(v) not in exec_req:
                buffer = True
                break
            #buffer = False

    return buffer

# helper for putRequest()
def handleBroadcastPut(key, val, cmd, cmd_lst, req_id):
   #check if needs to be buffered
   # need old value of cmd here
   if shouldBuffer(cmd_lst, global_vars.exec_req):
      global_vars.buff_req.append((key, val, cmd, req_id))
      response = Response('{"message":"Buffered your broadcast"}\n', status=206)
   else:
      # need to attach req_id to cmd before storing
      # add check if cmd is empty, if not then attach ", str(req_id)"
      cmd += str(req_id)
      tup = (val, cmd, req_id)
      global_vars.db[key] = tup
      global_vars.exec_req.append(req_id)
      response = Response('{"message":"Thank for the broadcast"}\n', status=200)
   return response

def handleClientPut(key, val, cmd, cmd_lst):
   if shouldBuffer(cmd_lst, global_vars.exec_req):
      global counter
      global counter_offset
      req_id = counter
      counter += counter_offset

      if cmd == '':
         new_cmd = cmd
      else:
         new_cmd = cmd + ','
      new_cmd += str(req_id)

      #cmd = new_cmd

      #buff_req.append((key, val, cmd, req_id))
      global_vars.buff_req.append((key, val, new_cmd, req_id))

      if key in global_vars.db.keys():
         response = Response('{"message":"Buffered update","version":'+str(req_id)+'"causal-metadata":'+str(new_cmd)+'}\n', status=300)
      else:
         response = Response('{"message":"Buffered initial add","version":'+str(req_id)+'"causal-metadata":'+str(new_cmd)+'}\n', status=301)

   else:
      response = exec_known_valid_request(key, val, cmd)

      # checks buffer for any requests that can now be executed
      # after exec_req has the new request
      while checkBuffer():
         pass
   return response

def putRequest(key, request):
   fromClient = False
   data = str(request.data)
   # can tell if request comes from client (no version attached)
   # or from another replica (version attached)
   try:
      jsobj = json.loads(data)
      req_id = jsobj["version"]
   except Exception:
      fromClient = True
   # catches malformed PUT requests
   try:
      jsobj = json.loads(data)
      val = jsobj["value"]
   except Exception:
      response = Response('{"error":"Value is missing","message":"Error in PUT"}\n', status=123)
      return response
   # catch the case where no cmd is passed in
   try:
      cmd = jsobj["causal-metadata"]
      cmd_lst = cmd.split(',')
   except Exception:
      cmd = ''
      cmd_lst = ['']

   # after request parsing, check if the key is too long
   if len(key) > 50:
      response = Response('{"error":"Key is too long","message":"Error in PUT"}\n', status=400)
      return response

   # If it's an internal broadcast message from another replica
   if not fromClient:
      response = handleBroadcastPut(key, val, cmd, cmd_lst, req_id)

   else:
      response = handleClientPut(key, val, cmd, cmd_lst)

   return response

def deleteRequest(key, request):
   json_response = ''
   # if the key exists
   if(global_vars.db.get(key) != None):
      del global_vars.db[key]
      json_response = '{"doesExist":true,"message":"Deleted successfully", "shard-id": ' + '"' + str(global_vars.shard_id) + '"' + '}'
      response = Response(json_response, status=200)

	# if the key does not exist
   else:
      json_response = '{"doesExist":false,"error":"Key does not exist","message":"Error in DELETE"}'
      response = Response(json_response, status=404)

   
   try:
      data = str(request.data)
      jsobj = json.loads(data)
      broadcast = jsobj.get("broadcast")
   except Exception:
      return None
	# forward this delete request to all other replicas if it's from client
   if broadcast == None:
      #for replica in VIEW:
      # broadcast only to members of its own shard
      myshard = global_vars.shard_members[str(global_vars.shard_id)]
      for replica in myshard:
         respFrom = requests.delete("http://"+replica+"/key-value-store/"+str(key), 
            json={'broadcast': False} ,timeout=1)

   return response
