import unittest
import requests
import time
import os

######################## initialize variables ################################################
subnetName = "assignment4-net"
subnetAddress = "10.10.0.0/16"

replica1Ip = "10.10.0.2"
replica1HostPort = "8082"
replica1SocketAddress = replica1Ip + ":8080"

replica2Ip = "10.10.0.3"
replica2HostPort = "8083"
replica2SocketAddress = replica2Ip + ":8080"

replica3Ip = "10.10.0.4"
replica3HostPort = "8084"
replica3SocketAddress = replica3Ip + ":8080"

replica4Ip = "10.10.0.5"
replica4HostPort = "8085"
replica4SocketAddress = replica4Ip + ":8080"

replica5Ip = "10.10.0.6"
replica5HostPort = "8086"
replica5SocketAddress = replica5Ip + ":8080"

replica6Ip = "10.10.0.7"
replica6HostPort = "8087"
replica6SocketAddress = replica6Ip + ":8080"

replica7Ip = "10.10.0.8"
replica7HostPort = "8088"
replica7SocketAddress = replica7Ip + ":8080"

replica8Ip = "10.10.0.9"
replica8HostPort = "8089"
replica8SocketAddress = replica8Ip + ":8080"

view6 = replica1SocketAddress + "," + replica2SocketAddress + "," + replica3SocketAddress + ',' + replica4SocketAddress + ',' + replica5SocketAddress + ',' + replica6SocketAddress

view8 = replica1SocketAddress + "," + replica2SocketAddress + "," + replica3SocketAddress + ',' + replica4SocketAddress + ',' + replica5SocketAddress + ',' + replica6SocketAddress + ',' + replica7SocketAddress + ',' + replica8SocketAddress

############################### Docker Linux Commands ###########################################################
def removeSubnet(subnetName):
    command = "docker network rm " + subnetName
    os.system(command)
    time.sleep(2)

def createSubnet(subnetAddress, subnetName):
    command  = "docker network create --subnet=" + subnetAddress + " " + subnetName
    os.system(command)
    time.sleep(2)

def buildDockerImage():
    command = "docker build -t assignment4-img ."
    os.system(command)

def runReplica(hostPort, ipAddress, subnetName, instanceName, shardCount,view):
    command = "docker run -d -p " + hostPort + ":8080 --net=" + subnetName + " --ip=" + ipAddress + " --name=" + instanceName + " -e SOCKET_ADDRESS=" + ipAddress + ":8080" + " -e VIEW=" + view + " -e SHARD_COUNT=" + str(shardCount) +" assignment4-img"
    os.system(command)
    time.sleep(10)

def stopAndRemoveInstance(instanceName):
    stopCommand = "docker stop " + instanceName
    removeCommand = "docker rm " + instanceName
    os.system(stopCommand)
    time.sleep(2)
    os.system(removeCommand)

def connectToNetwork(subnetName, instanceName):
    command = "docker network connect " + subnetName + " " + instanceName
    os.system(command)

def disconnectFromNetwork(subnetName, instanceName):
    command = "docker network disconnect " + subnetName + " " + instanceName
    os.system(command)

def dockerSystemPrune():
    command = "docker system prune -f"
    os.system(command)
################################# Unit Test Class ############################################################

class TestHW3(unittest.TestCase):

    ######################## Build docker image and create subnet ################################
    print("###################### Building Dokcer image ######################\n")
    # build docker image
    buildDockerImage()

    print("###################### Killing nodes and pruning ######################\n")
    stopAndRemoveInstance("replica1")
    stopAndRemoveInstance("replica2")
    stopAndRemoveInstance("replica3")
    stopAndRemoveInstance("replica4")
    stopAndRemoveInstance("replica5")
    stopAndRemoveInstance("replica6")
    stopAndRemoveInstance("replica7")
    stopAndRemoveInstance("replica8")
    stopAndRemoveInstance("node1")
    stopAndRemoveInstance("node2")
    stopAndRemoveInstance("node3")
    stopAndRemoveInstance("node4")
    stopAndRemoveInstance("node5")
    stopAndRemoveInstance("node6")
    stopAndRemoveInstance("node7")
    stopAndRemoveInstance("node8")
    dockerSystemPrune()

    ########################## Run tests #######################################################
    # Shard operations senario a
     
    def test_a_shard_operations(self):
        # Define local variables
        numberOfShards = 2

        # stop and remove containers from possible previous runs
        print("\n###################### Stopping and removing containers from previous run ######################\n")
        stopAndRemoveInstance("replica1")
        stopAndRemoveInstance("replica2")
        stopAndRemoveInstance("replica3")
        stopAndRemoveInstance("replica4")
        stopAndRemoveInstance("replica5")
        stopAndRemoveInstance("replica6")
        stopAndRemoveInstance("replica7")
        stopAndRemoveInstance("replica8")

        print("\n###################### Creating the subnet ######################\n")
        # remove the subnet possibly created from the previous run
        removeSubnet(subnetName)

        # create subnet
        createSubnet(subnetAddress, subnetName)

        #run instances
        print("\n###################### Running replicas ######################\n")
        runReplica(replica1HostPort, replica1Ip, subnetName, "replica1", numberOfShards, view6)
        runReplica(replica2HostPort, replica2Ip, subnetName, "replica2", numberOfShards, view6)
        runReplica(replica3HostPort, replica3Ip, subnetName, "replica3", numberOfShards, view6)
        runReplica(replica4HostPort, replica4Ip, subnetName, "replica4", numberOfShards, view6)
        runReplica(replica5HostPort, replica5Ip, subnetName, "replica5", numberOfShards, view6)
        runReplica(replica6HostPort, replica6Ip, subnetName, "replica6", numberOfShards, view6)

        print("\n###################### Getting the shard IDs from replica1 ######################\n")
        # Get the shard IDs from replica1
        response = requests.get('http://localhost:8082/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica2 ######################\n")
        # Get the shard IDs from replica2
        response = requests.get('http://localhost:8083/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica3 ######################\n")
        # Get the shard IDs from replica3
        response = requests.get('http://localhost:8084/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica4 ######################\n")
        # Get the shard IDs from replica4
        response = requests.get('http://localhost:8085/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica5 ######################\n")
        # Get the shard IDs from replica5
        response = requests.get('http://localhost:8086/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica6 ######################\n")
        # Get the shard IDs from replica6
        response = requests.get('http://localhost:8087/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting members of shard from replica1 ###################\n")
        # Define a dictionary to store shards and their members
        shard_members = {}
        # Get the members of shard 0 from replica1
        response = requests.get('http://localhost:8082/key-value-store-shard/shard-id-members/0')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Add shards to dictionary
        shard_members[0] = responseInJson.get('shard-id-members')

        # Get the members of shard 1 from replica1
        response = requests.get('http://localhost:8082/key-value-store-shard/shard-id-members/1')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Add shards to dictionary
        shard_members[1] = responseInJson.get('shard-id-members')
        # Print the shard member list that comparisions will be based on
        print("Shard Members Dict: ")
        print(shard_members)

        print("\n###################### Getting and comparing members of shard from replica2 ###################\n")
        # Get the members of shard 0 from replica2
        response = requests.get('http://localhost:8083/key-value-store-shard/shard-id-members/0')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Verify dictionary matches response
        self.assertEqual(responseInJson.get('shard-id-members'),shard_members[0])

        # Get the members of shard 1 from replica2
        response = requests.get('http://localhost:8083/key-value-store-shard/shard-id-members/1')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Add shards to dictionary
        self.assertEqual(responseInJson.get('shard-id-members'),shard_members[1])

        print("\n###################### Getting and comparing members of shard from replica3 ###################\n")
        # Get the members of shard 0 from replica3
        response = requests.get('http://localhost:8084/key-value-store-shard/shard-id-members/0')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Verify dictionary matches response
        self.assertEqual(responseInJson.get('shard-id-members'),shard_members[0])

        # Get the members of shard 1 from replica3
        response = requests.get('http://localhost:8084/key-value-store-shard/shard-id-members/1')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Add shards to dictionary
        self.assertEqual(responseInJson.get('shard-id-members'),shard_members[1])

        print("\n###################### Getting and comparing members of shard from replica4 ###################\n")
        # Get the members of shard 0 from replica4
        response = requests.get('http://localhost:8085/key-value-store-shard/shard-id-members/0')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Verify dictionary matches response
        self.assertEqual(responseInJson.get('shard-id-members'),shard_members[0])

        # Get the members of shard 1 from replica4
        response = requests.get('http://localhost:8085/key-value-store-shard/shard-id-members/1')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Add shards to dictionary
        self.assertEqual(responseInJson.get('shard-id-members'),shard_members[1])

        print("\n###################### Getting and comparing members of shard from replica5 ###################\n")
        # Get the members of shard 0 from replica5
        response = requests.get('http://localhost:8086/key-value-store-shard/shard-id-members/0')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Verify dictionary matches response
        self.assertEqual(responseInJson.get('shard-id-members'),shard_members[0])

        # Get the members of shard 1 from replica5
        response = requests.get('http://localhost:8086/key-value-store-shard/shard-id-members/1')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Add shards to dictionary
        self.assertEqual(responseInJson.get('shard-id-members'),shard_members[1])

        print("\n###################### Getting and comparing members of shard from replica6 ###################\n")
        # Get the members of shard 0 from replica6
        response = requests.get('http://localhost:8087/key-value-store-shard/shard-id-members/0')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Verify dictionary matches response
        self.assertEqual(responseInJson.get('shard-id-members'),shard_members[0])

        # Get the members of shard 1 from replica6
        response = requests.get('http://localhost:8087/key-value-store-shard/shard-id-members/1')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Add shards to dictionary
        self.assertEqual(responseInJson.get('shard-id-members'),shard_members[1])

        print('\n####################### Getting replica1 shard id ###########################\n')
        response = requests.get('http://localhost:8082/key-value-store-shard/node-shard-id')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        print("Shard ID: "+str(responseInJson['shard-id']))

        print('\n####################### Getting replica2 shard id ###########################\n')
        response = requests.get('http://localhost:8083/key-value-store-shard/node-shard-id')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        print("Shard ID: "+str(responseInJson['shard-id']))

        print('\n####################### Getting replica3 shard id ###########################\n')
        response = requests.get('http://localhost:8084/key-value-store-shard/node-shard-id')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        print("Shard ID: "+str(responseInJson['shard-id']))

        print('\n####################### Getting replica4 shard id ###########################\n')
        response = requests.get('http://localhost:8085/key-value-store-shard/node-shard-id')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        print("Shard ID: "+str(responseInJson['shard-id']))

        print('\n####################### Getting replica5 shard id ###########################\n')
        response = requests.get('http://localhost:8086/key-value-store-shard/node-shard-id')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        print("Shard ID: "+str(responseInJson['shard-id']))

        print('\n####################### Getting replica6 shard id ###########################\n')
        response = requests.get('http://localhost:8087/key-value-store-shard/node-shard-id')
        responseInJson = response.json()
        # Check status code
        self.assertEqual(response.status_code, 200)
        print("Shard ID: "+str(responseInJson['shard-id']))
    
    
#############################################################################################################################################
    # Shard operations senario b
    
    def test_b_shard_operations(self):
        # Define local variables
        numberOfShards = 3

        # stop and remove containers from possible previous runs
        print("\n###################### Stopping and removing containers from previous run ######################\n")
        stopAndRemoveInstance("replica1")
        stopAndRemoveInstance("replica2")
        stopAndRemoveInstance("replica3")
        stopAndRemoveInstance("replica4")
        stopAndRemoveInstance("replica5")
        stopAndRemoveInstance("replica6")
        stopAndRemoveInstance("replica7")
        stopAndRemoveInstance("replica8")

        print("\n###################### Creating the subnet ######################\n")
        # remove the subnet possibly created from the previous run
        removeSubnet(subnetName)

        # create subnet
        createSubnet(subnetAddress, subnetName)

        #run instances
        print("\n###################### Running replicas ######################\n")
        runReplica(replica1HostPort, replica1Ip, subnetName, "replica1", numberOfShards, view8)
        runReplica(replica2HostPort, replica2Ip, subnetName, "replica2", numberOfShards, view8)
        runReplica(replica3HostPort, replica3Ip, subnetName, "replica3", numberOfShards, view8)
        runReplica(replica4HostPort, replica4Ip, subnetName, "replica4", numberOfShards, view8)
        runReplica(replica5HostPort, replica5Ip, subnetName, "replica5", numberOfShards, view8)
        runReplica(replica6HostPort, replica6Ip, subnetName, "replica6", numberOfShards, view8)
        runReplica(replica7HostPort, replica7Ip, subnetName, "replica7", numberOfShards, view8)
        runReplica(replica8HostPort, replica8Ip, subnetName, "replica8", numberOfShards, view8)

        print("\n###################### Getting the shard IDs from replica1 ######################\n")
        # Get the shard IDs from replica1
        response = requests.get('http://localhost:8082/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica2 ######################\n")
        # Get the shard IDs from replica2
        response = requests.get('http://localhost:8083/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica3 ######################\n")
        # Get the shard IDs from replica3
        response = requests.get('http://localhost:8084/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica4 ######################\n")
        # Get the shard IDs from replica4
        response = requests.get('http://localhost:8085/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica5 ######################\n")
        # Get the shard IDs from replica5
        response = requests.get('http://localhost:8086/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica6 ######################\n")
        # Get the shard IDs from replica6
        response = requests.get('http://localhost:8087/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica7 ######################\n")
        # Get the shard IDs from replica6
        response = requests.get('http://localhost:8088/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )

        print("\n###################### Getting the shard IDs from replica8 ######################\n")
        # Get the shard IDs from replica6
        response = requests.get('http://localhost:8089/key-value-store-shard/shard-ids')
        responseInJson = response.json()
        print("Received shard ids: "+ responseInJson.get('shard-ids'))
        # Check status code
        self.assertEqual(response.status_code, 200)
        # Check that shard ids are unique and have the correct number of them
        self.assertEqual(len(set(responseInJson['shard-ids'].split(','))),numberOfShards )
    
    # attempting to test get_key_count on each shard
    def test_c_shard_operations(self):
        # Define local variables
        numberOfShards = 3

        # stop and remove containers from possible previous runs
        print("\n###################### Stopping and removing containers from previous run ######################\n")
        stopAndRemoveInstance("replica1")
        stopAndRemoveInstance("replica2")
        stopAndRemoveInstance("replica3")
        stopAndRemoveInstance("replica4")
        stopAndRemoveInstance("replica5")
        stopAndRemoveInstance("replica6")
        stopAndRemoveInstance("replica7")
        stopAndRemoveInstance("replica8")

        print("\n###################### Creating the subnet ######################\n")
        # remove the subnet possibly created from the previous run
        removeSubnet(subnetName)

        # create subnet
        createSubnet(subnetAddress, subnetName)

        #run instances
        print("\n###################### Running replicas ######################\n")
        runReplica(replica1HostPort, replica1Ip, subnetName, "replica1", numberOfShards, view8)
        runReplica(replica2HostPort, replica2Ip, subnetName, "replica2", numberOfShards, view8)
        runReplica(replica3HostPort, replica3Ip, subnetName, "replica3", numberOfShards, view8)
        runReplica(replica4HostPort, replica4Ip, subnetName, "replica4", numberOfShards, view8)
        runReplica(replica5HostPort, replica5Ip, subnetName, "replica5", numberOfShards, view8)
        runReplica(replica6HostPort, replica6Ip, subnetName, "replica6", numberOfShards, view8)
        runReplica(replica7HostPort, replica7Ip, subnetName, "replica7", numberOfShards, view8)
        runReplica(replica8HostPort, replica8Ip, subnetName, "replica8", numberOfShards, view8)

        print("\n###################### Getting shard id of replica1 ######################\n")
        response = requests.get('http://localhost:8082/key-value-store-shard/node-shard-id')
        responseInJson = response.json()
        replica1ShardId = responseInJson.get('shard-id')
        print("Received replica1's shard id: " + str(replica1ShardId))
        # Check status code
        self.assertEqual(response.status_code, 200)

        print("\n###################### Getting shard id of replica2 ######################\n")
        response = requests.get('http://localhost:8083/key-value-store-shard/node-shard-id')
        responseInJson = response.json()
        replica2ShardId = responseInJson.get('shard-id')
        print("Received replica2's shard id: " + str(replica2ShardId))

        print("\n###################### Getting shard id of replica3 ######################\n")
        response = requests.get('http://localhost:8084/key-value-store-shard/node-shard-id')
        responseInJson = response.json()
        replica3ShardId = responseInJson.get('shard-id')
        print("Received replica3's shard id: " + str(replica2ShardId))

        # Check status code
        self.assertEqual(response.status_code, 200)
        # get the members of replica1's shard-id
        response = requests.get('http://localhost:8082/key-value-store-shard/shard-id-members/' + str(replica1ShardId))
        responseInJson = response.json()
        replica1ShardMembers = responseInJson.get('shard-id-members')
        print("Received members of replica1's shard: " + str(replica1ShardMembers))
        # Check status code
        self.assertEqual(response.status_code, 200)

        # get the members of replica2's shard-id
        response = requests.get('http://localhost:8082/key-value-store-shard/shard-id-members/' + str(replica2ShardId))
        responseInJson = response.json()
        replica2ShardMembers = responseInJson.get('shard-id-members')
        print("Received members of replica1's shard: " + str(replica2ShardMembers))
        # Check status code
        self.assertEqual(response.status_code, 200)

        # actually push a key to one of the nodes
        print("\n###################### Putting key1/value1 to the store ######################\n")
        # put a new key in the store
        response = requests.put('http://localhost:8082/key-value-store/key1', json={'value': "value1", "causal-metadata": ""})
        self.assertEqual(response.status_code, 201)
        # check to see if it ended up in the proper shard
        print("\n###################### Waiting for 10 seconds ######################\n")
        time.sleep(10)
        print("\n###################### Getting key1 from the shard ######################\n")
        # get the value of the new key from replica1 after putting the new key
        response = requests.get('http://localhost:8082/key-value-store/key1')
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(responseInJson['value'], 'value1')
        # check to make sure it didn't end up in the other shards
        # get the value of the new key from replica2 after putting the new key
        # should not be found, because replica1 and replica2 are in different shards
        print("\n###################### Getting key1 from the other shard, should not be found######################\n")
        response = requests.get('http://localhost:8083/key-value-store/key1')
        responseInJson = response.json()
        self.assertEqual(response.status_code, 404)

        print("\n###################### Getting key1 from another shard, should be found######################\n")
        # get the value of the new key from replica3 after putting the new key
        # should not be found, because replica1 and replica3 are in different shards
        response = requests.get('http://localhost:8084/key-value-store/key1')
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)

        # now try getkeycount
        print("\n###################### Getting keycount from replica1's shard ######################\n")
        response = requests.get('http://localhost:8082/key-value-store-shard/shard-id-key-count/' + str(replica1ShardId))
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(responseInJson['shard-id-key-count'], '1')


if __name__ == '__main__':
    unittest.main()