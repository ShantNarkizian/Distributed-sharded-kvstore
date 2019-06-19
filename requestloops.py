# manually testing the PUT and GET request loops to see what the 500 error is

import requests
import time
import os

nodeIpList = ["10.10.0.2", "10.10.0.3", "10.10.0.4", "10.10.0.5", "10.10.0.6", "10.10.0.7"]
nodeHostPortList = ["8082","8083", "8084", "8085", "8086", "8087"]
nodeSocketAddressList = [ replicaIp + ":8080" for replicaIp in nodeIpList ]

for counter in range(600):
    nodeIndex = counter % len(nodeIpList)

    print ("node_index: ", nodeIndex, " counter: ", counter)

    # put a new key in the store
    response = requests.put('http://localhost:' + nodeHostPortList[nodeIndex] + '/key-value-store/key' + str(counter), json={'value': "value" + str(counter), "causal-metadata": ''})
    responseInJson = response.json()
    #self.assertEqual(response.status_code, 201)
    if(response.status_code != 201):
        print("NOT 201")

    nextCausalMetadata = responseInJson["causal-metadata"]

    keyShardId = responseInJson["shard-id"]

    #self.assertTrue(keyShardId in self.shardIdList)
    shardIdList = ['0', '1']
    if(keyShardId not in shardIdList):
        print("keyShardId not found!!!")

    time.sleep(0.1)

time.sleep(10)

print("\n###################### Getting keys/values from the store ######################\n")


for counter in range(600):

    nodeIndex = (counter + 1 ) % len(nodeIpList)
    print ("Getting counter: ", counter, " from node_index: ", nodeIndex)

    # get the value of the key
    response = requests.get('http://localhost:' + nodeHostPortList[nodeIndex] + '/key-value-store/key' + str(counter))

    print(response)

    responseInJson = response.json()
    #self.assertEqual(response.status_code, 200)
    if(response.status_code != 200):
        print("NOT 200")
    value = responseInJson["value"]
    #self.assertEqual(value, "value" + str(counter))
    if(value != ("value" + str(counter))):
        print("Wrong value!")