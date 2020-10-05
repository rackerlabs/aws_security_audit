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

    DATE_TIME = datetime.datetime.now().strftime("%d/%b/%Y %H:%M")
    REPORT_NAME_SUFFIX = f" Security Report - {DATE_TIME}"

    EC2_CHECK = False #True
    RDS_CHECK = False #True
    ALB_CHECK = False #True
    S3_CHECK = False #True
