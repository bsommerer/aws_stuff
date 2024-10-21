import boto3
from classic_lb_to_elb import lambda_handler, CLB_NAME, REGION

# Test imports
from moto import mock_aws
import pytest
import os

# Test ressources
@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'

@pytest.fixture
def mocked_aws(aws_credentials):
    with mock_aws():
        yield

@pytest.fixture
def ec2_client(mocked_aws):
    return boto3.client('ec2', region_name=REGION)

@pytest.fixture
def elb_client(mocked_aws):
    return boto3.client('elb', region_name=REGION)

@pytest.fixture
def elbv2_client(mocked_aws):
    return boto3.client('elbv2', region_name=REGION)

@pytest.fixture
def vpc(ec2_client):
    vpc_response = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')
    return vpc_response['Vpc']['VpcId']

@pytest.fixture
def instance_ids(ec2_client):
    """Create and return a list of mock EC2 instance IDs."""
    instances = ec2_client.run_instances(
        ImageId='ami-12345678',
        MinCount=3,
        MaxCount=3,
        InstanceType='t2.micro'
    )['Instances']
    instance_ids = [instance['InstanceId'] for instance in instances]
    ec2_client.start_instances(InstanceIds=instance_ids)
    return instance_ids

@pytest.fixture
def classic_load_balancer(elb_client):
    """Create a mock Classic Load Balancer."""
    elb_client.create_load_balancer(
        LoadBalancerName=CLB_NAME,
        Listeners=[
            {
                'Protocol': 'HTTP',
                'LoadBalancerPort': 80,
                'InstancePort': 8080,
                'InstanceProtocol': 'HTTP'
            }
        ],
        AvailabilityZones=['us-east-1a']
    )

@pytest.fixture
def target_group(vpc, elbv2_client):
    """Create a mock Target Group and return its ARN."""
    target_group_arn = elbv2_client.create_target_group(
        Name='test-target-group',
        Protocol='HTTP',
        Port=80,
        VpcId=vpc
    )['TargetGroups'][0]['TargetGroupArn']
    return target_group_arn

# Test Cases

def test_no_instances_in_clb_or_target_group(classic_load_balancer, target_group, elb_client, elbv2_client):
    """Test case when there are no instances in both CLB and Target Group."""
    lambda_handler({}, {}, target_group_arn=target_group)

    # Verify that no instances are registered in Target Group
    target_health = elbv2_client.describe_target_health(TargetGroupArn=target_group)['TargetHealthDescriptions']
    assert len(target_health) == 0

def test_instances_in_clb_but_none_in_target_group(classic_load_balancer, target_group, elb_client, elbv2_client, instance_ids):
    """Test case where instances are in CLB but not in Target Group."""
    # Register instances in CLB
    elb_client.register_instances_with_load_balancer(
        LoadBalancerName=CLB_NAME,
        Instances=[{'InstanceId': iid} for iid in instance_ids[:2]]  # Register first two instances
    )

    lambda_handler({}, {}, target_group_arn=target_group)

    # Verify that instances are registered in Target Group
    target_health = elbv2_client.describe_target_health(TargetGroupArn=target_group)['TargetHealthDescriptions']
    target_ids = [target['Target']['Id'] for target in target_health]

    assert set(target_ids) == set(instance_ids[:2])

def test_instances_in_target_group_but_none_in_clb(classic_load_balancer, target_group, elb_client, elbv2_client, instance_ids):
    """Test case where instances are in Target Group but not in CLB."""
    # Register instances in Target Group
    elbv2_client.register_targets(
        TargetGroupArn=target_group,
        Targets=[{'Id': iid} for iid in instance_ids[:2]]  # Register first two instances
    )

    lambda_handler({}, {}, target_group_arn=target_group)

    # Verify that no instances remain in Target Group
    target_health = elbv2_client.describe_target_health(TargetGroupArn=target_group)['TargetHealthDescriptions']
    assert len(target_health) == 0

def test_instances_in_clb_and_target_group_matching(classic_load_balancer, target_group, elb_client, elbv2_client, instance_ids):
    """Test case where instances in CLB and Target Group are already matching."""
    # Register instances in both CLB and Target Group
    elb_client.register_instances_with_load_balancer(
        LoadBalancerName=CLB_NAME,
        Instances=[{'InstanceId': iid} for iid in instance_ids[:2]]  # Register first two instances in CLB
    )

    elbv2_client.register_targets(
        TargetGroupArn=target_group,
        Targets=[{'Id': iid} for iid in instance_ids[:2]]  # Register first two instances in Target Group
    )

    lambda_handler({}, {}, target_group_arn=target_group)

    # Verify that instances remain registered in Target Group
    target_health = elbv2_client.describe_target_health(TargetGroupArn=target_group)['TargetHealthDescriptions']
    target_ids = [target['Target']['Id'] for target in target_health]

    assert set(target_ids) == set(instance_ids[:2])

def test_instances_in_clb_and_target_group_with_missing_instances(classic_load_balancer, target_group, elb_client, elbv2_client, instance_ids):
    """Test case where some instances are in CLB but not in Target Group."""
    # Register instances in CLB
    elb_client.register_instances_with_load_balancer(
        LoadBalancerName=CLB_NAME,
        Instances=[{'InstanceId': iid} for iid in instance_ids[:2]]  # Register first two instances in CLB
    )

    # Register only one instance in Target Group
    elbv2_client.register_targets(
        TargetGroupArn=target_group,
        Targets=[{'Id': instance_ids[0]}]  # Register first instance only in Target Group
    )

    lambda_handler({}, {}, target_group_arn=target_group)

    # Verify that missing instance is registered in Target Group
    target_health = elbv2_client.describe_target_health(TargetGroupArn=target_group)['TargetHealthDescriptions']
    target_ids = [target['Target']['Id'] for target in target_health]

    expected_ids = [instance_ids[0], instance_ids[1]]
    assert set(target_ids) == set(expected_ids)


def test_instances_in_clb_and_target_group_with_extra_instances(classic_load_balancer, target_group, elb_client, elbv2_client, instance_ids):
    """Test case where there are extra instances in the Target Group."""
    # Register instances in CLB
    elb_client.register_instances_with_load_balancer(
        LoadBalancerName=CLB_NAME,
        Instances=[{'InstanceId': iid} for iid in instance_ids[:2]]  # Register first two instances in CLB
    )

    # Register all instances in Target Group
    elbv2_client.register_targets(
        TargetGroupArn=target_group,
        Targets=[{'Id': iid} for iid in instance_ids]  # Register all instances in Target Group
    )

    lambda_handler({}, {}, target_group_arn=target_group)

    # Verify that extra instance is deregistered from Target Group
    target_health = elbv2_client.describe_target_health(TargetGroupArn=target_group)['TargetHealthDescriptions']
    target_ids = [target['Target']['Id'] for target in target_health]

    expected_ids = [instance_ids[0], instance_ids[1]]  # The ones registered in CLB
    assert set(target_ids) == set(expected_ids)