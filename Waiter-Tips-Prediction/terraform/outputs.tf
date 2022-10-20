# Generate output of IAM role name
output "iam_instance_profile_name" {
  value       = aws_iam_instance_profile.wtp_ec2_profile.name
  description = "IAM role name"
}
