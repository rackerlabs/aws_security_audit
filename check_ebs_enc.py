#!/usr/bin/python

"""
This script can be used to check the encrpytion status of EC2 EBS volumes

Executing the script will check all EC2 instances on whichever account you are currently authenticated. 

Developed By - ben.millingtondrake@rackspace.com
"""

import boto3
from botocore.exceptions import ClientError
from pprint import pprint as pp

REGION = "eu-central-1"

# Setup clients
ec2 = boto3.client('ec2', REGION)
ebs = boto3.client('ebs', REGION)

# initialise / declare required vars
INSTANCES = []
EBS_DEVICES = []

def get_all_instances():

    global INSTANCES
    try:
        token = ""
        while True:
            response = ec2.describe_instances(NextToken=token)
            INSTANCES += response['Reservations']

            if 'NextToken' in response:
                token = response['NextToken']
            else:
                break
        return True
        
    except ClientError as e:
        
        print (e)

def get_instance_block_device_mappings():

    """ Get ebs devices from the ec2 response """
    
    global INSTANCES
    global EBS_DEVICES

    for instance in INSTANCES:
        devices = []
        name_tag = "NO_NAME_TAG"


        for dev in instance['Instances'][0]['BlockDeviceMappings']:
            ebs_vol_id = dev['Ebs']['VolumeId']
            vol_arrtib = get_ebs_volume_attrib(ebs_vol_id)

            devices.append({
                "DeviceName": dev['DeviceName'],
                "VolumeId": ebs_vol_id,
                "Encrypted": vol_arrtib['Encrypted']
            })

        for t in instance['Instances'][0]['Tags']:
            if t['Key'] == "Name":
                name_tag = t["Value"]

        EBS_DEVICES.append({
            "name": name_tag if name_tag else "",
            "instance_id": instance['Instances'][0]["InstanceId"],
            "ebs_root": instance['Instances'][0]['RootDeviceName'],
            "ebs_optimised": instance['Instances'][0]['EbsOptimized'],
            "ebs_devices": devices
        })
        
    return True

def get_ebs_volume_attrib(vol_id):

    try:
        volume = ec2.describe_volumes(
            VolumeIds=[
                vol_id,
            ],
        )

        return(volume['Volumes'][0])
        
    except ClientError as e:
        
        print (e)

def print_details():
    global EBS_DEVICES

    for instance in EBS_DEVICES:
        print(f'{instance["name"]}')
        print(f'\tInstance ID:\t{instance["instance_id"]}')
        print(f'\tEBS Root:\t{instance["ebs_root"]}')
        print(f'\tEBS Optimised:\t{instance["ebs_optimised"]}')
        print(f'\tEBS Devices:')
        print(f'\t\tDevice\t\tVolume ID\t\tEncrypted')
        for ebs in instance['ebs_devices']:
            print(f'\t\t{ebs["DeviceName"]}\t{ebs["VolumeId"]}\t{ebs["Encrypted"]}')

        print('\n')
        

def main():
    get_all_instances()
    get_instance_block_device_mappings()
    print_details()

if __name__ == "__main__":
    main()