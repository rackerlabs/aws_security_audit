from botocore.exceptions import ClientError

def get_rds_clusters(client, region):

    RDS_INSTANCES = []

    try:
        db_instances = client.describe_db_instances()['DBInstances']        

    except ClientError as e:
        print (e)

    for instance in db_instances:
        RDS_INSTANCES.append({
            "NAME": instance['DBName'],
            "REGION": region,
            "ENCRYPTED": instance['StorageEncrypted']
        })

    return RDS_INSTANCES