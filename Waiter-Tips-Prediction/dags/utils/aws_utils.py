"""
    This module enables for working on a few AWS services.

    This script requires that `boto3` be installed within the Python environment you are
    running this script in.

    The script helps creating and getting parameters on Parameter Store, getting an object
    from and putting an object in S3 bucket, and sending email notifications to subscribers.

    This file can also be imported as a module and contains the following
    functions:

        * get_parameter - Retrieves a parameter from AWS Parameter Store to use it in the code
        * create_parameter - Creates a parameter on AWS Parameter Store to later use it in the code
        * get_bucket_object - Imports or gets an object from an S3 bucket
        * put_object - Puts an object to the S3 bucket
        * send_sns_topic_message - Sends a notification to subscribers by email.
"""

# Import libraries
from typing import IO, Any, Union

import boto3

s3 = boto3.resource("s3")
region: str = "eu-west-1"


def get_parameter(
    parameter_name: str, with_decryption: bool = False
) -> Union[int, str, list]:

    """
    Retrieves a parameter from AWS Parameter Store to use it in the code.
    """

    response = boto3.client("ssm", region_name=region).get_parameter(
        Name=parameter_name, WithDecryption=with_decryption
    )
    parameter_value = response["Parameter"]["Value"]

    return parameter_value


def create_parameter(
    parameter_name: str,
    parameter_description: str,
    parameter_value: Any,
    parameter_type: str,
) -> int:

    """
    Creates a parameter on AWS Parameter Store to later use it in the code.
    """

    response = boto3.client("ssm", region_name=region).put_parameter(
        Name=parameter_name,
        Description=parameter_description,
        Value=parameter_value,
        Type=parameter_type,
        Overwrite=True,
    )

    parameter_version = response["Version"]

    print(
        "Parameter '%s' of version '%s' has been created in AWS Parameter Store.",
        parameter_name,
        parameter_version,
    )
    print("\n")

    return parameter_version


def get_bucket_object(bucket_name: str, object_key: str) -> tuple[IO[str], str]:

    """
    Imports or gets an object from an S3 bucket.
    """

    response = boto3.client("s3").get_object(
        Bucket=bucket_name,
        Key=object_key,
    )

    file_object = response["Body"]
    object_etag = response["ETag"]

    return file_object, object_etag


def put_object(
    body: str,
    bucket_name: str,
    file_name: str,
    key: str,
    value: str,
) -> dict[str, Any]:

    """
    Puts an object to the S3 bucket.
    """

    response = s3.meta.client.upload_file(body, bucket_name, file_name)
    boto3.client("s3", region_name=region).put_object_tagging(
        Bucket=bucket_name,
        Key=file_name,
        Tagging={
            "TagSet": [
                {"Key": key, "Value": value},
            ]
        },
    )
    print("File '%s' has been uploaded to the bucket '%s'.", file_name, bucket_name)
    print("\n")

    return response


def send_sns_topic_message(topic_arn: str, message: str, subject: str) -> str:

    """
    Sends a notification to subscribers by email.
    """

    response = boto3.client("sns", region_name=region).publish(
        TopicArn=topic_arn,
        Message=message,
        Subject=subject,
        MessageStructure="string",
    )

    message_id = response["MessageId"]

    return message_id
