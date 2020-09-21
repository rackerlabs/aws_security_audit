#!/usr/bin/python

"""
This python script can be used to update and add alarm notifications 
to existing CW alarms

Developed By - ben.millingtondrake@rackspace.com

"""

import boto3
from botocore.exceptions import ClientError
from pprint import pprint as pp

REGION = "eu-central-1"

ALARM_PREFIX = "CPU"

ALARM_SNS_ARNS = [
    "arn:aws:sns:eu-central-1:985631632611:boj-os_team",
    # "arn:aws:sns:eu-central-1:985631632611:boj-network_team",
    "arn:aws:sns:eu-central-1:985631632611:boj-dba_team"
]

ALARM_SNS = [
    {
    "topic_name": "boj-os_team",
    "endpoint": "os_team@bankofjordan.com.jo"
    },
    {
    "topic_name": "boj-network_team",
    "endpoint": "network_team@bankofjordan.com.jo"
    },
    {
    "topic_name": "boj-dba_team",
    "endpoint": "DBATeam@bankofjordan.com.jo"
    }
]

# CW alarm inputs

# cpu alert

CPU_PERIOD = 300
CPU_THRESHOLD = 95
CPU_EVALUATION_PERIOD = 2
CPU_COMPARISON_OPERATOR = 'GreaterThanOrEqualToThreshold'

# disk alert

DISK_PERIOD = 300
DISK_THRESHOLD = 90
DISK_EVALUATION_PERIOD = 2
DISK_COMPARISON_OPERATOR = 'GreaterThanThreshold'

# memory alert

MEMORY_PERIOD = 300
MEMORY_THRESHOLD = 90
MEMORY_EVALUATION_PERIOD = 2
MEMORY_COMPARISON_OPERATOR = 'GreaterThanOrEqualToThreshold'

# Setup clients
cw = boto3.client('cloudwatch', REGION)
ec2 = boto3.client('ec2', REGION)
sns = boto3.client('sns', REGION)
events = boto3.client('events', REGION)


# initialise / declare required vars

WINDOWS_DISK_METRIC = "LogicalDisk %% Free Space".replace('%', '', 1)

CPU_METRICS = ["CPUUtilization"]
MEMORY_METRICS = ["MemoryUtilization", "Memory % Committed Bytes In Use"]
DISK_METRICS = [WINDOWS_DISK_METRIC, "disk_used_percent"]
INSTANCES = []

def get_minutes(num1,num2):
    """ Get number of minutes for CW -> Period * EvaluationPeriods / 60 """

    minutes = num1 * num2 / 60
    return minutes

def get_existing_alarms(alarm_prefix):

    cw_response = cw.describe_alarms(
                        AlarmNamePrefix=alarm_prefix,
                        AlarmTypes=['MetricAlarm']
                )
    return cw_response["MetricAlarms"]

def update_existing_alarm(alarm_list):
    for alarm in alarm_list:
        cw.put_metric_alarm(
            AlarmName=alarm['AlarmName'],
            AlarmDescription=alarm['AlarmDescription'],
            MetricName=alarm['MetricName'],
            Namespace=alarm['Namespace'],
            Statistic=alarm['Statistic'],
            Period=alarm['Period'],
            Threshold=alarm['Threshold'],
            ComparisonOperator=alarm['ComparisonOperator'],
            Dimensions=[
                {
                    'Name': alarm['Dimensions'][0]['Name'],
                    'Value': alarm['Dimensions'][0]['Value']
                },
            ],
            EvaluationPeriods=alarm['EvaluationPeriods'],
            AlarmActions=ALARM_SNS_ARNS
        )

def get_all_instances():
    
    try:
        response = ec2.describe_instances()

        get_instance_ids(response)

        return True
        
    except ClientError as e:
        
        print (e)

def get_instance_ids(ec2_response):
    """ Get instance ids from the ec2 response and categorize them """
    
    try:
        for reservation in ec2_response["Reservations"]:
            for instance in reservation["Instances"]:
                name_tag = None

                for t in instance["Tags"]:
                    if t['Key'] == "Name":
                        name_tag = t["Value"]

                INSTANCES.append({
                    "name": name_tag if name_tag else "",
                    "instance_id": instance["InstanceId"],
                    "platform": instance["Platform"].lower()
                })

        return True

    except:

        return False

def create_alarms():
    """ Process and add alarms """

    for instance in INSTANCES:
        create_memory_alarm(instance["instance_id"], instance["name"], instance["platform"])
        create_disk_alarm(instance["instance_id"], instance["name"], instance["platform"])

def create_memory_alarm(instance_id, name_tag, platform):
    """ Create rax managed Memory alarm  """

    global MEMORY_ALARM_DIMENSION
    global MEMORY_ALARM_METRIC
    global MEMORY_ALARM_NAMESPACE

    alarm_name = 'rackspace-low-available-memory-alert-' + name_tag
    memory_alarm_time_mins = get_minutes(MEMORY_PERIOD,MEMORY_EVALUATION_PERIOD)

    if platform == "windows":              
        
        WINDOWS_MEMORY_DIMENSION =  [
            {
                "Name": "InstanceId",
                "Value": instance_id
            }
        ]

        MEMORY_ALARM_DIMENSION = WINDOWS_MEMORY_DIMENSION
        MEMORY_ALARM_METRIC = "Memory % Committed Bytes In Use"
        MEMORY_ALARM_NAMESPACE = "CWAgent"

    elif platform == "linux":  

        LINUX_MEMORY_DIMENSION =  [
            {
                "Name": "InstanceId",
                "Value": instance_id
            }
        ]

        MEMORY_ALARM_DIMENSION = LINUX_MEMORY_DIMENSION
        MEMORY_ALARM_METRIC = "MemoryUtilization"
        MEMORY_ALARM_NAMESPACE = "System/Linux"

    else:
        print (f"Instance {instance_id} is of unsupported OS Type")
        return False

    try:

        cw.put_metric_alarm(
            AlarmName=alarm_name,
            ComparisonOperator=MEMORY_COMPARISON_OPERATOR,
            EvaluationPeriods=MEMORY_EVALUATION_PERIOD,
            MetricName=MEMORY_ALARM_METRIC,
            Namespace=MEMORY_ALARM_NAMESPACE,
            Period=MEMORY_PERIOD,
            Statistic='Average',
            Threshold=MEMORY_THRESHOLD,
            ActionsEnabled=True,
            AlarmActions=ALARM_SNS_ARNS,
            AlarmDescription= f'Notify when memory consumption of instance {name_tag} exceeds {MEMORY_THRESHOLD} percent for {memory_alarm_time_mins} mins',
            Dimensions=MEMORY_ALARM_DIMENSION
        )

        print (f"Created alarm {alarm_name}")


    except ClientError as e:

        print(e)
        print(f"Could not create CW Memory alert for instance {instance_id}")

def create_disk_alarm(instance_id, name_tag, platform):
    """ Create rax managed Disk alarm """

    global DISK_ALARM_DIMENSION
    global DISK_ALARM_METRIC
    global DISK_ALARM_NAMESPACE

    alarm_name = 'rackspace-low-disk-space-alert-' + name_tag
    disk_alarm_time_mins = get_minutes(DISK_PERIOD,DISK_EVALUATION_PERIOD)

    if platform == "windows":              
        
        WINDOWS_DISK_DIMENSION =  [
            # {
            #     "Name": "instance",
            #     "Value": "C:"
            # },
            {
                "Name": "InstanceId",
                "Value": instance_id
            }
            # {
            #     "Name": "objectname",
            #     "Value": "LogicalDisk"
            # }
        ]

        DISK_ALARM_DIMENSION = WINDOWS_DISK_DIMENSION
        DISK_ALARM_METRIC = WINDOWS_DISK_METRIC
        DISK_ALARM_NAMESPACE = "CWAgent"

    elif platform == "linux":  

        # metrics_list = cw.list_metrics(
        #     Namespace='System/Linux',
        #     MetricName='disk_used_percent',
        #     Dimensions=[
        #         {
        #             'Name': 'InstanceId',
        #             'Value': instance_id
        #         }
        #     ]
        # )

        # metrics = metrics_list["Metrics"]

        # for metric in metrics:
        #     for dimension in metric["Dimensions"]:
        #         if dimension["Value"] == "xvda1":
        #             target_dimensions = metric["Dimensions"]
        #             for dimension in target_dimensions:
        #                 if dimension["Name"] == "fstype":
        #                     fs_type = dimension["Value"]

        LINUX_DISK_DIMENSION =  [
                # {
                #     "Name": "path",
                #     "Value": "/"
                # },
                {
                    "Name": "InstanceId",
                    "Value": instance_id
                },
                {
                    "Name": "device",
                    "Value": "xvda1"
                }
                # {
                #     "Name": "fstype",
                #     "Value": fs_type
                # }
        ]

        DISK_ALARM_DIMENSION = LINUX_DISK_DIMENSION
        DISK_ALARM_METRIC = "disk_used_percent"
        DISK_ALARM_NAMESPACE = "System/Linux"

    else:
        print (f"Instance {instance_id} is of unsupported OS Type")
        return False

    try:

        cw.put_metric_alarm(
            AlarmName=alarm_name,
            ComparisonOperator=DISK_COMPARISON_OPERATOR,
            EvaluationPeriods=DISK_EVALUATION_PERIOD,
            MetricName=DISK_ALARM_METRIC,
            Namespace=DISK_ALARM_NAMESPACE,
            Period=DISK_PERIOD,
            Statistic='Average',
            Threshold=DISK_THRESHOLD,
            ActionsEnabled=True,
            AlarmActions=ALARM_SNS_ARNS,
            AlarmDescription= f'Notify when Disk usage of instance {instance_id} crosses {DISK_THRESHOLD} percent for {disk_alarm_time_mins} mins',
            Dimensions=DISK_ALARM_DIMENSION
        )

        print (f"Created alarm {alarm_name}")


    except ClientError as e:

        print(e)
        print(f"Could not create CW Disk alert for instance {instance_id}")

def create_sns(sns_dict):            
    for topic in sns_dict:
        try:
            create_topic_response = sns.create_topic(
                Name=topic['topic_name']
            )

            try:
                subscription_response = sns.subscribe(
                    TopicArn=create_topic_response['TopicArn'], 
                    Protocol="email", 
                    Endpoint=topic['endpoint']
                )

            except ClientError as e:

                print(e)
                print(f"Could not create sns subscription for {subscription_response['TopicArn']}")
    
        except ClientError as e:

            print(e)
            print(f"Could not create sns topic for {topic['topic_name']}")
        
        print(f"Created {create_topic_response['TopicArn']}")

def main():
    # current_alarms = get_existing_alarms(ALARM_PREFIX)
    # update_existing_alarm(current_alarms)
    get_all_instances()
    create_alarms()
    # create_sns(ALARM_SNS)


if __name__ == "__main__":
    main()