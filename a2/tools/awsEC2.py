import boto3
from botocore.exceptions import ClientError

try:
    from tools.credential import ConfigAWS
except:
    from credential import ConfigAWS

# Create a credential.py in tools/ with the code as following format:

# class ConfigAWS():
#     aws_access_key_id = "You wish"
#     aws_secret_access_key = "Fuck you"


# Credits: https://www.youtube.com/watch?v=ZYAOGVdlDqU
class MemcacheEC2(object):
    def __init__(self, ec2_client):
        self.ec2_client = ec2_client
        self.maxMemcacheNumber = 8
        self.memcacheDict = {}

        self.amiID = "ami-080ff70d8f5b80ba5"  # Change this to our own AMI ID!

    def grep_vpc_subnet_id(self):
        response = self.ec2_client.describe_vpcs()
        vpc_id = ""
        print(response)
        for vpc in response["Vpcs"]:
            if vpc["InstanceTenancy"].__contains__("default"):
                vpc_id = vpc["VpcId"]
                break
        print("The Default VPC : ", vpc_id)
        response = self.ec2_client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        subnet_id = response["Subnets"][0]["SubnetId"]
        print("The Default Subnet : ", subnet_id)
        return vpc_id, subnet_id

    def create_security_group(self):
        sg_name = "memcache_security_group"
        try:
            vpc_id, subnet_id = self.grep_vpc_subnet_id()
            response = self.ec2_client.create_security_group(
                GroupName=sg_name,
                Description="Memcache Security Group. This is created using python",
                VpcId=vpc_id
            )
            sg_id = response["GroupId"]
            print(sg_id)
            sg_config = self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }, {
                        'IpProtocol': 'tcp',
                        'FromPort': 5001,
                        'ToPort': 5001,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }, {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            print(sg_config)
            return sg_id, sg_name
        except Exception as e:
            if str(e).__contains__("already exists"):
                response = self.ec2_client.describe_security_groups(GroupNames=[
                                                                    sg_name])
                sg_id = response["SecurityGroups"][0]["GroupId"]
                print(sg_id, sg_name)
                return sg_id, sg_name

    def create_ec2_instance(self):
        """

            MaxCount=1, # Keep the max count to 1, unless you have a requirement to increase it
            InstanceType="t2.micro", # Change it as per your need, But use the Free tier one
            KeyName="ECE1779_A2_public"
            :return: Creates the EC2 instance.
        """

        # Check if there are already 8 instances:

        if (len(self.memcacheDict) >= self.maxMemcacheNumber):
            print("Cannot create new instance. dict already has 8. ")
            print("Trying to refresh... ")
            self.statelessRefresh()
            if (len(self.memcacheDict) >= self.maxMemcacheNumber):
                print("Dict still full. Abandoning...")
                return
            print("Dict refreshed. Proceeding...")

        try:
            print("Creating EC2 instance...")

            # Check what is the latest num

            number = 0
            memcacheName = ("ECE1779_A2_Memcache_" +
                            str(0))
            for i in range(self.maxMemcacheNumber):
                if str(i) in self.memcacheDict.keys():
                    continue
                break
            number = i
            memcacheName = ("ECE1779_A2_Memcache_" +
                            str(i))

            sg_id, sg_name = self.create_security_group()
            vpc_id, subnet_id = self.grep_vpc_subnet_id()
            conn = self.ec2_client.run_instances(

                ImageId=self.amiID,
                MinCount=1,
                MaxCount=1,
                InstanceType="t2.micro",
                KeyName="ECE1779_A2_public",
                SecurityGroupIds=[sg_id],
                SubnetId=subnet_id,
                TagSpecifications=[{'ResourceType': 'instance',
                                    'Tags': [
                                        {
                                            'Key': 'Name',
                                            'Value': memcacheName
                                        },
                                    ]
                                    }]

            )
            print(conn)

            self.memcacheDict[str(number)] = {"Name": memcacheName,
                                              "Status": "ON",
                                              "instanceID": conn['Instances'][0]['InstanceId'],
                                              "amiID": self.amiID,
                                              "Number": number,
                                              "PublicIP": ""}

        except Exception as e:
            print("Error, ", e)

    def describe_ec2_instance(self):
        """
            Get a super long description of all the EC2 instances in this AWS account
        """
        try:
            print("Describing EC2 instance")

            print(self.ec2_client.describe_instances())
            return self.ec2_client.describe_instances()
        except Exception as e:
            print("Error, ", e)

    def reboot_ec2_instance(self, number):
        """
            Reboot memcache number #. Don't think this would be used.
            Note that you should wait for some time for the memcache EC2 to reboot before it shows up.
        """
        try:
            print("Rebooting EC2 instance", number, "...")

            # If memcacheDict has stuff
            if self.memcacheDict:
                if not str(number) in self.memcacheDict:
                    print("Error. Memcache number", number, "does not exist.")
                    return
                instanceID = self.memcacheDict[str(number)]["instanceID"]

                if self.memcacheDict[str(number)]["Status"] == "ON":

                    conn = self.ec2_client.reboot_instances(
                        InstanceIds=[instanceID])

                    self.memcacheDict[str(number)]["Status"] = "ON"
                    print("Signal to reboot Memcache number", number, "sent.")
                elif self.memcacheDict[str(number)]["Status"] == "OFF":
                    print("Cannot Reboot. Memcache number",
                          number, "is stopped.")

        except Exception as e:
            print("Error, ", e)

    def start_ec2_instance(self, number):
        """
            Start memcache number #.
            Note that you should wait for some time for the memcache EC2 to boot before it shows up.
        """
        try:
            print("Starting EC2 instance", number, "...")

            # If memcacheDict has stuff
            if self.memcacheDict:
                if not str(number) in self.memcacheDict:
                    print("Error. Memcache number", number, "does not exist.")
                    return
                instanceID = self.memcacheDict[str(number)]["instanceID"]

                if self.memcacheDict[str(number)]["Status"] == "OFF":

                    conn = self.ec2_client.start_instances(
                        InstanceIds=[instanceID])

                    self.memcacheDict[str(number)]["Status"] = "ON"
                    print("Signal to start Memcache number", number, "sent.")
                elif self.memcacheDict[str(number)]["Status"] == "ON":
                    print("Memcache number", number, "is already running.")

        except Exception as e:
            print("Error, ", e)

    def _stop_ec2_instance(self, number):
        """
            Stop memcache number #.
            Note that you should wait for some time for the memcache EC2 to shutdown before it shows up.
            An internal function because theoretically should not be useful to shut a specific number.
        """
        try:
            print("Stopping EC2 instance", number, "...")
            # If memcacheDict has stuff
            if self.memcacheDict:
                if not str(number) in self.memcacheDict:
                    print("Error. Memcache number", number, "does not exist.")
                    return
                instanceID = self.memcacheDict[str(number)]["instanceID"]
                if self.memcacheDict[str(number)]["Status"] == "ON":
                    conn = self.ec2_client.stop_instances(
                        InstanceIds=[instanceID])

                    self.memcacheDict[str(number)]["Status"] = "OFF"
                    print("Signal to stop Memcache number", number, "sent.")
                elif self.memcacheDict[str(number)]["Status"] == "OFF":
                    print("Memcache number", number, "is already stopped.")

        except Exception as e:
            print("Error, ", e)

    def stop_ec2_instance(self):
        """
            Stop memcache with the LARGEST number.
            Note that you should wait for some time for the memcache EC2 to shutdown before it shows up.
        """
        if self.memcacheDict:

            # Check what is the last num
            number = 0
            for i in range(self.maxMemcacheNumber-1, -1, -1):
                if str(i) not in self.memcacheDict.keys():
                    continue
                break
            number = i

            return self._stop_ec2_instance(number)
        return "ERROR! self.memcacheDict is empty."

    def _terminate_ec2_instance(self, number):
        """
            Terminate memcache number #.
            Note that you should wait for some time for the memcache EC2 to terminate before it shows up.
            Ideally only call this on shutdown?
        """
        try:
            print("Terminating EC2 instance", number, "...")
            if self.memcacheDict:
                if not str(number) in self.memcacheDict:
                    print("Error. Memcache number", number, "does not exist.")
                    return
                instanceID = self.memcacheDict[str(number)]["instanceID"]

                conn = self.ec2_client.terminate_instances(
                    InstanceIds=[instanceID])

                self.memcacheDict.pop(str(number))
                print("Signal to terminate Memcache number", number, "sent.")
        except Exception as e:
            print("Error, ", e)

    def terminate_ec2_instance(self):
        """
            Terminate memcache with the LARGEST number.
            Note that you should wait for some time for the memcache EC2 to terminate before it shows up.
            Ideally only call this on shutdown?
        """
        if self.memcacheDict:
            # Check what is the last num
            number = 0

            for i in range(self.maxMemcacheNumber-1, -1, -1):
                if str(i) not in self.memcacheDict.keys():
                    continue
                break
            number = number

            return self._terminate_ec2_instance(i)
        return "ERROR! self.memcacheDict is empty."

    def get_live_ec2_instance_id(self):
        """
            Get a list of instance ids that are memcaches.
        """
        try:
            print("Instance IDs are: ")

            response = self.ec2_client.describe_instances()
            #  print(response)
            instanceIDs = []
            for i in response["Reservations"]:
                if self.amiID == i["Instances"][0]["ImageId"] and "Tags" in i["Instances"][0] and ("ECE1779_A2_Memcache") in i["Instances"][0]["Tags"][0]["Value"] and i["Instances"][0]["State"]["Name"] != 'terminated':
                    instanceIDs.append(i["Instances"][0]["InstanceId"])
            print(instanceIDs)
            return instanceIDs
        except Exception as e:
            print("Error, ", e)

    def get_live_ec2_running_instance_id(self):
        """
            Get a list of running instance ids that are memcaches.
        """
        try:
            print("Running Instance IDs are: ")

            response = self.ec2_client.describe_instances()

            runningInstanceIDs = []
            states = ['running', 'pending']
            for i in response["Reservations"]:
                if self.amiID == i["Instances"][0]["ImageId"] and i["Instances"][0]["State"]["Name"] in states and "Tags" in i["Instances"][0] and i["Instances"][0]["Tags"][0]["Value"].__contains__("ECE1779_A2_Memcache") and i["Instances"][0]["State"]["Name"] != 'terminated':
                    runningInstanceIDs.append(i["Instances"][0]["InstanceId"])
            print(runningInstanceIDs)
            return runningInstanceIDs
        except Exception as e:
            print("Error, ", e)

    def howMany(self):
        """
            Get how many memcache EC2 instances are present
        """
        return len(self.memcacheDict)

    def howManyAreRunning(self):
        """
            Get how many memcache EC2 instances are running
        """
        if self.memcacheDict:
            runningNum = 0
            for i in self.memcacheDict.values():
                if i["Status"] == "ON":
                    runningNum = runningNum+1
            return runningNum
        else:
            return 0

    def whoAreRunning(self):
        """ 
            Get the numbers of memcache EC2 instances that are running
        """
        if self.memcacheDict:
            runningList = []
            for i in self.memcacheDict.values():
                if i["Status"] == "ON":
                    runningList.append(i["Number"])
            return runningList
        else:
            return []

    def tellMeAbout(self, number, verbose=False):
        """
            Returns all relevent information (in dict) about memcache number #, also prints if verbose.
        """
        if self.memcacheDict:
            if not str(number) in self.memcacheDict:
                print("Error. Memcache number", number, "does not exist.")
                return {}
        if verbose:
            print("Memcache Number ", self.memcacheDict[str(number)]["Number"])
            print("Name:", self.memcacheDict[str(number)]["Name"])
            print("Status:", self.memcacheDict[str(number)]["Status"])
            print("instanceID:", self.memcacheDict[str(number)]["instanceID"])
            print("amiID:", self.memcacheDict[str(number)]["amiID"])
            print("PublicIP:", self.memcacheDict[str(number)]["PublicIP"])

        return self.memcacheDict[str(number)]

    def getIP(self, number, verbose=False):
        """
            Returns public IP of memcache number #, also prints if verbose.
        """
        if self.memcacheDict:
            if not str(number) in self.memcacheDict:
                print("Error. Memcache number", number, "does not exist.")
                return {}
        if verbose:
            print("PublicIP:", self.memcacheDict[str(number)]["PublicIP"])

        return self.memcacheDict[str(number)]["PublicIP"]

    def refreshPublicIP(self):
        """
            VERY IMPORTANT: 

            Because public IPs are assigned after an instance is created,
            Need to repeatedly call this function after an instance is created
            to update its public IP.
        """
        try:
            response = self.ec2_client.describe_instances()
            states = ['running', 'pending']
            # print(response)
            for i in response["Reservations"]:
                if self.amiID == i["Instances"][0]["ImageId"] and "Tags" in i["Instances"][0] and i["Instances"][0]["Tags"][0]["Value"].__contains__("ECE1779_A2_Memcache") and i["Instances"][0]["State"]["Name"] != 'terminated':
                    memcacheName = i["Instances"][0]["Tags"][0]["Value"]
                    memcacheNum = int(memcacheName[-1])
                    if i["Instances"][0]["State"]["Name"] in states:
                        if i["Instances"][0]["PublicIpAddress"]:
                            if str(memcacheNum) in self.memcacheDict:
                                self.memcacheDict[str(
                                    memcacheNum)]["PublicIP"] = i["Instances"][0]["PublicIpAddress"]
        except Exception as e:
            print("Error, ", e)

    def isON(self, number):
        """
            Check if memcache EC2 number # is ON.
        """
        if self.memcacheDict:
            if not str(number) in self.memcacheDict:
                print("Error. Memcache number", number, "does not exist.")
                return {}
        return self.memcacheDict[str(number)]["Status"] == "ON"

    def statelessRefresh(self):
        """
            Refresh the dict with current data from AWS.
        """
        try:
            response = self.ec2_client.describe_instances()
            self.memcacheDict.clear()
            instanceIDs = []
            runningInstanceIDs = []

            states = ['running', 'pending']
            # print(response)
            for i in response["Reservations"]:
                if self.amiID == i["Instances"][0]["ImageId"] and "Tags" in i["Instances"][0] and i["Instances"][0]["Tags"][0]["Value"].__contains__("ECE1779_A2_Memcache") and i["Instances"][0]["State"]["Name"] != 'terminated':
                    instanceIDs.append(i["Instances"][0]["InstanceId"])
                    memcacheName = i["Instances"][0]["Tags"][0]["Value"]
                    memcacheNum = int(memcacheName[-1])
                    if i["Instances"][0]["State"]["Name"] in states:
                        runningInstanceIDs.append(
                            i["Instances"][0]["InstanceId"])
                        self.memcacheDict[str(memcacheNum)] = {"Name": memcacheName,
                                                               "Status": "ON",
                                                               "instanceID": i['Instances'][0]['InstanceId'],
                                                               "amiID": self.amiID,
                                                               "Number": memcacheNum,
                                                               "PublicIP": ""}
                        if i["Instances"][0]["PublicIpAddress"]:
                            self.memcacheDict[str(
                                memcacheNum)]["PublicIP"] = i["Instances"][0]["PublicIpAddress"]
                    else:
                        self.memcacheDict[str(memcacheNum)] = {"Name": memcacheName,
                                                               "Status": "OFF",
                                                               "instanceID": i['Instances'][0]['InstanceId'],
                                                               "amiID": self.amiID,
                                                               "Number": memcacheNum,
                                                               "PublicIP": ""}

            print(self.memcacheDict)
        except Exception as e:
            print("Error, ", e)


# Calling Area ######################################################################
try:
    ec2_client = boto3.client('ec2',
                              "us-east-1",
                              aws_access_key_id=ConfigAWS.aws_access_key_id,
                              aws_secret_access_key=ConfigAWS.aws_secret_access_key)
    call_obj = MemcacheEC2(ec2_client)

    call_obj.get_live_ec2_instance_id()
    call_obj.statelessRefresh()

    input("Press Enter to continue...")

    call_obj.create_ec2_instance()
    input("Press Enter to continue...")
    call_obj.get_live_ec2_instance_id()
    call_obj.get_live_ec2_running_instance_id()

    input("Press Enter to continue...")

    call_obj.refreshPublicIP()

    for i in range(8):
        call_obj.tellMeAbout(i, verbose=True)

    print(call_obj.whoAreRunning())

    input("Press Enter to continue...")
    call_obj.stop_ec2_instance()
    input("Press Enter to continue...")
    call_obj.get_live_ec2_instance_id()
    call_obj.get_live_ec2_running_instance_id()

    input("Press Enter to continue...")

    call_obj.statelessRefresh()
    input("Press Enter to continue...")

    call_obj.terminate_ec2_instance()
    input("Press Enter to continue...")
    call_obj.get_live_ec2_instance_id()
    call_obj.get_live_ec2_running_instance_id()

except ClientError as e:
    print("There is a error in the client configuration: ", e)

# Calling Area ######################################################################
