data "aws_ami" "server_ami" {
  most_recent = true

  owners = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}


/* Terraform LocalStack example
data "aws_ami" "server_ami" {
  most_recent      = true

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
} */


data "aws_iam_policy_document" "wtp_ec2_policy_doc" {
  statement {

    sid = "1"

    effect = "Allow"

    actions = [
      "rds:*",
      "s3:*",
      "sns:*",
      "ssm:*"
    ]

    resources = ["*"]
  }
}
