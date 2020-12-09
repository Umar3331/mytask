resource "aws_eks_cluster" "Umar" {
  name     = var.cluster-name
  role_arn = aws_iam_role.Umar-cluster.arn

  vpc_config {
    security_group_ids = [aws_security_group.Umar-cluster.id]
    subnet_ids = module.vpc.public_subnets
  }

  depends_on = [
    aws_iam_role_policy_attachment.Umar-cluster-AmazonEKSClusterPolicy,
    aws_iam_role_policy_attachment.Umar-cluster-AmazonEKSServicePolicy,
  ]
}

