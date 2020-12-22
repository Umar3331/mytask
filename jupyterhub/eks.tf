# Module that creates EKS cluster
# Possible to add more config inputs
# See the docs:
# https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = var.cluster_name
  cluster_version = "1.17"
  subnets         = module.vpc.private_subnets
  vpc_id          = module.vpc.vpc_id
  ### Here is possible to add Cluster log groups
  ### Uncommented to make JanisK life easier
  # cluster_enabled_log_types = ["audit", "api", "authenticator", "controllerManager", "scheduler"]

  worker_groups = [
    {
      name                 = "worker-group-1"
      instance_type        = data.aws_ec2_instance_type_offering.ubuntu_micro.id
      subnets              = [module.vpc.private_subnets[0]]
      asg_desired_capacity = 1
    },
    {
      name                 = "worker-group-2"
      instance_type        = data.aws_ec2_instance_type_offering.ubuntu_micro.id
      subnets              = [module.vpc.private_subnets[1]]
      asg_desired_capacity = 1
    }
 ]

}
