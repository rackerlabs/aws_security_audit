from botocore.exceptions import ClientError

def get_all_s3(client):

    """ Pull every S3 bucket and add to array """

    S3_BUCKETS = []

    try:
        response = client.list_buckets()
        for bucket in response['Buckets']:
            S3_BUCKETS.append({
                "bucket_name": bucket['Name'],
                "encrypted": "false"
            })

        return S3_BUCKETS
        
    except ClientError as e:
        print (e)

def check_s3_encryption(client, S3_BUCKETS):

    """ Check encryption of each S3 bucket """

    bucket_status = []

    try:
        for bucket in S3_BUCKETS:
            try:
                client.get_bucket_encryption(Bucket=bucket['bucket_name'])
                bucket_status.append({
                    "bucket_name": bucket['bucket_name'],
                    "encrypted": "true"
                })
            
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    bucket_status.append({
                        "bucket_name": bucket['bucket_name'],
                        "encrypted": "false"
                    })
                else:
                    print (e)

    except ClientError as e:
        print (e)

    return bucket_status

def check_s3_public(client, S3_BUCKETS):

    """ Check whether S3 bucket is public """

    bucket_public = []

    def append_policy(is_public):
        bucket_public.append({
            "bucket_name": bucket['bucket_name'],
            "encrypted": bucket['encrypted'],
            "is_public": is_public
        })

    try:
        for bucket in S3_BUCKETS:
            try:
                response = client.get_bucket_policy_status(Bucket=bucket['bucket_name'])
                append_policy(response['PolicyStatus']['IsPublic'])
            
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                    append_policy("False")
                else:
                    print (e)

    except ClientError as e:
        print (e)

    return bucket_public