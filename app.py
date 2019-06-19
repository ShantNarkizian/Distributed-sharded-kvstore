# Assignment 4: Sharding key-value-store
from flask import Flask, request, Response, redirect, jsonify, json
import global_vars
import os
import requests
import socket
import threading
import random
import collections
import keyvalue
import view
import time
import hashlib
import shard


app = Flask(__name__)

def is_flask_starting(app):
	wrm = (os.environ.get("WERKZEUG_RUN_MAIN") == 'true')
	return (not app.debug) or wrm


def startup():
   # we start up normally
   if global_vars.SHARD_COUNT is not None:
      shard.generate_shards(global_vars.SHARD_COUNT)
   # we must find out where we belong
   else:
      pass

   broadcast = False
   # get random replica address to compare our views
   while True:
      replica = random.choice(global_vars.VIEW)
      if replica != global_vars.MY_ADDRESS:
         try:
            # get another replica's view
            viewData = requests.get("http://" + replica + "/key-value-store-view", timeout=1)
            jsobj = viewData.json()
            otherView = jsobj.get("view")
            viewList = otherView.split(',')
            # check if we are a new replica
            if collections.Counter(viewList) != collections.Counter(global_vars.VIEW):
               broadcast = True
         except Exception:
            viewData = None
         break

   # if we are a new replica broadcast existence
   if broadcast:
      for replica in global_vars.VIEW:
         if replica != global_vars.MY_ADDRESS:
            try:
               global potential_data
               global pot_db
               global db
               global exec_req
               global buff_req
               # await response
               # putViewstartup(MY_ADDRESS)
               respFrom = requests.put("http://" + replica + "/key-value-store-view",
                                       json={'socket-address': global_vars.MY_ADDRESS}, timeout=1)
               potential_data = respFrom.json()
               pot_db = potential_data.get('db')
               pot_exec_req = [v for v in potential_data['exec_req'].values()]
               pot_buff_req = [tuple(tup) for tup in potential_data['buff_req'].values()]

               # if len(pot_db) > len(db) and len(pot_exec_req) > len(exec_req) and len(pot_buff_req) > len(buff_req):
               db = pot_db
               exec_req = pot_exec_req
               buff_req = pot_buff_req

            except Exception:
               respFrom = 5
   return 'OK'




# special private endpoint for internal updates/debugging
@app.route('/state-update/<what>', methods=['GET','PUT'])
def update_state(what):
   if request.method == 'GET':
      # get a specific state variable
      response = shard.get_update(what)
   elif request.method == 'PUT':
      # update a specific state variable
      response = shard.put_update(request.data, what)
   else:
      response = Response('This method is unsupported.', status=405)
   return response



# special endpoint to return length of db for keycount
@app.route('/dblen', methods=['GET'])
def get_db_len():
   response = shard.get_db_len()
   return response



# shard operations endpoint
@app.route('/key-value-store-shard/<path:subpath>', methods=['GET', 'PUT'])
@app.route('/key-value-store-shard/<path:subpath>/<shard_id>', methods=['GET', 'PUT'])
def key_value_store_shard(subpath, shard_id='None'):
   # dispatch functions based on subpath
   if (subpath == 'shard-ids'):
      response = shard.get_shard_ids()
      #response = Response('return list of all shard ids.\n', status = 200)
   elif (subpath == 'node-shard-id'):
      response = shard.get_shard_id()
      #response = Response('return shard id of this node.\n', status = 200)
   elif (subpath == 'shard-id-members'):
      response = shard.get_shard_members(shard_id)
      #response = Response('return members of shard ' + shard_id + '.\n', status = 200)
   elif (subpath == 'shard-id-key-count'):
      response = shard.get_key_count(shard_id)
      #response = Response('return number of keys in shard ' + shard_id + '.\n', status = 200)
   # special endpoint helper for shard-id-count
   elif (subpath == 'dblen'):
      response = shard.get_db_len()
   elif (subpath == 'add-member'):
      response = shard.add_member(shard_id, request.data)
      #response = Response('Put the specified node into shard ' + shard_id + '.\n', status = 200)
   elif (subpath == 'reshard'):
      possible_reshard = shard.check_if_possible_reshard(request.data)
      if possible_reshard:
         response = shard.reshard(request.data)
         #response = Response('Rearrange nodes into the specified number of shards.\n', status = 200)
      else:
         response = Response('{"message":"Not enough nodes to provide fault-tolerance with the given shard count!"}\n', status = 400)
   else:
      response = Response('Invalid request', status = 400)

   return response


# database operations endpoint
@app.route('/key-value-store/<key>', methods=['GET', 'PUT', 'DELETE'])
def key_value_store(key):
   # Define default response
   resp_data ={
      'message': 'This method is unsupported.'
   }
   status=405
   # Hash the key and send a request to the specified node
   hash_object = hashlib.md5(key.encode())
   hash_hex = hash_object.hexdigest()
   hashed_key = int(hash_hex, 16)
   # figure out which shard_id the key should go to
   destination_shard = str((hashed_key % int(global_vars.SHARD_COUNT)))

   if request.method == 'GET':
      # if this node is in the destination shard, just execute it
      if(destination_shard == global_vars.shard_id):
         response = keyvalue.getRequest2(key)
      # otherwise send the request to a node in the destination shard
      else:
         # Make sure shard_members has been initialized
         destination_shard_list = global_vars.shard_members.get(str(destination_shard))
         if(destination_shard_list != None):
            # Get the address for a node that contains the key
            destination_node = destination_shard_list[0]
            # Send GET request to that node
            respFrom = requests.get("http://" + destination_node + "/key-value-store/" + key, timeout=1)
            # Craft response from request response
            response = Response(json.dumps(respFrom.json()), status=respFrom.status_code)
         else:
            # resp_data = {
            #    'message': "shard_members list not found"
            # }
            # Update response
            resp_data['message'] = "shard_members list not found"
            status = 404
            response = Response(json.dumps(resp_data), status=status)

   elif request.method == 'PUT':
      # if this node is in the destination shard, just execute it
      if(destination_shard == global_vars.shard_id):
         response = keyvalue.putRequest(key, request)
         return response
      # otherwise send the request to a node in the destination shard
      else:
         # Make sure shard_members has been initialized
         destination_shard_list = global_vars.shard_members.get(str(destination_shard))
         if(destination_shard_list != None):
            # Get the address for a node to put the key
            destination_node = destination_shard_list[0]
            # Send PUT request to that node
            respFrom = requests.put("http://" + destination_node + "/key-value-store/" + key, request.data, timeout=1)
            # Craft response from request response
            response = Response(json.dumps(respFrom.json()), status=respFrom.status_code)
         else:
            # resp_data = {
            #    'message': "shard_id: " + str(global_vars.shard_id) + 'destination_shard:' + str(destination_shard)
            # }
            # Update response
            resp_data['message'] = "shard_members list not found"
            status = 404
            response = Response(json.dumps(resp_data), status=status)


      # check buffer logic

   elif request.method == 'DELETE':
      # if this node is in the destination shard, just execute it
      if(destination_shard == global_vars.shard_id):
         response = keyvalue.deleteRequest(key, request)
      # otherwise send the request to a node in the destination shard
      else:
         # Make sure shard_members has been initialized
         destination_shard_list = global_vars.shard_members.get(str(destination_shard))
         if(destination_shard_list != None):
            # Get the address for a node to delete the key
            destination_node = destination_shard_list[0]
            # Send DELETE request to that node
            respFrom = requests.delete("http://" + destination_node + "/key-value-store/" + key, timeout=1)
            # Craft response from request response
            response = Response(json.dumps(respFrom.json()), status=respFrom.status_code)
         else:
            # resp_data = {
            #    'message': "shard_members list not found"
            # }
            # Update response
            resp_data['message'] = "shard_members list not found"
            status = 404
            response = Response(json.dumps(resp_data), status=status)

   #else:
   #   response = Response('This method is unsupported.', status=405)

   return response

# view operations endpoint
@app.route('/key-value-store-view', methods=['GET', 'PUT', 'DELETE'])
def view_operations():
   if request.method == 'GET':
         #response = backend.getViewList()
         response = view.getViewList()

   elif request.method == 'PUT':
      #response = backend.handlePutView(request)
      response = view.handlePutView(request)

   elif request.method == 'DELETE':
      #response = backend.handleDeleteView(request)
      response = view.handleDeleteView(request)
   return response

if __name__ == '__main__':
   if is_flask_starting(app):
     startup()
   app.run(debug=False, host='0.0.0.0', port=8080)
