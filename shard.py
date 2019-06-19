# shard backend to handle all shar operations
import os
import json
import global_vars
from flask import Flask, Response
import requests
import hashlib


# gets a specific global variable
def get_update(what):
	# default return value
	resp_data = {
		'message': 'Error, unable to GET ' + str(what)
	}
	status = 404
	
	if what == 'db':
		resp_data['message'] = 'Database successfully retrieved'
		resp_data['db'] = global_vars.db
		status = 200
	elif what == 'shard-members':
		resp_data['message'] = 'Shard members successfully retrieved'
		resp_data['shard-members'] = global_vars.shard_members
		status = 200
	elif what == 'all':
		resp_data['message'] = 'All data successfully retrieved'
		resp_data['db'] = global_vars.db
		resp_data['VIEW'] = global_vars.VIEW
		resp_data['shard-id'] = global_vars.shard_id
		resp_data['exec_req'] = global_vars.exec_req
		resp_data['buff_req'] = global_vars.buff_req

		resp_data['shard_members'] = global_vars.shard_members
		resp_data['SHARD_COUNT'] = global_vars.SHARD_COUNT

		status = 200
	
	return Response(json.dumps(resp_data), status=status)

# updates global variables
def put_update(data, what):
	# Specify varibles

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

	new_SHARD_COUNT = jsobj.get('SHARD_COUNT')
	#Define message to be appended to
	message=''
	if new_db != None:
		global_vars.db = new_db
		message += 'db updated, '
	if new_view != None:
		global_vars.VIEW = new_view
		message += 'view updated, '
	if new_shard_id != None:
		global_vars.shard_id = new_shard_id
		message += 'shard-id updated, '
	if new_shard_members != None:
		global_vars.shard_members = new_shard_members
		message += 'shard-members updated, '
	if new_exec_req != None:
		global_vars.exec_req = new_exec_req
		message += 'exec_req updated, '
	if new_buff_req != None:
		global_vars.buff_req = new_buff_req
		message += 'buff_req updated, '
	if new_cmd != None:
		global_vars.cmd = new_cmd
		message += 'cmd updated, '

	if new_SHARD_COUNT != None:
		global_vars.SHARD_COUNT = new_SHARD_COUNT
		message += 'shard count updated, '

	# at this point if db is empty, then this node needs
	# db, exec_req, and buff_req from another member of its shard
	if(not global_vars.db):
		from_node = global_vars.shard_members[str(global_vars.shard_id)][0]
		respFrom = requests.get("http://" + from_node + "/state-update/all")
		jsobj = respFrom.json()
		global_vars.db = jsobj.get('db')
		message += 'db updated from its shard, '
		global_vars.exec_req = jsobj.get('exec_req')
		message += 'exec_req updated from its shard, '
		global_vars.buff_req = jsobj.get('buff_req')
		message += 'buff_req updated from its shard, '

	# Check to see if something was updated
	if message != "":
		resp_data['message'] = message
		status = 200

	return Response(json.dumps(resp_data), status=status)



#returns list of current shard ids
def get_shard_ids():
	#Define default response data
	resp_data = {
		'message':'No Shard Count'
	}
	status = 404
	# If SHARD_COUNT is defined
	if global_vars.SHARD_COUNT != None:
		# Update the response data
		resp_data['message'] = "Shard IDs retrieved successfully"
		resp_data['shard-ids'] = ','.join([str(n) for n in range(int(global_vars.SHARD_COUNT))])
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
	if global_vars.SHARD_COUNT != None:
		# computing the id is deprecated, doesn't work if a node is
		# added later
		id = global_vars.shard_id
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
	members = global_vars.shard_members.get(str(curr_shard))
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
		member = global_vars.shard_members[str(curr_shard)][0]

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
	dblen = len(global_vars.db)
	resp_data = {
		'length': str(dblen)
	}
	status = 200
	return Response(json.dumps(resp_data), status=status)

# given a shard-id, add a new node to the shard (its IP is in data)
def add_member(id, data):
	resp_data = {
		'message': "adding member failed"
	}
	status = 404

	jsobj = json.loads(data)
	socket_address = jsobj.get("socket-address")
	if(socket_address != None):
		# take socket_address and add that node to shard #: id
		# add to shard_members

		global_vars.shard_members[str(id)].append(socket_address)

		# update view
		global_vars.VIEW.append(str(socket_address))

		# send VIEW and shard_members to all nodes
		broadcast_data = {
			'VIEW': global_vars.VIEW,
			'shard-members': global_vars.shard_members,
		}
		for replica in global_vars.VIEW:
			respFrom = requests.put('http://' + replica + '/state-update/blah', json.dumps(broadcast_data), timeout=1)	

		put_data = {
			'shard-id': id,
			'SHARD_COUNT': global_vars.SHARD_COUNT
		}

		# if new node is in the same shard, send db and other necessary stuff
		if(global_vars.shard_id == id):
			put_data['db'] = global_vars.db
			put_data['exec_req'] = global_vars.exec_req
			put_data['buff_req'] = global_vars.buff_req

		respFrom = requests.put('http://' + socket_address + '/state-update/blah', json.dumps(put_data), timeout=1)	

		resp_data = respFrom.json()
		status = respFrom.status_code
	else:
		resp_data['message'] = "no socket address provided"
		status = 409
			
	return Response(json.dumps(resp_data), status=status)

# function to generate shard members db, shard_id, and other metadata
def generate_shards(count):
	#count = SHARD_COUNT
	# needs node's address and view list
	# assumes SHARD_COUNT is defined
	for node in global_vars.VIEW:
		# get current node id
		n_id = int(node.split(':')[0].split('.')[-1])
		# place node in correct shard
		s_id = str(n_id % int(count))
		# check if this is first item in list
		if s_id not in global_vars.shard_members:
			global_vars.shard_members[s_id] = []

		# save address in correct shard
		if(node not in global_vars.shard_members[s_id]):
			global_vars.shard_members[s_id].append(node)

		if node == global_vars.MY_ADDRESS:
			global_vars.shard_id = s_id
			global_vars.node_id = n_id



def reshard(data):
	# Define dict to store all key:value pairs
	all_data_db = {}
	# get all the keys from all the shards
	for i in range(int(global_vars.SHARD_COUNT)):
		# get a replica from shard_members to send GET request
		node = global_vars.shard_members[str(i)][0]
		# send get request to node
		respFrom = requests.get('http://'+node+'/state-update/db')
		a_db = respFrom.json().get('db')

		all_data_db.update(a_db)






	#reset shard members list
	global_vars.shard_members = {}

	#update new shard count
	jsobj = json.loads(data)
	#global_vars.SHARD_COUNT = jsobj.get("SHARD_COUNT")
	global_vars.SHARD_COUNT = jsobj.get("shard-count")

	#generate new shard members list
	generate_shards(global_vars.SHARD_COUNT)

	# Create list of dictionaries to store db partitions
	db_parts = []
	for i in range(int(global_vars.SHARD_COUNT)):
		db_parts.append({})

	# make new db partitions
	for key, val in all_data_db.items():
		hash_object = hashlib.md5(key.encode())
		hash_hex = hash_object.hexdigest()
		hashed_key = int(hash_hex, 16)
		destination_shard = (hashed_key % int(global_vars.SHARD_COUNT))
		db_parts[destination_shard][key] = val

	resp_data = {
		'message': str(global_vars.shard_members),
		'db_parts': str(db_parts)
	}

	# replace local db
	#global_vars.db = db_parts[global_vars.shard_id]
	global_vars.db = db_parts[int(global_vars.shard_id)]

	# send PUT messages to the other nodes
	for k,v in global_vars.shard_members.items():
		for ip in v:
			req_data = {
				#'db': db_parts[k],
				'db': db_parts[int(k)],
				'shard-id': str(k),
				'SHARD_COUNT': str(global_vars.SHARD_COUNT),
				'shard-members': global_vars.shard_members
			}
			respFrom = requests.put('http://'+ip+'/state-update/blah', json.dumps(req_data))

	status = 404


	return Response(json.dumps(resp_data), status=200)



# reshard implementation takes request and checks if it is possible
def check_if_possible_reshard(data):
	# regenerate shard members list
	jsobj = json.loads(data)
	new_shard_count = jsobj.get("shard-count")
	# check if we can generate a new list
	if (len(global_vars.VIEW) // int(new_shard_count)) < 2:
		possible = False
	else:
		possible = True
	#generate_shards(new_shard_count)

	return possible