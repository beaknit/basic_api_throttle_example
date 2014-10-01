import argparse
import botocore.session
import pprint

global p3
p3 = pprint.PrettyPrinter(indent=4)


class ApiException(Exception):
    pass


class AWSCredential:

    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key


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

    except KeyboardInterrupt:
        print('Keyboard interrupt!')
    except Exception as e:
        print(e)

    finally:
        print("Tearing down...")
        destroy_subnet(creds, REGION, subnet_id=subnet_1)
        destroy_subnet(creds, REGION, subnet_id=subnet_2)
        destroy_vpc(creds, REGION, vpc_id=vpc_id)


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


if __name__ == '__main__':
    main()
