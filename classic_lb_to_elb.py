import boto3

REGION = 'us-east-1'
CLB_NAME = 'test-clb'

def lambda_handler(event, context, target_group_arn=None):
    elb_client = boto3.client('elb', region_name=REGION)      # Für den Classic Load Balancer
    elbv2_client = boto3.client('elbv2', region_name=REGION)  # Für die Target Group

    # Abrufen der Instanzen vom CLB
    clb_instances = elb_client.describe_instance_health(
        LoadBalancerName=CLB_NAME
    )['InstanceStates']
    clb_instance_ids = [instance['InstanceId'] for instance in clb_instances]

    # Abrufen der Instanzen aus der Target Group
    target_health_descriptions = elbv2_client.describe_target_health(
        TargetGroupArn=target_group_arn
    )['TargetHealthDescriptions']

    target_group_instance_ids = [target['Target']['Id'] for target in target_health_descriptions]

    # Finden der Instanzen, die im CLB sind, aber nicht in der Target Group
    instances_to_register = list(set(clb_instance_ids) - set(target_group_instance_ids))

    # Finden der Instanzen, die in der Target Group sind, aber nicht im CLB
    instances_to_deregister = list(set(target_group_instance_ids) - set(clb_instance_ids))

    if instances_to_register:
        # Registrieren der fehlenden Instanzen in der Target Group
        targets = [{'Id': instance_id} for instance_id in instances_to_register]
        elbv2_client.register_targets(
            TargetGroupArn=target_group_arn,
            Targets=targets
        )
        print(f"Registrierte Instanzen in der Target Group: {instances_to_register}")
    else:
        print("Keine neuen Instanzen zum Registrieren.")

    if instances_to_deregister:
        # Deregistrieren der nicht mehr benötigten Instanzen aus der Target Group
        targets = [{'Id': instance_id} for instance_id in instances_to_deregister]
        elbv2_client.deregister_targets(
            TargetGroupArn=target_group_arn,
            Targets=targets
        )
        print(f"Deregistrierte Instanzen aus der Target Group: {instances_to_deregister}")
    else:
        print("Keine Instanzen zum Deregistrieren.")