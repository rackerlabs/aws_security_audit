#!/usr/bin/python

"""
This script can be used to check the encrpytion status of EC2 EBS volumes

Executing the script will check all EC2 instances on whichever account you are currently authenticated. 

Developed By - ben.millingtondrake@rackspace.com
"""

import boto3
import csv, sys
from botocore.exceptions import ClientError
from pprint import pprint as pp

REGION = "eu-central-1"

CSV_FILE = "boj.csv"

# Setup clients
ec2 = boto3.client('ec2', REGION)

# initialise / declare required vars
INSTANCES = []
JSON_CSV = []
CH_TAG_NAME = "CH_FRIENDLY_NAME"
OVERWRITE_TAGS = False

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

def parse_and_filter_csv():

    try:
        account_id = boto3.client('sts').get_caller_identity().get('Account')
        
    except ClientError as e:
        print (e)

    try: 
        with open(CSV_FILE, encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            for row in csv_reader:
                if row["account id"] == account_id:
                    JSON_CSV.append({
                        "account_id": row["account id"],
                        "instance_name": row["instance name"],
                        "instance_id": row["instance id"],
                        "friendly_name": row["friendly name"]
                    })

    except Exception as e:
        print(e)

    if len(JSON_CSV) == 0:
        print(f"Currently authenticated to AWS account \"{account_id}\" but no instances found with that in CSV.")
        print("Exiting.")
        sys.exit(0)

def update_tags():

    def add_tag(aws_instance_id_internal):
        for row in JSON_CSV:
            if row['instance_id'] == aws_instance_id_internal:
                try: 
                    ec2.create_tags(
                        Resources=[aws_instance_id_internal],
                        Tags = [
                            {
                                'Key': CH_TAG_NAME,
                                'Value': row['friendly_name']
                            }
                        ]
                    )
                    return
        
                except ClientError as e:
                    print (e)
        
    global INSTANCES

    for instance in INSTANCES:
        TAG_MATCH = False
        aws_instance_id = instance['Instances'][0]['InstanceId']
        for tags in instance['Instances'][0]['Tags']:
            if tags['Key'] == CH_TAG_NAME:
                PREVIOUS_TAG_VALUE = tags['Value']
                TAG_MATCH = True
                break
        if not TAG_MATCH or OVERWRITE_TAGS:
            if OVERWRITE_TAGS:
                print(f"Overwriting tag {CH_TAG_NAME} on {aws_instance_id}")
                print(f"Previous Value: {PREVIOUS_TAG_VALUE}")
            add_tag(aws_instance_id)
        else:
            print(f"Tag {CH_TAG_NAME} already exists on instance {aws_instance_id} with a value of \"{PREVIOUS_TAG_VALUE}\"")
            print("Skipping")


def main():
    parse_and_filter_csv()
    get_all_instances()
    update_tags()

if __name__ == "__main__":
    main()