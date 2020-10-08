
from botocore.exceptions import ClientError

def get_all_instances(client, EC2_INSTANCES):

    """ Get all ec2 instances in a given region """

    try:
        token = ""
        while True:
            response = client.describe_instances(NextToken=token)
            EC2_INSTANCES += response['Reservations']

            if 'NextToken' in response:
                token = response['NextToken']
            else:
                break
            
        return EC2_INSTANCES
        
    except ClientError as e:
        print (e)

        
def get_instance_block_device_mappings(client, EC2_INSTANCES, region):

    """ Get ebs devices from the ec2 response """

    EBS_DEVICES = []

    for instance in EC2_INSTANCES:
        devices = []
        name_tag = "NO_NAME_TAG"

        for dev in instance['Instances'][0]['BlockDeviceMappings']:
            ebs_vol_id = dev['Ebs']['VolumeId']
            vol_arrtib = get_ebs_volume_attrib(client, ebs_vol_id)

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
            "region": region,
            "ebs_root": instance['Instances'][0]['RootDeviceName'],
            "ebs_optimised": instance['Instances'][0]['EbsOptimized'],
            "ebs_devices": devices
        })
        
    return EBS_DEVICES


def get_ebs_volume_attrib(client, vol_id):

    """ get ebs volume attributes """

    try:
        volume = client.describe_volumes(
            VolumeIds=[
                vol_id,
            ],
        )

        return(volume['Volumes'][0])
        
    except ClientError as e:
        print (e)