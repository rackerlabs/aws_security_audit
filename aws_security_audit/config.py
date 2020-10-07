import datetime

class Config(object):
    # A list of AWS Config variables to check for
    CHECKED_RESOURCES = [
        'AWS::ElasticLoadBalancingV2::LoadBalancer',
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

    DATE_TIME = datetime.datetime.now().strftime("%d%b%Y %H%M")
    REPORT_NAME_SUFFIX = f" Security Report - {DATE_TIME}.csv"

    EC2_CHECK = False
    RDS_CHECK = False
    ALB_CHECK = True
    S3_CHECK = False

    EC2_CSV_NAME = "ec2" + REPORT_NAME_SUFFIX
    RDS_CSV_NAME = "rds" + REPORT_NAME_SUFFIX
    ELB_CSV_NAME = "elb" + REPORT_NAME_SUFFIX
    S3_CSV_NAME = "s3" + REPORT_NAME_SUFFIX
