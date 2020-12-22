data "aws_ami" "ubuntu_latest" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}
# Search for instance type
# Probably t2.small is better, but no time for testing
data "aws_ec2_instance_type_offering" "ubuntu_micro" {
  filter {
    name   = "instance-type"
    values = ["t2.medium"]
  }

  preferred_instance_types = ["t2.medium"]
}

data "aws_region" "current" {}

# Availability zones data source to get list of AWS Availability zones
data "aws_availability_zones" "available" {
  state = "available"
}
