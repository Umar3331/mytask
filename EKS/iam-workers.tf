resource "aws_iam_role" "Umar-node" {
  name = "terraform-eks-Umar-node"

  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY

}

resource "aws_iam_role_policy_attachment" "Umar-node-AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role = aws_iam_role.Umar-node.name
}

resource "aws_iam_role_policy_attachment" "Umar-node-AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role = aws_iam_role.Umar-node.name
}

resource "aws_iam_role_policy_attachment" "Umar-node-AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role = aws_iam_role.Umar-node.name
}

resource "aws_iam_instance_profile" "Umar-node" {
  name = "terraform-eks-Umar"
  role = aws_iam_role.Umar-node.name
}

