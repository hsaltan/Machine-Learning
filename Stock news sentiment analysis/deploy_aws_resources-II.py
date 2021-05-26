# Import libraries
import sys
sys.path.insert(1, 'YOUR_PATH_TO_AWSResourceDeploy_SCRIPT_ON_YOUR_LOCAL_MACHINE')
sys.path.insert(1, 'YOUR_PATH_TO_inquire_SCRIPT_ON_YOUR_LOCAL_MACHINE')
import boto3
import time
import json
import os
from colorama import Fore, Back, Style
import AWSResourceDeploy as aws
import inquire as inq
from requests import get
from datetime import datetime


# Set AWS region
region = 'eu-west-1'

# Runs commands on one or more managed instances
def run_ssm_commands():
    runCommandsWithParametersDocument = "AWS-RunShellScript"
    parameterName = 'S3BucketCopy'
    parameterDescription = 'S3 bucket files to copy to ec2 instance'
    parameterValue = "s3://" + bucketName + " /scripts"
    parameterType = "String"
    key = "NAME"
    value = "SSMS3Parameter"
    aws.create_parameter(parameterName, parameterDescription, parameterValue, parameterType,
                            key, value, region)
    t1, t2, t3 = 3, 10, 15
    command_items = [
        ("sudo yum install python37 -y", t3),
        ("pip3 install pip --upgrade", t2),
        ("pip3 install boto3", t2),
        ("pip3 install beautifulsoup4", t2),
        ("pip3 install pandas", t2),
        ("pip3 install numpy", t2),
        ("pip3 install requests", t2),
        ("pip3 install colorama", t2),
        ("pip3 install inquirer", t2),
        ("pip3 install matplotlib", t2),
        ("pip3 install textblob", t2),
        ("pip3 install pandas-datareader", t2),
        ("pip3 install psycopg2", t3),
        ("pip3 install scipy", t3),
        ("pip3 install scikit-learn", t3),
        ("pip3 install statsmodels", t3),
        ("aws s3 sync {{ssm:S3BucketCopy}}", t1),
    ]
    for command_item in command_items:
        command = command_item[0]
        seconds = command_item[1]
        status = aws.send_parameter_ssm_commands(instanceID, runCommandsWithParametersDocument, 
                                                    command, seconds, region)
        print(f"{Fore.MAGENTA}Status for{Style.RESET_ALL} {Fore.CYAN}{command}{Style.RESET_ALL} {Fore.MAGENTA}by{Style.RESET_ALL} {Fore.CYAN}{runCommandsWithParametersDocument}:{Style.RESET_ALL} {Fore.GREEN}{status}{Style.RESET_ALL}")
        print('\n')
    print('\n')

# Create IAM policies and roles
def organize_iam_for_ec2():

    # Create a policy document for EC2
    ec2AccessPolicyJsonDocument = {
            "Version": "2012-10-17",
            "Statement": [
            {
                "Sid": "ec201",
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:ListAllMyBuckets",
                    "s3:GetBucketLocation",
                    "s3:CreateBucket",
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:PutBucketPublicAccessBlock",
                    "s3:PutObjectTagging"
                ],
                "Resource": '*'
            },
            {
                "Sid": "ssm01",
                "Effect": "Allow",
                "Action": [
                    "ssm:CancelCommand",
                    "ssm:GetCommandInvocation",
                    "ssm:ListCommandInvocations",
                    "ssm:ListCommands",
                    "ssm:SendCommand",
                    "ssm:GetAutomationExecution",
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath",
                    "ssm:StartAutomationExecution",
                    "ssm:ListTagsForResource",
                    "ssm:GetCalendarState",
                    "ssm:DescribeAssociation",
                    "ssm:GetDeployablePatchSnapshotForInstance",
                    "ssm:GetDocument",
                    "ssm:DescribeDocument",
                    "ssm:GetManifest",
                    "ssm:ListAssociations",
                    "ssm:ListInstanceAssociations",
                    "ssm:PutInventory",
                    "ssm:PutComplianceItems",
                    "ssm:PutConfigurePackageResult",
                    "ssm:UpdateAssociationStatus",
                    "ssm:UpdateInstanceAssociationStatus",
                    "ssm:UpdateInstanceInformation"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "rds:RestoreDBInstanceFromS3",
                    "rds:DeleteDBSnapshot",
                    "rds:StopDBInstance",
                    "rds:StartDBInstance",
                    "rds:DescribeDBInstances",
                    "rds:AddRoleToDBInstance",
                    "rds:CreateDBSecurityGroup",
                    "rds:CreateDBSnapshot",
                    "rds:RestoreDBInstanceFromDBSnapshot",
                    "rds:RebootDBInstance",
                    "rds:DeleteDBSecurityGroup",
                    "rds:CreateDBInstance",
                    "rds:ModifyDBInstance",
                    "rds:RestoreDBInstanceToPointInTime",
                    "rds:DeleteDBInstance",
                    "rds-db:connect",
                    "rds:BeginTransaction",
                    "rds:CommitTransaction",
                    "rds:ExecuteSql",
                    "rds:ExecuteStatement",
                    "rds:RollbackTransaction"

                ],
                "Resource": "arn:aws:rds:*:138633676667:db:*"
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Allow",
                "Action": "rds:DeleteDBInstanceAutomatedBackup",
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ssmmessages:CreateControlChannel",
                    "ssmmessages:CreateDataChannel",
                    "ssmmessages:OpenControlChannel",
                    "ssmmessages:OpenDataChannel"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstanceAttribute",
                    "ec2:DescribeInstanceStatus",
                    "ec2:DescribeInstances"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ec2messages:AcknowledgeMessage",
                    "ec2messages:DeleteMessage",
                    "ec2messages:FailMessage",
                    "ec2messages:GetEndpoint",
                    "ec2messages:GetMessages",
                    "ec2messages:SendReply"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": [
                    "arn:aws:lambda:*:*:function:SSM*",
                    "arn:aws:lambda:*:*:function:*:SSM*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "states:DescribeExecution",
                    "states:StartExecution"
                ],
                "Resource": [
                    "arn:aws:states:*:*:stateMachine:SSM*",
                    "arn:aws:states:*:*:execution:SSM*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "resource-groups:ListGroups",
                    "resource-groups:ListGroupResources",
                    "resource-groups:GetGroupQuery"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cloudformation:DescribeStacks",
                    "cloudformation:ListStackResources"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "tag:GetResources"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "config:SelectResourceConfig"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "compute-optimizer:GetEC2InstanceRecommendations"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "support:DescribeTrustedAdvisorChecks",
                    "support:DescribeTrustedAdvisorCheckSummaries",
                    "support:DescribeTrustedAdvisorCheckResult",
                    "support:DescribeCases"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "config:DescribeComplianceByConfigRule",
                    "config:DescribeComplianceByResource",
                    "config:DescribeRemediationConfigurations"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": "iam:PassRole",
                "Resource": "*",
                "Condition": {
                    "StringEquals": {
                        "iam:PassedToService": [
                            "ssm.amazonaws.com"
                        ]
                    }
                }
            },
            {
                "Effect": "Allow",
                "Action": "organizations:DescribeOrganization",
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": "cloudformation:ListStackSets",
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cloudformation:ListStackInstances",
                    "cloudformation:DescribeStackSetOperation",
                    "cloudformation:DeleteStackSet"
                ],
                "Resource": "arn:aws:cloudformation:*:*:stackset/AWS-QuickSetup-SSM*:*"
            },
            {
                "Effect": "Allow",
                "Action": "cloudformation:DeleteStackInstances",
                "Resource": [
                    "arn:aws:cloudformation:*:*:stackset/AWS-QuickSetup-SSM*:*",
                    "arn:aws:cloudformation:*:*:stackset-target/AWS-QuickSetup-SSM*:*",
                    "arn:aws:cloudformation:*:*:type/resource/*"
                ]
            }
        ]
    }
    ec2AccessPolicyDocument = json.dumps(ec2AccessPolicyJsonDocument, indent = 4)
    
    # Create a policy for the EC2 instance
    ec2PolicyName = 'EC2SSMS3Access-Policy'
    ec2PolicyDescription = "policy for accessing SSM and S3"
    ec2AccessPolicyARN = aws.create_policy(ec2PolicyName, ec2AccessPolicyDocument, ec2PolicyDescription, region)

    # Create an assume role policy document for EC2
    assumeRolePolicyJsonDocument={
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Action': [
                    'sts:AssumeRole'
                ],
                'Principal': {
                    'Service': [
                        'ec2.amazonaws.com'
                    ]
                }
            }
        ]
    }
    assumeRolePolicyDocument = json.dumps(assumeRolePolicyJsonDocument, indent = 4)

    # Create a role for EC2
    ec2RoleName = "EC2SSMS3-Role"
    ec2RoleDescription = "EC2 access to S3 for getting and uploading file"
    key = 'NAME'
    value = 'EC2-SSMS3'
    ec2RoleName, _ = aws.create_role(ec2RoleName, assumeRolePolicyDocument, ec2RoleDescription, key, value, region)
    time.sleep(10)

    # Attach the policy to EC2
    aws.attach_policy(ec2AccessPolicyARN, ec2RoleName, region)
    return ec2RoleName

# Use the existing key pair
def get_key_pair():
    print('\n')
    path_2 = input(f"{Fore.MAGENTA}Type the path where the key pair is located on the local machine, e.g. /main_dir/sub_dir/sub_dir2/.../: {Style.RESET_ALL}")
    print('\n')
    files = os.listdir(path_2)
    key_pairs = []
    for f in files:
        key_pairs.append(f)
    if '.DS_Store' in key_pairs:
        key_pairs.remove('.DS_Store')
    message = f"{Fore.MAGENTA}Select the regional key pair{Style.RESET_ALL}"
    name = 'key-pair'
    options = key_pairs
    keyName = inq.define_list(name, message, options)
    print('\n')
    completeName = os.path.join(path_2, keyName)
    return completeName, keyName

# Describe the existing security groups and identify the default one
def get_default_sg():
    key = 'group-name'
    value = 'default'
    _, defaultSecurityGroup = aws.describe_security_groups(key, value, region)
    defaultSgId = defaultSecurityGroup['GroupId']
    return defaultSgId

# Launch the server
def start_ec2_instance():

    # Find the default security group ID
    sgID = get_default_sg()

    # Get the key pair directory and file
    completeName, keyName = get_key_pair()

    # Get the IAM role for the server
    ec2RoleName = organize_iam_for_ec2()

    # Create an instance profile
    instanceProfileName = 'StockNewsEffectSearcherServer'
    aws.create_instance_profile(instanceProfileName, region)

    # Attach the S3 Access role to the instance profile
    aws.attach_role_to_instance_profile(ec2RoleName, instanceProfileName, region)

    # Enter an AMI
    ami = input(f"{Fore.MAGENTA}Enter a valid AMI for the selected region: {Style.RESET_ALL}")
    print('\n')

    # Enter an instance type
    instanceType = input(f"{Fore.MAGENTA}Enter a valid instance type for the selected region: {Style.RESET_ALL}")
    print('\n')

    userDataScript = """#!/bin/bash
    sudo yum update -y
    sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
    cd /
    sudo mkdir -m 777 scripts
    """

    # Describe the EC2 parameters
    volumeSize = 8
    volumeType = 'gp2'
    keyName = keyName.replace('.pem', "")
    maxCount = 1
    minCount = 1
    subnetID ='subnet-03aaaa4b'
    instanceName = 'stock-news-server'
    key = "Name"
    value = instanceName

    # Launch the instance
    instanceID = aws.launch_ec2_instance(volumeSize, volumeType, ami, instanceType,
                                keyName, maxCount, minCount, sgID, subnetID, userDataScript, 
                                instanceName, instanceProfileName, key, value,
                                region)

    # Describe the instance status and find the hostname
    aws.describe_instance_status(instanceID, region)
    instanceInfo = aws.describe_instance(instanceID, region)
    publicDNSName = instanceInfo['Reservations'][0]['Instances'][0]['PublicDnsName']
    username="ec2-user"
    hostname = username + "@" + publicDNSName

    # Find your public IP
    publicIP = get('https://api.ipify.org').text + "/32"

    return instanceID, hostname, completeName

# Create an S3 bucket
def organize_s3():
    now = datetime.now()
    dt_string = now.strftime("%Y-%b-%d-%H-%M-%S")
    bucketName = "s3b-" + dt_string.lower()
    bucketArn = "arn:aws:s3:::"+bucketName+"/*"
    aws.create_bucket(bucketName, region)
    return bucketName, bucketArn

# Upload the script files to S3
def upload_file():
    bucketName, bucketArn = organize_s3()
    path = '/Users/hasanserdaraltan/OneDrive/Files/Education/Data_Science/Lab/ZLS0003-Stocks_News_Performance/'
    for file in files:
        body = path + file
        key = 'NAME'
        value = 'Script'
        aws.put_object(body, bucketName, file, key, value, region)
    return bucketName, bucketArn

# Create an instance
instanceID, hostname, completeName = start_ec2_instance()

# Script files to be uploaded to S3
files = [
            'main.py',
            'query.py',
            'link_finder.py',
            'polarity_finder.py',
            'price_finder.py',
            'return_calculator.py',
            'analysis.py',
            'inquire.py',
            'AWSResourceDeploy.py'
        ]

# Create a bucket to upload the script files
bucketName, bucketArn = upload_file()

# Create a parameter and run document on Systems Manager to run the scripts on EC2 instance 
run_ssm_commands()

# SSH connect to the instance
aws.ssh_connect(instanceID, hostname, completeName)
