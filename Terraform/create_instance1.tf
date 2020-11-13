provider "aws" {
 access_key = "your_access_key"
 secret_key = "your_secret_key"
 region     = "your_region"
}

data "aws_ami" "ubuntu" {
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
/*
resource "aws_instance" "myFirstInstance" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t2.micro"
  key_name = "Umar_Mumbai"
  security_groups = ["security_terraform"]
  user_data = file("Umar3.sh")
  tags = {
    Name = "terraform_new"
  }
}
*/
resource "aws_security_group" "security_terraform" {
  name        = "security_terraform"
  description = "security group for terraform"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

 ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

 # outbound from terraform server
  egress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags= {
    Name = "security_terraform"
  }
}

resource "aws_launch_configuration" "launch_conf" {
  image_id      = data.aws_ami.ubuntu.id
  instance_type = "t2.micro"
  key_name = "Umar_Mumbai"
  security_groups = ["security_terraform"]
  user_data = filebase64("Umar3.sh")

  lifecycle {
      create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "asg_1" {
  availability_zones = ["ap-south-1a", "ap-south-1b"]
# desired_capacity   = 1
  max_size           = 4
  min_size           = 2
  load_balancers = [aws_elb.Umar1.id] 
  launch_configuration = aws_launch_configuration.launch_conf.id
  
  lifecycle {
      create_before_destroy = true
  }  
}

# Create a new load balancer
resource "aws_elb" "Umar1" {
  name               = "Umar2"
  availability_zones = ["ap-south-1a", "ap-south-1b"]
 # security_groups = aws_security_group.security_terraform.id
  
  listener {
    instance_port     = 80
    instance_protocol = "http"
    lb_port           = 80
    lb_protocol       = "http"
  }

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    target              = "HTTP:80/"
    interval            = 30
  }

# instances                   = [aws_instance.myFirstInstance.id]
  cross_zone_load_balancing   = true
  idle_timeout                = 400
  connection_draining         = true
  connection_draining_timeout = 400

  tags = {
    Name = "Umar2"
  }
}

output "elb_dns_name" {
value = aws_elb.Umar1.dns_name
}
