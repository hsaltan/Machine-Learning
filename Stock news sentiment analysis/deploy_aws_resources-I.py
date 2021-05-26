# Import libraries
import sys
sys.path.insert(1, 'YOUR_PATH_TO_AWSResourceDeploy_SCRIPT_ON_YOUR_LOCAL_MACHINE')
from colorama import Fore, Back, Style
import time
import json
import AWSResourceDeploy as aws
from requests import get


# Set AWS region
region = 'eu-west-1'

# Find your public IP
publicIP = get('https://api.ipify.org').text + "/32"

# Describe the existing security groups and identify the default one
def get_default_sg():
    key = 'group-name'
    value = 'default'
    _, defaultSecurityGroup = aws.describe_security_groups(key, value, region)
    defaultSgId = defaultSecurityGroup['GroupId']
    return defaultSgId

# Create an ingress SSH rule
def sg_ssh_rule(sgID, publicIP):

    # SSH rule
    port = 22
    ipProtocol = 'tcp'
    sgDescription =  'SSH ingress rule'
    aws.create_sg_rule(sgID, port, ipProtocol, publicIP, sgDescription, region)

    # PostgreSQL rule
    port = 5432
    ipProtocol = 'tcp'
    sgDescription =  'PostgreSQL ingress rule'
    aws.create_sg_rule(sgID, port, ipProtocol, publicIP, sgDescription, region)

# Create policies and roles for RDS
def organize_iam_for_rds():

    # 1. Create an assume role policy document for RDS
    assumeRolePolicyJsonDocumentForRDS={
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Action': [
                    'sts:AssumeRole'
                ],
                'Principal': {
                    'Service': [
                        'rds.amazonaws.com'
                    ]
                }
            }
        ]
    }
    assumeRolePolicyDocumentForRDS = json.dumps(assumeRolePolicyJsonDocumentForRDS, indent = 4)

    # 2.a. Create a read policy document for the RDS instance
    rdsReadAccessPolicyJsonDocument = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "rds01",
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetObject",
                ],
                "Resource": '*'
            },
        ]
    }
    rdsReadAccessPolicyDocument = json.dumps(rdsReadAccessPolicyJsonDocument, indent = 4)

    # 2.b. Create a read policy for the RDS instance
    readPolicyName = 'RDSS3ReadAccess-Policy'
    readPolicyDescription = "policy for RDS accessing S3 for read"
    rdsReadAccessPolicyARN = aws.create_policy(readPolicyName, rdsReadAccessPolicyDocument, readPolicyDescription, region)

    # 2.c. Create a read role for RDS
    readRoleName = "RDSS3Read-Role"
    readRoleDescription = "RDS access to S3 for getting files"
    key = 'NAME'
    value = 'RDS-S3'
    rdsReadRoleName, readRoleARN = aws.create_role(readRoleName, assumeRolePolicyDocumentForRDS, readRoleDescription, key, value, region)
    time.sleep(10)

    # 2.d. Attach the read policy to the role for RDS
    aws.attach_policy(rdsReadAccessPolicyARN, rdsReadRoleName, region)

    # 2.e. Add the read role to the RDS
    time.sleep(300)
    readFeatureName = 's3Import'
    aws.add_role_to_rds(dbInstanceIdentifier, readRoleARN, readFeatureName, region)

    # 3.a. Create a write policy document for the RDS instance
    rdsWriteAccessPolicyJsonDocument = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "rds02",
                "Effect": "Allow",
                "Action": [
                    "s3:AbortMultipartUpload",
                    "s3:PutObject"
                ],
                "Resource": '*'
            },
        ]
    }
    rdsWriteAccessPolicyDocument = json.dumps(rdsWriteAccessPolicyJsonDocument, indent = 4)

    # 3.b. Create a write policy for the RDS instance
    writePolicyName = 'RDSS3WriteAccess-Policy'
    writePolicyDescription = "policy for RDS accessing S3 for write"
    rdsWriteAccessPolicyARN = aws.create_policy(writePolicyName, rdsWriteAccessPolicyDocument, writePolicyDescription, region)

    # 3.c. Create a write role for RDS
    writeRoleName = "RDSS3Write-Role"
    writeRoleDescription = "RDS access to S3 for writing files"
    key = 'NAME'
    value = 'RDS-S3'
    rdsWriteRoleName, writeRoleARN = aws.create_role(writeRoleName, assumeRolePolicyDocumentForRDS, writeRoleDescription, key, value, region)
    time.sleep(10)

    # 3.d. Attach the write policy to the role for RDS
    aws.attach_policy(rdsWriteAccessPolicyARN, rdsWriteRoleName, region)

    # 3.e. Add the read role to the RDS
    writeFeatureName = 's3Export'
    aws.add_role_to_rds(dbInstanceIdentifier, writeRoleARN, writeFeatureName, region)

# Create parameters for database identifier and user password in Parameter Store
def create_ssm_parameter():
    dbiParamName = "dbInstanceIdentifier"
    dbiParamDescription = "RDS database instance identifier name"
    dbiParamValue = dbInstanceIdentifier
    dbiParamType = "String"
    dbiKey = "Name"
    dbiValue = "stocks"
    aws.create_parameter(dbiParamName, dbiParamDescription, dbiParamValue, dbiParamType, 
                        dbiKey, dbiValue, region)

    userPasswordParamName = "masterUserPassword"
    userPasswordParamDescription = "RDS database instance master user password"
    userPasswordParamValue = masterUserPassword
    userPasswordParamType = "SecureString"
    userPasswordKey = "Name"
    userPasswordValue = "stocks"
    aws.create_parameter(userPasswordParamName, userPasswordParamDescription, userPasswordParamValue, 
                        userPasswordParamType, userPasswordKey, userPasswordValue, region)

# Find the default security group ID
sgID = get_default_sg()

# Create ingress SSH and PostgreSQL rules
sg_ssh_rule(sgID, publicIP)

# Create an RDS instance
dbName = 'YOUR_DB_NAME'
dbInstanceIdentifier = 'YOUR_DB_INSTANCE_IDENTIFIER'
allocatedStorage = 20
dbInstanceClass = 'db.t2.micro'
engine = 'postgres'
masterUsername = 'YOUR_USERNAME'
masterUserPassword = 'YOUR_PASSWORD'
vpcSecurityGroupId = [sgID]
availabilityZone = 'eu-west-1a'
preferredMaintenanceWindow = 'Sun:04:00-Sun:04:30'
backupRetentionPeriod = 0
key = 'NAME'
value = 'stocks'
maxAllocatedStorage = 30

print('\n')
print(f"{Fore.MAGENTA}RDS instance is being initiated...{Style.RESET_ALL}")
print('\n')

aws.create_rds(dbName, dbInstanceIdentifier, allocatedStorage, dbInstanceClass, engine, masterUsername, 
                masterUserPassword, vpcSecurityGroupId, availabilityZone, preferredMaintenanceWindow,
                backupRetentionPeriod, key, value, maxAllocatedStorage, region)
time.sleep(3)

# Create parameters for database identifier and user password in Parameter Store
create_ssm_parameter()
time.sleep(3)

# Attach IAM roles to the RDS instance
organize_iam_for_rds()

print(f"{Fore.MAGENTA}RDS instance creation, security group rule adjustments, creation of necessary roles and policies and their attachments have been successfully fulfilled.{Style.RESET_ALL}")
print('\n')
