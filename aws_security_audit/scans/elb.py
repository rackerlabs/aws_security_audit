from botocore.exceptions import ClientError

def get_load_balancers(region, elb_client, elbv2_client):

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


    LOAD_BALANCERS = []

    try:
        current_elb = elb_client.describe_load_balancers()
        current_alb = elbv2_client.describe_load_balancers()
        
    except ClientError as e:
        print (e)

    if len(current_elb['LoadBalancerDescriptions']) > 0:
        for lb in current_elb['LoadBalancerDescriptions']:
            # initialise the lb_object, append the type and name properties, and initialise the LISTENERS property list
            lb_object = {}
            lb_object['LB_TYPE'] = "elb"
            lb_object['LB_NAME'] = lb['LoadBalancerName']
            lb_object['REGION'] = region
            lb_object['LISTENERS'] = []

            # get all listeners on the ELB
            for listener in lb['ListenerDescriptions']:
                lb_listener_object = {}

                for listener_policy_name in listener['PolicyNames']:
                    lb_listener_object['POLICY_NAME'] = listener_policy_name

                    policies = elb_client.describe_load_balancer_policies(
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
            lb_object['REGION'] = region
            lb_object['LISTENERS'] = []

            listeners = elbv2_client.describe_listeners(LoadBalancerArn=lb['LoadBalancerArn'])

            for listener in listeners['Listeners']:
                if 'SslPolicy' in listener:
                    lb_listener_object = {}
                    lb_listener_object['POLICY_NAME'] = listener['SslPolicy']
                    policies = elbv2_client.describe_ssl_policies(
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

    return LOAD_BALANCERS