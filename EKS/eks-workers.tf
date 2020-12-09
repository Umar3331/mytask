data "aws_ami" "eks-worker" {
  filter {
    name   = "name"
    values = ["amazon-eks-node-${aws_eks_cluster.Umar.version}-v*"]
  }

  most_recent = true
  owners      = ["602401143452"] # Amazon
}

locals {
  Umar-node-userdata = <<USERDATA
#!/bin/bash
set -o xtrace
/etc/eks/bootstrap.sh --apiserver-endpoint '${aws_eks_cluster.Umar.endpoint}' --b64-cluster-ca '${aws_eks_cluster.Umar.certificate_authority[0].data}' '${var.cluster-name}'
USERDATA

}

resource "aws_launch_configuration" "Umar" {
  associate_public_ip_address = true
  iam_instance_profile = aws_iam_instance_profile.Umar-node.name
  image_id = data.aws_ami.eks-worker.id
  instance_type = "t2.micro"
  name_prefix = "terraform-eks-Umar"
  security_groups = [aws_security_group.Umar-node.id]
  user_data_base64 = base64encode(local.Umar-node-userdata)

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "Umar" {
  desired_capacity = 2
  launch_configuration = aws_launch_configuration.Umar.id
  max_size = 4
  min_size = 2
  name = "terraform-eks-Umar"
  vpc_zone_identifier = module.vpc.public_subnets

  tag {
    key = "Name"
    value = "terraform-eks-Umar"
    propagate_at_launch = true
  }

  tag {
    key = "kubernetes.io/cluster/${var.cluster-name}"
    value = "owned"
    propagate_at_launch = true
  }
}

