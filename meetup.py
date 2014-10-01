import argparse
import botocore.session
import pprint
import time

global p3
p3 = pprint.PrettyPrinter(indent=4)


class ApiException(Exception):
    pass


class AWSCredential:

    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key


def poll_api(api_call):
    def api_poller(*args, **kwargs):
        retval = ''
        while True:
            try:
                retval = api_call(*args, **kwargs)
                break
            except ApiException as e:
                print(str(e))
                print('.')
                time.sleep(5)
        return retval
    return api_poller


def main():

    REGION = 'us-west-2'

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", help="Access Key")
    parser.add_argument("-s", help="Secret Key")
    args = parser.parse_args()

    p3.pprint("Access Key is %s" % args.a)
    p3.pprint("Secret Key is %s" % args.s)

    creds = AWSCredential(args.a, args.s)

    try:
        print('Setting up')
        vpc_id = build_vpc(creds, REGION, cidr="10.13.0.0/16")
        subnet_1 = build_subnet(creds, REGION, vpc_id=vpc_id,
                                cidr="10.13.1.0/24", az='a')
        subnet_2 = build_subnet(creds, REGION, vpc_id=vpc_id,
                                cidr="10.13.2.0/24", az='b')
        elb_sg_id = build_security_group(creds, REGION,
                                         sg_name='meetup-elb-sg',
                                         vpc_id=vpc_id)

        build_elb(creds, REGION, lb_name="meetup-elb",
                  subnets=[subnet_1, subnet_2], elb_sg_id=elb_sg_id)

        import pdb; pdb.set_trace()

    except KeyboardInterrupt:
        print('Keyboard interrupt!')
    except Exception as e:
        print(e)

    finally:
        print("Tearing down...")
        destroy_elb(creds, REGION, lb_name="meeterp-elb")
        destroy_security_group(creds, REGION, sg_id=elb_sg_id)
        destroy_subnet(creds, REGION, subnet_id=subnet_1)
        destroy_subnet(creds, REGION, subnet_id=subnet_2)
        destroy_vpc(creds, REGION, vpc_id=vpc_id)


@poll_api
def build_vpc(aws_creds, region, cidr=""):
    print('Building VPC for %s network' % str(cidr))
    session = botocore.session.get_session()
    session.set_credentials(aws_creds.access_key, aws_creds.secret_key)
    ec2 = session.get_service('ec2')
    operation = ec2.get_operation('CreateVpc')
    endpoint = ec2.get_endpoint(region)
    http_response, response_data = operation.call(endpoint,
                                                  CidrBlock=cidr)
    p3.pprint(str(http_response.status_code) + " - " + http_response.reason)
    p3.pprint(response_data)

    if http_response.status_code != 200:
        raise(ApiException)

    vpc_id = response_data['Vpc']['VpcId']

    operation = ec2.get_operation('CreateTags')
    http_response, response_data = operation.call(endpoint,
                                                  Resources=[vpc_id],
                                                  Tags=[{"Key": "Name",
                                                         "Value": 'Meetup'
                                                         }],
                                                  )

    return vpc_id


@poll_api
def destroy_vpc(aws_creds, region, vpc_id=""):
    print('Destroying VPC %s' % str(vpc_id))
    session = botocore.session.get_session()
    session.set_credentials(aws_creds.access_key, aws_creds.secret_key)
    ec2 = session.get_service('ec2')
    operation = ec2.get_operation('DeleteVpc')
    endpoint = ec2.get_endpoint(region)
    http_response, response_data = operation.call(endpoint,
                                                  VpcId=vpc_id)

    p3.pprint(str(http_response.status_code) + " - " + http_response.reason)
    p3.pprint(response_data)

    if http_response.status_code != 200:
        raise(ApiException)

    return True


@poll_api
def build_subnet(aws_creds, region, vpc_id="", cidr="", az=""):
    print('Building subnet %s in AZ %s' % (str(cidr), str(az)))
    session = botocore.session.get_session()
    session.set_credentials(aws_creds.access_key, aws_creds.secret_key)
    ec2 = session.get_service('ec2')
    operation = ec2.get_operation('CreateSubnet')
    endpoint = ec2.get_endpoint(region)
    http_response, response_data = operation.call(endpoint,
                                                  VpcId=vpc_id,
                                                  CidrBlock=cidr,
                                                  AvailabilityZone="%s%s" % (
                                                      region, az))

    p3.pprint(str(http_response.status_code) + " - " + http_response.reason)
    p3.pprint(response_data)

    if http_response.status_code != 200:
        raise(ApiException)

    subnet_id = response_data['Subnet']['SubnetId']
    return subnet_id


@poll_api
def destroy_subnet(aws_creds, region, subnet_id=""):
    print('Destroying subnet %s' % str(subnet_id))
    session = botocore.session.get_session()
    session.set_credentials(aws_creds.access_key, aws_creds.secret_key)
    ec2 = session.get_service('ec2')
    operation = ec2.get_operation('DeleteSubnet')
    endpoint = ec2.get_endpoint(region)
    http_response, response_data = operation.call(endpoint,
                                                  SubnetId=subnet_id)
    p3.pprint(str(http_response.status_code) + " - " + http_response.reason)
    p3.pprint(response_data)

    if http_response.status_code != 200:
        raise(ApiException)

    return True


@poll_api
def build_security_group(aws_creds, region, sg_name="", vpc_id=""):
    print('Building security group')
    session = botocore.session.get_session()
    session.set_credentials(aws_creds.access_key, aws_creds.secret_key)
    ec2 = session.get_service('ec2')
    operation = ec2.get_operation('CreateSecurityGroup')
    endpoint = ec2.get_endpoint(region)
    http_response, response_data = operation.call(endpoint,
                                                  GroupName=sg_name,
                                                  Description=sg_name,
                                                  VpcId=vpc_id)

    p3.pprint(str(http_response.status_code) + " - " + http_response.reason)
    p3.pprint(response_data)

    if http_response.status_code != 200:
        raise(ApiException)

    sg_id = response_data['GroupId']
    return sg_id


@poll_api
def destroy_security_group(aws_creds, region, sg_id=""):
    print('Destroying security group')
    session = botocore.session.get_session()
    session.set_credentials(aws_creds.access_key, aws_creds.secret_key)
    ec2 = session.get_service('ec2')
    operation = ec2.get_operation('DeleteSecurityGroup')
    endpoint = ec2.get_endpoint(region)
    http_response, response_data = operation.call(endpoint,
                                                  GroupId=sg_id)

    p3.pprint(str(http_response.status_code) + " - " + http_response.reason)
    p3.pprint(response_data)

    if http_response.status_code != 200:
        raise(ApiException)

    return True


@poll_api
def build_elb(aws_creds, region, lb_name="", subnets=[], elb_sg_id=""):
    print('Building elb')
    session = botocore.session.get_session()
    session.set_credentials(aws_creds.access_key, aws_creds.secret_key)
    elb = session.get_service('elb')
    operation = elb.get_operation('CreateLoadBalancer')
    endpoint = elb.get_endpoint(region)
    http_response, response_data = operation.call(endpoint,
                                                  LoadBalancerName=lb_name,
                                                  Listeners=[
                                                      {"Protocol": 'http',
                                                       "LoadBalancerPort": 80,
                                                       "InstanceProtocol": 'http',
                                                       "InstancePort": 80}],
                                                  Subnets=subnets,
                                                  SecurityGroups=[elb_sg_id],
                                                  Scheme='internal')

    p3.pprint(str(http_response.status_code) + " - " + http_response.reason)
    p3.pprint(response_data)

    if http_response.status_code != 200:
        raise(ApiException)

    elb_name = response_data['DNSName']
    return elb_name


@poll_api
def destroy_elb(aws_creds, region, lb_name=""):
    print('Destroying elb')
    session = botocore.session.get_session()
    session.set_credentials(aws_creds.access_key, aws_creds.secret_key)
    elb = session.get_service('elb')
    operation = elb.get_operation('DeleteLoadBalancer')
    endpoint = elb.get_endpoint(region)
    http_response, response_data = operation.call(endpoint,
                                                  LoadBalancerName=lb_name)

    p3.pprint(str(http_response.status_code) + " - " + http_response.reason)
    p3.pprint(response_data)

    if http_response.status_code != 200:
        raise(ApiException)

    return True

if __name__ == '__main__':
    main()
