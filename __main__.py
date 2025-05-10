"""An AWS Python Pulumi program"""

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


)


#}2

