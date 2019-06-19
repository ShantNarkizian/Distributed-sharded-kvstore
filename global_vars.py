# global_vars.py
# holds global variables for everything to import
import os
# GLOBAL VARIABLES:
# -----------------------------------------------
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
#usage {'0':['10.10.0.2', '10.10.0.5'],
#		'1':['10.10.0.3', '10.10.0.6'],
#}
# -----------------------------------------------