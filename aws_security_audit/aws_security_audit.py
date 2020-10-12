#!/usr/bin/env python

import boto3, sys
from botocore.exceptions import ClientError

try:
    from .config import Config
except ImportError:
    from config import Config

try:
    from .scans import ec2, rds, elb, s3
except ImportError:
    from scans import ec2, rds, elb, s3

# Setup clients
ec2_client = boto3.client('ec2', Config.DEFAULT_AWS_REGION)

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

class report_csv:

    def __init__(self, output_file):
        self.csv_file = output_file
        self.csv_data = []

    def newline(self, linedata):
        self.csv_data.append(linedata)

    def write(self):
        with open(self.csv_file, "w") as output_file:
            for entry in self.csv_data:
                output_file.write(f"{entry}\r\n")

def populate_used_regions():

    """
    Use AWS config to get resources in each region and confirm which are in use
    (based on the resources we are looking for)
    """

    global USED_REGIONS
    discovered_regions = set()

    try: 
        all_regions = ec2_client.describe_regions()
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

def check_ec2(region):
    # Overwrite global ec2 object and update region
    global ec2_client
    global EBS_DEVICES
    EC2_INSTANCES = []

    ec2_client = boto3.client('ec2', region)
    EC2_INSTANCES = ec2.get_all_instances(
        ec2_client, 
        EC2_INSTANCES
    )

    EBS_DEVICES += ec2.get_instance_block_device_mappings(
        ec2_client, 
        EC2_INSTANCES,
        region
    )
    return

def check_s3():
    global S3_BUCKETS

    s3_client = boto3.client('s3')

    S3_BUCKETS = s3.get_all_s3(s3_client)
    S3_BUCKETS = s3.check_s3_encryption(s3_client, S3_BUCKETS)
    S3_BUCKETS = s3.check_s3_public(s3_client, S3_BUCKETS)
    return

def check_alb(region):
    global LOAD_BALANCERS

    elb_client = boto3.client('elb', region)
    elbv2_client = boto3.client('elbv2', region)

    LOAD_BALANCERS = elb.get_load_balancers(region, elb_client, elbv2_client)
    return

def check_rds(region):
    global RDS_INSTANCES

    rds_client = boto3.client('rds', region)

    RDS_INSTANCES = rds.get_rds_clusters(rds_client, region)
    return

def write_ec2_report():
    global EBS_DEVICES
    ec2_report = report_csv(Config.EC2_CSV_NAME)
    ec2_report.newline("Instance Name,Instance ID,Region,EBS Device,Root Device,Volume ID,Encrypted")
    
    for instance in EBS_DEVICES:
        for device in instance['ebs_devices']:
            root_device = "False"
            if {instance['ebs_root']} == {device['DeviceName']}:
                root_device = "True"

            ec2_report.newline(f"{instance['name']},{instance['instance_id']},{instance['region']},{device['DeviceName']},{root_device},{device['VolumeId']},{device['Encrypted']}")

    ec2_report.write()
    return

def write_rds_report():
    rds_report = report_csv(Config.RDS_CSV_NAME)
    rds_report.newline(f"RDS Instance Name,Region,Encrypted")

    for instance in RDS_INSTANCES:
        rds_report.newline(f"{instance['NAME']},{instance['REGION']},{instance['ENCRYPTED']}")
    
    rds_report.write()

def write_elb_report():
    elb_report = report_csv(Config.ELB_CSV_NAME)
    elb_report.newline(f"Load Balancer,Region,Type,Reference Policy,Ciphers,Insecure")

    for lb in LOAD_BALANCERS:
        for listener in lb['LISTENERS']:
            if lb['LB_TYPE'] == "elb":
                reference_policy = listener['REFERENCE_POLICY']
            elif lb['LB_TYPE'] == "alb":
                reference_policy = listener['POLICY_NAME']

            for cipher in listener['CIPHERS']:
                if cipher not in Config.SKIPPED_ALB_CIPHERS:
                    if cipher in Config.INSECURE_SSL_CIPHERS:
                        elb_report.newline(f"{lb['LB_NAME']},{lb['REGION']},{lb['LB_TYPE']},{reference_policy},{cipher},True")
                    else:
                        elb_report.newline(f"{lb['LB_NAME']},{lb['REGION']},{lb['LB_TYPE']},{reference_policy},{cipher}")            
    
    elb_report.write()

def write_s3_report():
    s3_report = report_csv(Config.S3_CSV_NAME)
    s3_report.newline(f"S3 Bucket,Encrypted,Public")

    for bucket in S3_BUCKETS:
        s3_report.newline(f"{bucket['bucket_name']},{bucket['encrypted']},{bucket['is_public']}")
    
    s3_report.write()

def main():
    populate_used_regions()
    perform_security_checks()
    write_ec2_report()
    write_rds_report()
    write_elb_report()
    write_s3_report()

if __name__ == "__main__":
    main()
