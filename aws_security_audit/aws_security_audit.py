#!/usr/bin/env python

import boto3
from botocore.exceptions import ClientError
from pprint import pprint as pp

from config import Config

# Setup clients
ec2 = boto3.client('ec2')
s3 = boto3.client('s3')

# Pull config into main code.
CHECKED_RESOURCES = Config.CHECKED_RESOURCES
INSECURE_SSL_CIPHERS = Config.INSECURE_SSL_CIPHERS

# initialise / declare required vars
EC2_INSTANCES = []
EBS_DEVICES = []
USED_REGIONS = []
S3_BUCKETS = []
LOAD_BALANCERS = []
RDS_INSTANCES = []

def get_all_instances():

    """ Get all ec2 instances in a given region """

    global EC2_INSTANCES

    try:
        token = ""
        while True:
            response = ec2.describe_instances(NextToken=token)
            EC2_INSTANCES += response['Reservations']

            if 'NextToken' in response:
                token = response['NextToken']
            else:
                break
        return True
        
    except ClientError as e:
        
        print (e)

def get_instance_block_device_mappings():

    """ Get ebs devices from the ec2 response """
    
    global EC2_INSTANCES
    global EBS_DEVICES

    for instance in EC2_INSTANCES:
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

    """ get ebs volume attributes """

    try:
        volume = ec2.describe_volumes(
            VolumeIds=[
                vol_id,
            ],
        )

        return(volume['Volumes'][0])
        
    except ClientError as e:
        print (e)

def populate_used_regions():

    """ 
    Use AWS config to get resources in each region and confirm which are in use
    (based on the resources we are looking for)
    """

    global USED_REGIONS
    discovered_regions = set()

    try: 
        all_regions = ec2.describe_regions()
    except ClientError as e:
        print (e)
        return(1)

    for region in all_regions['Regions']:
        try:
            # Use AWS config to list all resources in the region
            config_client = boto3.client('config', region['RegionName'])
            discovered_rescources = config_client.get_discovered_resource_counts()
        
        except ClientError as e:
            print (e)

        for resource in discovered_rescources['resourceCounts']:
            for monitored_resource in CHECKED_RESOURCES:
                # If a discovered resource exists in our list of checked resources then add the region to a list with the associated resources
                if monitored_resource == resource['resourceType'] and region['RegionName'] not in discovered_regions:
                    USED_REGIONS.append({
                        "region": region['RegionName'],
                        "resources": discovered_rescources['resourceCounts']
                    })
                    discovered_regions.add(region['RegionName'])

    return

def perform_security_checks():

    """ Run functions for executing security checks """

    global USED_REGIONS

    # Kick off security checks for each region and resource type
    for region in USED_REGIONS:
        for resource in region['resources']:
            if Config.EC2_CHECK:
                if resource['resourceType'] == 'AWS::EC2::Instance':
                    check_ec2(region['region'])

            if Config.S3_CHECK:
                if resource['resourceType'] == 'AWS::S3::Bucket' and not S3_BUCKETS:
                    check_s3()

            if Config.ALB_CHECK:
                if resource['resourceType'] == 'AWS::ElasticLoadBalancingV2::LoadBalancer':
                    check_alb(region['region'])

            if Config.RDS_CHECK:
                if resource['resourceType'] == 'AWS::RDS::DBInstance':
                    check_rds(region['region'])

    return

def get_all_s3():

    """ Pull every S3 bucket and add to array """

    global S3_BUCKETS

    try:
        response = s3.list_buckets()
        for bucket in response['Buckets']:
            S3_BUCKETS.append({
                "bucket_name": bucket['Name'],
                "encrypted": "false"
            })

        return True
        
    except ClientError as e:
        print (e)

    return

def check_s3_encryption():

    """ Check encryption of each S3 bucket """

    global S3_BUCKETS
    buckets_encrypted = []

    try:
        for bucket in S3_BUCKETS:
            try:
                s3.get_bucket_encryption(Bucket=bucket['bucket_name'])
                buckets_encrypted.append({
                    "bucket_name": bucket['bucket_name'],
                    "encrypted": "true"
                })
            
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    buckets_encrypted.append({
                        "bucket_name": bucket['bucket_name'],
                        "encrypted": "false"
                    })
                else:
                    print (e)

    except ClientError as e:
        print (e)

    S3_BUCKETS = buckets_encrypted

    return

def get_load_balancers(region):

    """ 
    Get all LB's and add to list 

    LOAD_BALANCERS is the object which will end up populated. 
    
    This function creates objects which ultimately get added to that list. 

    Object dict:
    -------------
    LB_TYPE : < elb/alb >,
    LB_NAME : < Name of LB >,
    LISTENERS : [
        LISTENER_NAME : < Name of Listener >,
        REFERENCE_POLICY : < Name of policy >, # Un-needed but good for debug
        CIPHERS : [
            < List of ciphers in use >
        ]
    ]

    lb_object           == the whole object dict
    lb_listener_object  == objects created by loop and appended to lb_listeners list. 
    lb_listener_ciphers == list of ciphers used by the listener. Appended to lb_listener_object['CIPHERS']

    """


    global LOAD_BALANCERS

    elb = boto3.client('elb', region)
    elbv2 = boto3.client('elbv2', region)

    try:
        current_elb = elb.describe_load_balancers()
        current_alb = elbv2.describe_load_balancers()
        
    except ClientError as e:
        print (e)

    if len(current_elb['LoadBalancerDescriptions']) > 0:
        for lb in current_elb['LoadBalancerDescriptions']:
            # initialise the lb_object, append the type and name properties, and initialise the LISTENERS property list
            lb_object = {}
            lb_object['LB_TYPE'] = "elb"
            lb_object['LB_NAME'] = lb['LoadBalancerName']
            lb_object['LISTENERS'] = []

            # get all listeners on the ELB
            for listener in lb['ListenerDescriptions']:
                lb_listener_object = {}

                for listener_policy_name in listener['PolicyNames']:
                    lb_listener_object['POLICY_NAME'] = listener_policy_name

                    policies = elb.describe_load_balancer_policies(
                        LoadBalancerName=lb_object['LB_NAME'],
                        PolicyNames=[
                            listener_policy_name
                        ]
                    )

                    lb_listener_ciphers = []
                    # loop through configured ciphers, make note of reference policy if there is one and record all ciphers in use
                    for cipher in policies['PolicyDescriptions'][0]['PolicyAttributeDescriptions']:
                        if 'AttributeValue' in cipher and cipher['AttributeName'] == "Reference-Security-Policy":
                            lb_listener_object['REFERENCE_POLICY'] = cipher['AttributeValue']

                        if 'AttributeValue' in cipher and cipher['AttributeValue'] == "true":
                            lb_listener_ciphers.append(cipher['AttributeName'])
                    
                    # add ciphers to the listener object and then add the object to the lb_object. 
                    lb_listener_object['CIPHERS'] = lb_listener_ciphers
                    lb_object['LISTENERS'].append(lb_listener_object)

            # once all listener objects have been added to the lb_object, add that to the main LOAD_BALANCERS list
            LOAD_BALANCERS.append(lb_object)

    if len(current_alb['LoadBalancers']) > 0:
        for lb in current_alb['LoadBalancers']:
            # initialise the lb_object, append the type and name properties, and initialise the LISTENERS property list
            lb_object = {}
            lb_object['LB_TYPE'] = "alb"
            lb_object['LB_NAME'] = lb['LoadBalancerName']
            lb_object['LISTENERS'] = []

            listeners = elbv2.describe_listeners(LoadBalancerArn=lb['LoadBalancerArn'])

            for listener in listeners['Listeners']:
                if 'SslPolicy' in listener:
                    lb_listener_object = {}
                    lb_listener_object['POLICY_NAME'] = listener['SslPolicy']
                    policies = elbv2.describe_ssl_policies(
                        Names=[
                            lb_listener_object['POLICY_NAME']
                        ]
                    )
    
                    lb_listener_ciphers = []
                    # loop through configured ciphers, make note of reference policy if there is one and record all ciphers in use
                    for cipher in policies['SslPolicies'][0]['Ciphers']: #[0]['Ciphers']:
                        lb_listener_ciphers.append(cipher['Name'])
    
                    for protocol in policies['SslPolicies'][0]['SslProtocols']:
                        lb_listener_ciphers.append(protocol)
    
                    # add ciphers to the listener object and then add the object to the lb_object. 
                    lb_listener_object['CIPHERS'] = lb_listener_ciphers
                    lb_object['LISTENERS'].append(lb_listener_object)
    
                # once all listener objects have been added to the lb_object, add that to the main LOAD_BALANCERS list
                LOAD_BALANCERS.append(lb_object)      
    return

def get_rds_clusters(region):

    global RDS_INSTANCES
    rds = boto3.client('rds', region)

    try:
        db_instances = rds.describe_db_instances()['DBInstances']        

    except ClientError as e:
        print (e)

    for instance in db_instances:
        RDS_INSTANCES.append({
            "NAME": instance['DBName'],
            "REGION": region,
            "ENCRYPTED": instance['StorageEncrypted']
        })

def check_ec2(region):
    # Overwrite global ec2 object and update region
    global ec2
    ec2 = boto3.client('ec2', region)
    get_all_instances()
    get_instance_block_device_mappings()
    return

def check_s3():
    get_all_s3()
    check_s3_encryption()
    return

def check_alb(region):
    get_load_balancers(region)
    pp(LOAD_BALANCERS)
    return

def check_rds(region):
    get_rds_clusters(region)
    pp(RDS_INSTANCES)
    return

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
    populate_used_regions()
    perform_security_checks()
    # print_details()

if __name__ == "__main__":
    main()