# backend.py
# Trying to store everything in one file because we were having lots of annoying problems
from flask import Response, request, jsonify, json
import requests
import os
import time
import threading
import random
import collections
import hashlib
# -----------------------------------------------
# GLOBAL VARIABLES:
# Having to do with key-value operations:
db = {}
exec_req = []
buff_req = []
counter = None

#Temp variables for testing
potential_data = None
pot_db = {"fake_key":"fake_val"}

# retrieve this replicas socket address from environment variable
MY_ADDRESS = os.environ.get('SOCKET_ADDRESS')
# retrieveing view list from environment vairable
VIEW = os.environ.get('VIEW').split(',')

# Initialize counter with last digit from ip (assuming we will always use these test IPs, otherwise
# if we want to generalize we just increment counter everytime by 256 instead of by number of replicas.)
counter = VIEW.index(MY_ADDRESS)
counter_offset = len(VIEW)  # Change len(VIEW) to 256 for general case
# -----------------------------------------------

# -----------------------------------------------
# Having to do with shards
# initial shard count global variable
SHARD_COUNT = os.environ.get('SHARD_COUNT')

# global shard structures
node_id = 0
shard_id = 0
shard_members = {}
# -----------------------------------------------

########################################################################################
# /key-value-store-shard################################################################
########################################################################################
# shard backend to handle all shar operations

# gets a specific global variable
def get_update(what):
	# default return value
	resp_data = {
		'message': 'Error, unable to GET ' + what
	}
	status = 404
	
	if what == 'db':
		resp_data['message'] = 'Database successfully retrieved'
		resp_data['db'] = db
		status = 200
	elif what == 'shard-members':
		resp_data['message'] = 'Shard members successfully retrieved'
		resp_data['shard-members'] = shard_members
		status = 200
	elif what == 'all':
		resp_data['message'] = "All data received"
		resp_data['db'] = db
		resp_data['shard-id'] = shard_id
		resp_data['shard-members'] = shard_members
		status=200
	
	return Response(json.dumps(resp_data), status=status)

# updates global variables
def put_update(data):
	# Specify varibles
	global db
	global VIEW
	global shard_id
	global shard_members
	global exec_req
	global buff_req
	global cmd

	# Define default return value
	resp_data = {
		'message': 'Error, unable to PUT update'
	}
	status = 404
	
	# load data from payload
	jsobj = json.loads(data)
	# Parse the data from the payload
	new_db = jsobj.get('db')
	new_view = jsobj.get('VIEW')
	new_shard_id = jsobj.get('shard-id')
	new_shard_members = jsobj.get('shard-members')
	new_exec_req = jsobj.get('exec_req')
	new_buff_req = jsobj.get('buff_req')
	new_cmd = jsobj.get('cmd')
	#Define message to be appended to
	message=''
	if new_db != None:
		db = new_db
		message += 'db updated, '
	if new_view != None:
		VIEW = new_view
		message += 'view updated, '
	if new_shard_id != None:
		shard_id = new_shard_id
		message += 'shard-id updated, '
	if new_shard_members != None:
		shard_members = new_shard_members
		message += 'shard-members updated, '
	if new_exec_req != None:
		exec_req = new_exec_req
		message += 'exec_req updated, '
	if new_buff_req != None:
		buff_req = new_buff_req
		message += 'buff_req updated, '
	if new_cmd != None:
		cmd = new_cmd
		message += 'cmd updated, '
	# Check to see if something was updated
	if message != "":
		resp_data['message'] = message
		status = 200
	
	return Response(json.dumps(resp_data), status = status)
	
	#return Response(json.dumps(resp_data), status=status)

#returns list of current shard ids
def get_shard_ids():
	#Define default response data
	resp_data = {
		'message':'No Shard Count'
	}
	status = 404
	# If SHARD_COUNT is defined
	if SHARD_COUNT != None:
		# Update the response data
		resp_data['message'] = "Shard IDs retrieved successfully"
		resp_data['shard-ids'] = ','.join([str(n) for n in range(int(SHARD_COUNT))])
		status = 200

	return Response(json.dumps(resp_data), status=status)


#returns shard id that current node is in
def get_shard_id():
	# Define default response data
	resp_data = {
		'message':'No shard id'
	}
	status = 404
	# Make sure SHARD COUNT has been initialized
	if SHARD_COUNT != None:
		# Compute simple id
		id = node_id % int(SHARD_COUNT)
		# Update the response data
		resp_data['message'] = "Shard ID of the node retrieved successfully"
		resp_data['shard-id'] = str(id)
		status = 200

	return Response(json.dumps(resp_data), status=status)


#returns list of members of shard
def get_shard_members(curr_shard):
	#Define default response data
	resp_data = {
		'message':'No Shard Member List'
	}
	status = 404
	# Get the members of the given shard
	members = shard_members.get(int(curr_shard))
	# Make sure members isn't None
	if members != None:
		# Update the response data
		resp_data['message'] = "Members of shard ID retrieved successfully"
		resp_data['shard-id-members'] = ','.join(members)
		status = 200
	
	return Response(json.dumps(resp_data), status=status)

#returns number of keys stored in this shard
def get_key_count(curr_shard):
	try:
		member = shard_members[int(curr_shard)][0]
		# member should have IP of first node in the shard
		# send request to that IP for length of its db
		'''
		resp_data = {
			'message': 'Node studied: ' + str(member)
		}
		'''
		# send request to member for its dblen
		respFrom = requests.get("http://"+member+"/key-value-store-shard/dblen", json={'broadcast': False} ,timeout=1)
		# grab dblen from respFrom
		respJson = respFrom.json()
		keycount = respJson.get("length")
		status = 200
		resp_data = {
			'message': 'Key count of shard ID returned successfully',
			'shard-id-key-count': ''+str(keycount)+''
		}
	except KeyError:
		resp_data = {
			'message': 'shard id ' + str(curr_shard) + ' not recognized'
		}
		status = 404
	return Response(json.dumps(resp_data), status=status)

#helper function for get_key_count
def get_db_len():
	dblen = len(db)
	resp_data = {
		'length': str(dblen)
	}
	status = 200
	return Response(json.dumps(resp_data), status=status)





# function to generate shard members db, shard_id, and other metadata
def generate_shards(count):
	# needs node's address and view list
	global shard_id
	global shard_members
	global node_id
	# assumes SHARD_COUNT is defined
	for node in VIEW:
		# get current node id
		n_id = int(node.split(':')[0].split('.')[-1])
		# place node in correct shard
		s_id = n_id % int(count)
		# check if this is first item in list
		if s_id not in shard_members:
			shard_members[s_id] = []
		# save address in correct shard
		shard_members[s_id].append(node)
		# check if this is our address
		# deferred import to avoid circular dependency
		from keyvalue import MY_ADDRESS
		if node == MY_ADDRESS:
			shard_id = s_id
			node_id = n_id


########################################################################################
# /key-value-store################################################################
########################################################################################

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
def startup():
   # we start up normally
   if SHARD_COUNT is not None:
     generate_shards(SHARD_COUNT)
   # we must find out where we belong
   else:
     pass

   broadcast = False
   # get random replica address to compare our views
   while True:
      replica = random.choice(VIEW)
      if replica != MY_ADDRESS:
         try:
            # get another replica's view
            viewData = requests.get("http://" + replica + "/key-value-store-view", timeout=1)
            jsobj = viewData.json()
            otherView = jsobj.get("view")
            viewList = otherView.split(',')
            # check if we are a new replica
            if collections.Counter(viewList) != collections.Counter(VIEW):
               broadcast = True
         except Exception: 
            viewData = None
         break

   # if we are a new replica broadcast existence
   if broadcast:    
      for replica in VIEW:
         if replica != MY_ADDRESS:
            try:
               global potential_data
               global pot_db
               global db
               global exec_req
               global buff_req
               # await response
               #putViewstartup(MY_ADDRESS)
               respFrom = requests.put("http://" + replica + "/key-value-store-view",json={'socket-address': MY_ADDRESS}, timeout=1)
               potential_data = respFrom.json()
               pot_db = potential_data.get('db')
               pot_exec_req = [ v for v in potential_data['exec_req'].values()]
               pot_buff_req = [tuple(tup) for tup in potential_data['buff_req'].values()]
               
               #if len(pot_db) > len(db) and len(pot_exec_req) > len(exec_req) and len(pot_buff_req) > len(buff_req):
               db = pot_db
               exec_req = pot_exec_req
               buff_req = pot_buff_req

            except Exception:
               respFrom = 5
   return 'OK'

def repPutBroad(key, value, cmd, req_id):
   #for replica in VIEW:
   # broadcast only to members of its own shard
   myshard = shard_members[shard_id]
   
   for replica in myshard:
      if replica != MY_ADDRESS:
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
   #tup = (val, cmd, req_id)
   tup = (val, new_cmd, req_id)

   if key in db.keys():
      response = Response(
         '{"message":"Updated successfully","version": "' + str(req_id) + '", "causal-metadata": "' + str(new_cmd)+ '", "shard-id": ' + '"' + str(shard_id) + '"' + '}\n', status = 200)
   else:
      response = Response(
         '{"message":"Added successfully","version": "' + str(req_id) + '", "causal-metadata": "' + str(new_cmd)+ '", "shard-id": ' + '"' + str(shard_id) + '"' + '}\n', status = 201)

   # deliver request
   db[key] = tup
   exec_req.append(req_id)
   # broadcast to other replicas?
   repPutBroad(key, val, cmd, req_id)
   
   return response

# the same as exec_known_valid_request, except it only does database
# entry operations
def exec_buffered_request(key, val, cmd, req_id):
    tup = (val, cmd, req_id)
    # deliver request
    db[key] = tup
    exec_req.append(req_id)
    # broadcast to other replicas?
    #repPutBroad(key, val, new_cmd, req_id)
    repPutBroad(key, val, cmd, req_id)

# Checks if any requests in the buffer can be executed
# If it finds one, it is executed and returns True
# If no requests in the buffer can be executed, returns False


def checkBuffer():
    for r in buff_req:
        key = r[0]
        val = r[1]
        cmd = r[2]
        req_id = r[3]
        can_execute = True
        for v in cmd:  # for each version # in cmd
            if v not in exec_req:
                can_execute = False
                break
        if can_execute:
            # remove this request from the buffer
            # and execute it
            buff_req.remove(r)
            exec_buffered_request(key, val, cmd, req_id)
            return True

    return False


# Assumes PUT requests enter info into the database in this format:
# 'key': (value, [dependency-list], id#)
# ex: db = {'x': ("A", [], 0), 'y': ("B", [0], 2)}
def getRequest(key):
    # Hash the key and send a request to the specified node
    hash_object = hashlib.md5(key.encode())
    hash_hex = hash_object.hexdigest()
    hashed_key = int(hash_hex, 16)
    # figure out which shard_id the key should go to
    destination_shard = (hashed_key % int(SHARD_COUNT))

    # special case to serve the entire database
    if(key == "everything"):
      data={
         "message":"Replica added successfully to the view",
         "db":json.dumps(db),
         "exec_req":",".join([str(n) for n in exec_req]),
         "buff_req":json.dumps({i:tup for i, tup in enumerate(buff_req)}),
         "pot_data": "None" if potential_data == None else json.dumps(potential_data),
         "pot_db": "None" if pot_db == None else json.dumps(pot_db)
      }
      response = Response(json.dumps(data)+'\n', status=250)
      return response

    # if this node is in the destination shard, just execute it
    if(destination_shard == shard_id):
        response = localGet(key)
    # otherwise send the request to a node in the destination shard
    else:
        destination_shard_list = shard_members.get(int(destination_shard))
        if(destination_shard_list != None):
           #destination_node = destination_shard_list[0]
           #response = requests.get("http://" + destination_node + "/key-value-store/" + key, timeout=1)
           destination_node = destination_shard_list[0]
           respFrom = requests.get("http://" + destination_node + "/key-value-store/" + key, timeout=1)
           respJson = respFrom.json()
           resp_message = respJson.get("message")
           resp_version = respJson.get("version")
           resp_causal_metadata = respJson.get("causal-metadata")
           #resp_shard_id = respJson.get("shard-id")
           resp_value = respJson.get("value")
           status = respFrom.status_code
           resp_data = {
              'message': resp_message,
              'version': resp_version,
              'causal-metadata': resp_causal_metadata,
              #'shard-id': resp_shard_id
              'value': resp_value 
           }
           response = Response(json.dumps(resp_data), status=status)
        else:
            resp_data = {
                'message': "shard_members list not found"
            }
            status = 404
            response = Response(json.dumps(resp_data), status=status)
    return response
      
def localGet(key):
    # retrieve key from store
    data = db.get(key)
    # existing key response
    if data is not None:
        # convert value to json object for response
        value = data[0]
        cmd = data[1]
        req_id = data[2]
        json_response = '{"message":"Retrieved successfully", "version": ' + str(req_id) + ', "causal-metadata": ' + str(cmd) + ', "value": "' + str(value) + '", "shard-id": ' + '"' + str(shard_id) + '"' + '}\n'
        code = 200
    # non-existing key response
    else:
        # set error message in json
        # check if db is empty or if it just can't find the key
        if not db:
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
   '''
   if shouldBuffer(cmd_lst, exec_req):
      buff_req.append((key, val, cmd, req_id))
      response = Response('{"message":"Buffered your broadcast"}\n', status=206)
   '''
   #else:
   # need to attach req_id to cmd before storing
   # add check if cmd is empty, if not then attach ", str(req_id)"
   cmd += str(req_id)
   tup = (val, cmd, req_id)
   db[key] = tup
   exec_req.append(req_id)
   response = Response('{"message":"Thank for the broadcast"}\n', status=200)
   return response

def handleClientPut(key, val, cmd, cmd_lst):
   '''
   if shouldBuffer(cmd_lst, exec_req):
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
      buff_req.append((key, val, new_cmd, req_id))

      if key in db.keys():
         response = Response('{"message":"Buffered update","version": '+str(req_id)+',"causal-metadata":"'+str(new_cmd)+'"}\n', status=300)
      else:
         response = Response('{"message":"Buffered initial add","version":'+str(req_id)+',"causal-metadata":"'+str(new_cmd)+'"}\n', status=301)
   '''
   #else:
   response = exec_known_valid_request(key, val, cmd)

   # checks buffer for any requests that can now be executed
   # after exec_req has the new request
   while checkBuffer():
      pass
   return response

def putRequest(key, request):
   # Hash the key and send a request to the specified node
   hash_object = hashlib.md5(key.encode())
   hash_hex = hash_object.hexdigest()
   hashed_key = int(hash_hex, 16)
   # figure out which shard_id the key should go to
   destination_shard = (hashed_key % int(SHARD_COUNT))
   #data = str(request.data)
   if(destination_shard == shard_id):
       response = localPut(key, request)
   else:
        destination_shard_list = shard_members.get(int(destination_shard))
        if(destination_shard_list != None):
            destination_node = destination_shard_list[0]
            respFrom = requests.put("http://" + destination_node + "/key-value-store/" + key, request.data, timeout=1)
            respJson = respFrom.json()
            resp_message = respJson.get("message")
            resp_version = respJson.get("version")
            resp_causal_metadata = respJson.get("causal-metadata")
            resp_shard_id = respJson.get("shard-id")
            status = respFrom.status_code
            resp_data = {
               'message': resp_message,
               'version': resp_version,
               'causal-metadata': resp_causal_metadata,
               'shard-id': resp_shard_id
            }
            response = Response(json.dumps(resp_data), status=status)
        else:
            resp_data = {
                'message': "shard_members list not found"
            }
            status = 404
            response = Response(json.dumps(resp_data), status=status)
   return response


def localPut(key, request):
   fromClient = False
   # can tell if request comes from client (no version attached)
   # or from another replica (version attached)
   try:
      jsobj = json.loads(request.data)
      req_id = jsobj["version"]
   except Exception:
      fromClient = True
   # catches malformed PUT requests
   try:
      jsobj = json.loads(request.data)
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

   # Hash the key and send a request to the specified node
   hash_object = hashlib.md5(key.encode())
   hash_hex = hash_object.hexdigest()
   hashed_key = int(hash_hex, 16)
   # figure out which shard_id the key should go to
   destination_shard = (hashed_key % int(SHARD_COUNT))
   if(destination_shard == shard_id):
       response = localDelete(key, request)
   else:
       destination_shard_list = shard_members.get(int(destination_shard))
       if(destination_shard_list != None):
          destination_node = destination_shard_list[0]
          #response = requests.delete("http://" + destination_node + "/key-value-store/" + key, timeout=1)
          destination_node = destination_shard_list[0]
          respFrom = requests.delete("http://" + destination_node + "/key-value-store/" + key, request.data, timeout=1)
            
          respJson = respFrom.json()
          resp_message = respJson.get("message")
          resp_version = respJson.get("version")
          resp_causal_metadata = respJson.get("causal-metadata")
          resp_shard_id = respJson.get("shard-id")
          status = respFrom.status_code
          resp_data = {
             'message': resp_message,
             'version': resp_version,
             'causal-metadata': resp_causal_metadata,
             'shard-id': resp_shard_id
          }
          response = Response(json.dumps(resp_data), status=status)
       else:
            resp_data = {
                'message': "shard_members list not found"
            }
            status = 404
            response = Response(json.dumps(resp_data), status=status)
   return response

def localDelete(key, request):
   json_response = ''
   # if the key exists
   if(db.get(key) != None):
      del db[key]
      json_response = '{"doesExist":true,"message":"Deleted successfully", "shard-id": ' + '"' + str(shard_id) + '"' + '}'
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
      myshard = shard_members[shard_id]
      for replica in myshard:
         respFrom = requests.delete("http://"+replica+"/key-value-store/"+str(key), 
            json={'broadcast': False} ,timeout=1)

   return response





########################################################################################
# /key-value-store-view ################################################################
########################################################################################
# view GET request
def getViewList():
	# Define the response data
	resp_data ={
		'message':"View retrieved successfully",
		'view':','.join(VIEW)
	}
	# Return the response
	return Response(json.dumps(resp_data), status=200)

# internal put view function
def putView(ip, broadcast=False):
   # add view 
   VIEW.append(ip)

   # check for broadcast
   if broadcast:
      # if true send to all other replicas
      for replica in VIEW:
         if replica != MY_ADDRESS:
            # send message to replicas
            try:
               # await response
               respFrom = requests.put("http://"+replica+"/key-value-store-view", 
                  '{"socket-address":'+ip+'}',timeout=1)
            except Exception:
               # cancel current broadcast and broadcast local update
               removeView(replica, True)

# view PUT request
def handlePutView(request):
   data = str(request.data)
   try:
      jsobj = json.loads(data)
      addr = jsobj["socket-address"]
      if addr not in VIEW:
         putView(addr)
         exec_req_str = json.dumps({i:n for i,n in enumerate(exec_req)})
         response = Response('{"message":"Replica added successfully to the view","exec_req":' + str(exec_req_str) +',"buff_req":' + json.dumps({i:tup for i,tup in enumerate(buff_req)}) + ',"db":' +json.dumps(db) + '}\n',status=200, mimetype='application/json')
         #response = Response(json.dumps(data)+'\n', status=200)
      else:
         response = Response('{"error":"Socket address already exists in the view","message":"Error in PUT"}\n', status=404)
   except Exception:
      response = Response('{"error":"Value is missing","message":"Error in PUT"}\n', status=400)

   return response

# internal delete view function
def removeView(ip, broadcast=False):
   # remove view locally
   # TODO: check for potentially not in our view
   VIEW.remove(ip)

   # check for broadcast
   if broadcast:
      # if true send to all other replicas
      for replica in VIEW:
         if replica != MY_ADDRESS:
            # send message to replicas
            # if two replicas go down before a put is sent, it crashes
            # here.
            try:
               respFrom = requests.delete("http://"+replica+"/key-value-store-view",json={'socket-address': ip}, timeout=1)

            except Exception:
               removeView(replica, False)

# view DELETE request
def handleDeleteView(request):
	# Define (default) response data 
	resp_data = {
		'message':"Error in DELETE",
		'error':"Value is missing"
	}
	# Define default status code
	status = 400 
	# Parse the request data
	data = str(request.data)
	try:
		jsobj = json.loads(data)
		addr = jsobj.get("socket-address")
		internal = jsobj.get('internal')
		if addr in VIEW:
			# Delete the view locally
			VIEW.remove(addr)
			# Determine if we need to broadcast
			if internal == None:
				# Broadcast to all replicas in VIEW that aren't this replica
				for replica in VIEW:
					if replica != MY_ADDRESS:
						# Define the url to request from
						req_url = "http://"+replica+"/key-value-store-view"
						# Define the data to be sent in the request
						req_data = {
							'socket-address': addr,
							'internal': 'True'
						}
						# if two replicas go down before a put is sent, it crashes
						# here.
						try:
							respFrom = requests.delete(req_url,json=req_data, timeout=1)
						# If we never get a response we assume that replica is dead
						except Exception:
							removeView(replica, True)
			# Update the response data for case replica deleted successfully
			resp_data['message']="Replica deleted successfully from the view"
			del resp_data['error']
			status=200
		else:
			# Update the response data for case address DNE in the view
			resp_data['error']="Socket address does not exist in the view"
			resp_data['message']="Error in DELETE"
			status=404
	except Exception:
		pass
	# Return the response
	return Response(json.dumps(resp_data), status=status)
########################################################################################
# /key-value-store-view ################################################################
########################################################################################