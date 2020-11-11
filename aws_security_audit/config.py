import datetime
import os

class Config(object):
    # A list of AWS Config variables to check for
    CHECKED_RESOURCES = [
        'AWS::ElasticLoadBalancingV2::LoadBalancer',
        'AWS::ElasticLoadBalancing::LoadBalancer',
        'AWS::S3::Bucket',
        'AWS::EC2::Instance',
        'AWS::RDS::DBInstance'
    ]

    # Stick to AWS naming for the below, to prevent false positives
    INSECURE_SSL_CIPHERS = [
        "Protocol-TLSv1",
        "Protocol-TLSv1.1",
        "TLSv1",
        "TLSv1.1"
    ]

    # Skip these ase they are AWS naming placeholders
    SKIPPED_ALB_CIPHERS = [
        "Server-Defined-Cipher-Order"
    ]

    # Name the report with date/time for sanity and prevent accidental over writing. 
    DATE_TIME = datetime.datetime.now().strftime("%d%b%Y %H%M")
    REPORT_NAME_SUFFIX = f" Security Report - {DATE_TIME}.csv"

    EC2_CSV_NAME = "ec2" + REPORT_NAME_SUFFIX
    RDS_CSV_NAME = "rds" + REPORT_NAME_SUFFIX
    ELB_CSV_NAME = "elb" + REPORT_NAME_SUFFIX
    S3_CSV_NAME = "s3" + REPORT_NAME_SUFFIX

    # Set default region. This is needed to lookup all available regions.
    DEFAULT_AWS_REGION = "eu-west-1"


    # Ability to disable individual checks. More for DEBUG purposes.
    EC2_CHECK = True
    RDS_CHECK = True
    ALB_CHECK = True
    S3_CHECK = True

    # Add ability to pass additional boto config if needed
    AWS_ACCESS_ID = os.environ['AWS_ACCESS_KEY_ID'] if 'AWS_ACCESS_KEY_ID' in os.environ else None
    AWS_SECRET_KEY = os.environ['AWS_SECRET_ACCESS_KEY'] if 'AWS_SECRET_ACCESS_KEY' in os.environ else None
    AWS_SESSION_TOKEN = os.environ['AWS_SESSION_TOKEN'] if 'AWS_SESSION_TOKEN' in os.environ else None

    BOTO_CONFIG = None
