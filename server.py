import socket
import os
import sys
from flask import Response
import backend

class Request:
	data = None



#MY_ADDRESS = os.environ.get('SOCKET_ADDRESS')
#VIEW = os.environ.get('VIEW').split(',')
HOST = '0.0.0.0'
PORT = 8080

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = (HOST, PORT)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
	# Wait for a connection
	print('waiting for a connection')
	connection, client_address = sock.accept()
	try:
		print('connection from', client_address)
		data = ""
		# Receive the data in small chunks and retransmit it
		data = connection.recv(4096).decode("utf-8")
		# Get the data field from the request
		payload = data.split('\r\n')[-1]
		# Reformate to emulate flask
		request = Request()
		request.data = payload
		# Get the request type and the endpoint
		req_type, endpoint, _ = data.split('\r\n')[0].split(" ")
		print("Request Type: "+req_type)
		print("Endpoint: "+endpoint)
		print("Payload: "+payload)
		# Check if it is a request for key value store
		if endpoint == '/key-value-store-view':
			if req_type == 'GET':
				pass
				#response = backend.getViewList()

			elif req_type == 'PUT':
				pass
				#response = backend.handlePutView(request)
			elif req_type == 'DELETE':
				pass
				#response = backend.handleDeleteView(request)

		loc = endpoint.find('/key-value-store/')
		if loc > -1:
			key = endpoint[loc+len('/key-value-store/'):]
			if req_type == 'GET':
				pass
				response = backend.getRequest(key)

			elif req_type == 'PUT':
				pass
				response = backend.putRequest(key, request)
				print(response)
			# check buffer logic

			elif req_type == 'DELETE':
				pass
				#response = backend.deleteRequest(key)

			else:
				pass
				#response = Response('This method is unsupported.', status=405)


	finally:
		# Clean up the connection
		connection.close()
