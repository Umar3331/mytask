resource "time_sleep" "wait_30_seconds" {
  depends_on = [helm_release.jhub]

  create_duration = "30s"
}

# Aws and kubectl commands to show IP where to acess Jupyterhub

resource "null_resource" "Jhub-access" {
  depends_on = [time_sleep.wait_30_seconds]

  provisioner "local-exec" {
    command = "aws eks --region $REGION update-kubeconfig --name $CLUSTER_NAME"

    environment = {
      REGION       = data.aws_region.current.name
      CLUSTER_NAME = var.cluster_name
    }
  }

  provisioner "local-exec" {
    command = "kubectl --namespace=$NAMESPACE get svc proxy-public"

    environment = {
      NAMESPACE = var.hub_namespace
    }
  }
}
