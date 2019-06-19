# view_ops.py
# extracting view operations code from backend into its own module

from flask import Response, request, jsonify, json
import requests
import os
import time
import threading
import random
import collections

from global_vars import VIEW, MY_ADDRESS, exec_req, buff_req, db
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