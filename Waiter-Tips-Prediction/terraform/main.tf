resource "aws_iam_policy" "wtp_ec2_policy" {
  name   = "wtp_ec2_policy"
  path   = "/"
  policy = data.aws_iam_policy_document.wtp_ec2_policy_doc.json
}

resource "aws_iam_role" "wtp_ec2_role" {
  name = "wtp_ec2_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })

  tags = {
    tag-key = "wtp_ec2_role"
  }
}

resource "aws_iam_role_policy_attachment" "wtp_ec2_policy_attach" {
  role       = aws_iam_role.wtp_ec2_role.name
  policy_arn = aws_iam_policy.wtp_ec2_policy.arn
}

resource "aws_iam_instance_profile" "wtp_ec2_profile" {
  name = "wtp_ec2_profile"
  role = aws_iam_role.wtp_ec2_role.name
}

resource "aws_vpc" "wtp_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "wtp-vpc"
    Environment = "production"
  }
}

resource "aws_subnet" "wtp_public_subnet" {
  vpc_id                  = aws_vpc.wtp_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "eu-west-1a"

  tags = {
    Name        = "wtp-pub_subnet"
    Environment = "production"
  }
}

resource "aws_subnet" "wtp_private_subnet" {
  vpc_id            = aws_vpc.wtp_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "eu-west-1b"

  tags = {
    Name        = "wtp-pri_subnet"
    Environment = "production"
  }
}

resource "aws_internet_gateway" "wtp_igw" {
  vpc_id = aws_vpc.wtp_vpc.id

  tags = {
    Name        = "wtp-igw"
    Environment = "production"
  }
}

resource "aws_route_table" "wtp_public_rt" {
  vpc_id = aws_vpc.wtp_vpc.id

  tags = {
    Name        = "wtp-pub_rt"
    Environment = "production"
  }
}

resource "aws_route" "public_route" {
  route_table_id         = aws_route_table.wtp_public_rt.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.wtp_igw.id
}

resource "aws_route_table_association" "wtp_public_assoc" {
  subnet_id      = aws_subnet.wtp_public_subnet.id
  route_table_id = aws_route_table.wtp_public_rt.id
}

resource "aws_security_group" "wtp_ec2_sg" {
  name        = "wtp-ec2_sg"
  description = "wtp security group for ec2 instance"
  vpc_id      = aws_vpc.wtp_vpc.id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "wtp-ec2_sg"
    Environment = "production"
  }
}

resource "aws_security_group" "wtp_rds_sg" {
  name        = "wtp-rds_sg"
  description = "wtp security group for rds instance"
  vpc_id      = aws_vpc.wtp_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.wtp_ec2_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "wtp-rds_sg"
    Environment = "production"
  }
}

resource "aws_s3_bucket" "s3b-tip-predictor" {
  bucket = var.bucket
  tags = {
    Name        = "my-bucket"
    Environment = "production"
  }
}

resource "aws_s3_bucket_public_access_block" "wtp_public_access" {
  bucket = aws_s3_bucket.s3b-tip-predictor.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "wtp_bucket_acl" {
  bucket = aws_s3_bucket.s3b-tip-predictor.id
  acl    = "public-read"
}

resource "aws_s3_object" "object1" {
  bucket = aws_s3_bucket.s3b-tip-predictor.id
  acl    = "private"
  key    = "config/requirements.txt"
  source = "../requirements.txt"
}

resource "aws_s3_object" "object2" {
  bucket = aws_s3_bucket.s3b-tip-predictor.id
  acl    = "private"
  key    = "config/prometheus-config.yml"
  source = "../prometheus-config.yml"
}

resource "aws_s3_object" "object3" {
  bucket = aws_s3_bucket.s3b-tip-predictor.id
  acl    = "private"
  key    = "config/start.sh"
  source = "../start.sh"
}

resource "aws_key_pair" "wtp_key" {
  key_name   = "wtpkey"
  public_key = file("~/.ssh/wtpkey.pub")
}

resource "aws_instance" "wtp_node" {
  ami                    = data.aws_ami.server_ami.id
  instance_type          = "t2.large"
  key_name               = aws_key_pair.wtp_key.id
  vpc_security_group_ids = [aws_security_group.wtp_ec2_sg.id]
  subnet_id              = aws_subnet.wtp_public_subnet.id
  iam_instance_profile   = aws_iam_instance_profile.wtp_ec2_profile.name
  user_data              = file("userdata.sh")

  root_block_device {
    volume_size = 30
  }

  tags = {
    Name        = "wtp-ec2"
    Environment = "production"
  }

  provisioner "local-exec" {
    command = templatefile("linux-ssh-config.tpl", {
      hostname     = self.public_ip,
      user         = "ubuntu",
      identityfile = "~/.ssh/wtpkey"
    })
    interpreter = ["bash", "-c"]
  }
}

resource "aws_s3_object" "data_folder" {
  bucket = aws_s3_bucket.s3b-tip-predictor.id
  acl    = "public-read"
  key    = "data/tips.csv"
  source = "../data/tips.csv"
}

resource "aws_s3_object" "evidently_folder" {
  bucket = aws_s3_bucket.s3b-tip-predictor.id
  acl    = "private"
  key    = "evidently/"
  source = "../init.txt"
}

resource "aws_s3_object" "mlflow_folder" {
  bucket = aws_s3_bucket.s3b-tip-predictor.id
  acl    = "private"
  key    = "mlflow/"
  source = "../init.txt"
}

resource "aws_sns_topic" "waiter_tip_topic" {
  name         = "waiter-tip-topic"
  display_name = "Waiter tip predictiom"

  tags = {
    Name        = "wtp-sns"
    Environment = "production"
  }
}

resource "aws_sns_topic_subscription" "waiter_tip_topic_sub" {
  topic_arn = aws_sns_topic.waiter_tip_topic.arn
  protocol  = "email"
  endpoint  = var.sns_endpoint
}

resource "aws_db_subnet_group" "wtp_db_subnet" {
  name       = "wtp_db_subnet"
  subnet_ids = [aws_subnet.wtp_private_subnet.id, aws_subnet.wtp_public_subnet.id]

  tags = {
    Name        = "db_subnet_group"
    Environment = "production"
  }
}

resource "aws_db_instance" "wtp_rds" {
  identifier                   = "wtp-rds-instance"
  allocated_storage            = 20
  db_subnet_group_name         = aws_db_subnet_group.wtp_db_subnet.id
  db_name                      = "mlflow_db"
  engine                       = "postgres"
  engine_version               = "14.3"
  instance_class               = "db.t3.micro"
  username                     = "postgres"
  password                     = "password"
  parameter_group_name         = "default.postgres14"
  multi_az                     = false
  publicly_accessible          = true
  max_allocated_storage        = 100
  storage_encrypted            = true
  storage_type                 = "gp2"
  performance_insights_enabled = true
  backup_retention_period      = 1
  skip_final_snapshot          = true
  allow_major_version_upgrade  = false
  auto_minor_version_upgrade   = true
  vpc_security_group_ids       = [aws_security_group.wtp_rds_sg.id]
  delete_automated_backups     = true
  apply_immediately            = true

  tags = {
    Name        = "wtp-rds"
    Environment = "production"
  }
}

resource "aws_ssm_parameter" "artifact_paths" {
  name        = "artifact_paths"
  description = "Paths to artifact folders in S3"
  type        = "String"
  value       = var.artifact_paths

  tags = {
    Name        = "artifact_paths"
    Environment = "production"
  }
}

resource "aws_ssm_parameter" "initial_paths" {
  name        = "initial_paths"
  description = "Main paths to S3 folders"
  type        = "String"
  value       = var.inital_paths

  tags = {
    Name        = "initial_paths"
    Environment = "production"
  }
}

resource "aws_ssm_parameter" "sns_topic" {
  name        = "sns_topic_arn"
  description = "SNS topic ARN to send emails"
  type        = "String"
  value       = aws_sns_topic.waiter_tip_topic.arn

  tags = {
    Name        = "sns_topic"
    Environment = "production"
  }
}

resource "aws_ssm_parameter" "tracking_server_host" {
  name        = "tracking_server_host"
  description = "Server host address"
  type        = "String"
  value       = var.tracking_server_host

  tags = {
    Name        = "tracking_server_host"
    Environment = "production"
  }
}
