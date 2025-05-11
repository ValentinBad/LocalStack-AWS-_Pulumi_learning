"""An AWS Python Pulumi program"""
import json
import pulumi
import pulumi_aws as aws
from pulumi_aws import s3

localstack_provider = aws.Provider("localstack",
    region="us-east-1",
    access_key="test",
    secret_key="test",
    skip_credentials_validation=True,
    skip_metadata_api_check=True,
    s3_use_path_style=True,
    endpoints=[
        {"ec2": "http://localhost:4566"},
        {"sts": "http://localhost:4566"},
        {"ecs": "http://localhost:4566"},
        {"iam": "http://localhost:4566"},
        {"logs": "http://localhost:4566"},
        {"elbv2": "http://localhost:4566"},
    ]
)


#1 Practice with VPC{

#vpc
vpc = aws.ec2.Vpc("main-vpc",
cidr_block="10.0.0.0/16",
enable_dns_support=True,
enable_dns_hostnames=True,
tags = {"Name": "main-vpc"},
opts=pulumi.ResourceOptions(provider=localstack_provider)
)

#public subnet
public_subnet = aws.ec2.Subnet("public-subnet",
vpc_id=vpc.id,
cidr_block="10.0.1.0/24",
map_public_ip_on_launch=True,
availability_zone = "us-east-1a",
tags = {"Name": "public-subnet"},        
opts=pulumi.ResourceOptions(provider=localstack_provider)            
)

#internet getaway
igw = aws.ec2.InternetGateway("main-igw",
vpc_id=vpc.id,
tags = {"Name": "main-igw"} , 
opts=pulumi.ResourceOptions(provider=localstack_provider)
)

#Route table
route_table = aws.ec2.RouteTable("public-route-table",
vpc_id = vpc.id,
routes = [{
    "cidr_block" : "0.0.0.0/0",
    "gateway_id" : igw.id
}],
tags = {"Name": "public-route-table "}  ,
opts=pulumi.ResourceOptions(provider=localstack_provider)
)

route_table_assoc = aws.ec2.RouteTableAssociation("public-rt-assoc",
    subnet_id=public_subnet.id,
    route_table_id=route_table.id,
    opts=pulumi.ResourceOptions(provider=localstack_provider)
)

pulumi.export("vpc_id", vpc.id)
pulumi.export("subnet_id", public_subnet.id)
#}1

#2Security Group{
security_group = aws.ec2.SecurityGroup("my-security-group",
description="Allow SSH and HTTP traffic",
ingress=[
aws.ec2.SecurityGroupIngressArgs(
    from_port=22,
    to_port= 22,
    protocol="tcp",
    cidr_blocks=["0.0.0.0/0"],
),
aws.ec2.SecurityGroupIngressArgs(
    from_port=80,
    to_port=80,
    protocol="tcp",
    cidr_blocks=["0.0.0.0/0"],
),
],
egress=[
aws.ec2.SecurityGroupEgressArgs(
from_port=0,
to_port=0,
protocol="-1",
cidr_blocks=["0.0.0.0/0"],
),
],
opts=pulumi.ResourceOptions(provider=localstack_provider),
)
pulumi.export("security_group_id", security_group.id)

#}2

#3 NAT Gateway{
elastic_ip = aws.ec2.Eip("nat-eip",
   opts=pulumi.ResourceOptions(provider=localstack_provider),)

nat_instance = aws.ec2.Instance("nat-instance",
    ami="ami-0c55b159cbfafe1f0",  # Amazon Linux 2 AMI (update if needed)
    instance_type="t2.micro",     # Instance type (small and free-tier eligible)
    associate_public_ip_address=True,  # Attach a public IP
    key_name="test",      # Your SSH key name (must exist in AWS)
    security_groups=[security_group.name],  # Attach security group
    tags={"Name": "NAT Instance"},
    opts=pulumi.ResourceOptions(provider=localstack_provider),
)
pulumi.export("nat_instance_id", nat_instance.id)

#}3

# #4 NOT FREE lambda{

# # IAM role that Lambda can assume
# lambda_role = aws.iam.Role("lambda-exec-role",
#     assume_role_policy=json.dumps({
#         "Version": "2012-10-17",
#         "Statement": [{
#             "Action": "sts:AssumeRole",
#             "Principal": {
#                 "Service": "lambda.amazonaws.com"
#             },
#             "Effect": "Allow",
#             "Sid": ""
#         }]
#     }),
#     opts=pulumi.ResourceOptions(provider=localstack_provider)
# )

# # Inline policy to allow basic logging
# role_policy = aws.iam.RolePolicy("lambda-policy",
#     role=lambda_role.id,
#     policy=json.dumps({
#         "Version": "2012-10-17",
#         "Statement": [{
#             "Effect": "Allow",
#             "Action": ["logs:*"],
#             "Resource": "*"
#         }]
#     }),
#     opts=pulumi.ResourceOptions(provider=localstack_provider)
# )

# # The Lambda function code (inline for testing)
# lambda_function = aws.lambda_.Function("hello-lambda",
#     runtime="python3.8",
#     role=lambda_role.arn,
#     handler="index.handler",
#     code=pulumi.AssetArchive({
#         ".": pulumi.FileArchive("./lambda")  # folder with index.py file
#     }),
#     opts=pulumi.ResourceOptions(provider=localstack_provider)
# )

# pulumi.export("lambda_name", lambda_function.name)

# #}4

# #5 NOT FREE ecs{

# # ECS Cluster
# cluster = aws.ecs.Cluster("ecs-cluster",
#     opts=pulumi.ResourceOptions(provider=localstack_provider)
# )

# # Dummy role (LocalStack accepts this for simulation)
# execution_role = aws.iam.Role("ecsTaskExecutionRole",
#     assume_role_policy=json.dumps({
#         "Version": "2012-10-17",
#         "Statement": [{
#             "Action": "sts:AssumeRole",
#             "Principal": { "Service": "ecs-tasks.amazonaws.com" },
#             "Effect": "Allow",
#             "Sid": ""
#         }]
#     }),
#     opts=pulumi.ResourceOptions(provider=localstack_provider)
# )

# # Task Definition (nginx)
# task_definition = aws.ecs.TaskDefinition("nginx-task",
#     family="nginx",
#     cpu="256",
#     memory="512",
#     network_mode="bridge",
#     requires_compatibilities=["EC2"],
#     execution_role_arn=execution_role.arn,
#     container_definitions=json.dumps([{
#         "name": "nginx",
#         "image": "nginx",
#         "portMappings": [{
#             "containerPort": 80,
#             "hostPort": 8080,
#             "protocol": "tcp"
#         }]
#     }]),
#     opts=pulumi.ResourceOptions(provider=localstack_provider)
# )

# # ECS Service
# service = aws.ecs.Service("nginx-service",
#     cluster=cluster.arn,
#     desired_count=1,
#     launch_type="EC2",
#     task_definition=task_definition.arn,
#     opts=pulumi.ResourceOptions(provider=localstack_provider)
# )

# pulumi.export("cluster_name", cluster.name)
# pulumi.export("task_def", task_definition.arn)


# #}5

# Not free #6 App load balancer { 

# # Subnet 2 for ALB
# subnet2 = aws.ec2.Subnet("subnet-2", vpc_id=vpc.id, cidr_block="10.0.2.0/24",opts=pulumi.ResourceOptions(provider=localstack_provider))

# alb = aws.lb.LoadBalancer("main-alb",
#     internal=False,
#     load_balancer_type="application",
#     security_groups=[security_group.id],
#     subnets=[public_subnet.id , subnet2.id],
#     enable_deletion_protection=True,
# opts=pulumi.ResourceOptions(provider=localstack_provider)
# )

# listener = aws.lb.Listener("alb-listener",
#     load_balancer_arn=alb.arn,
#     port=80,
#     protocol="HTTP",
#     default_actions=[{
#         "type": "fixed-response",
#         "fixed_response": {
#             "status_code": 200,
#             "content_type": "text/plain",
#             "message_body": "OK"
#         }
#     }],
#     opts=pulumi.ResourceOptions(provider=localstack_provider)
# )

# #}6

