# This thing pulls J-hub Helm chart and uses your values.yaml file
# Uses default namespace, but you can change that
# See the docs:
# https://registry.terraform.io/providers/hashicorp/helm/latest/docs/resources/release

resource "helm_release" "jhub" {
  name = "jupyterhub"
  # repository = "https://jupyterhub.github.io/helm-chart/"
  # chart      = "jupyterhub"
  # chart     = "./jupyterhub"
  chart     = "https://jupyterhub.github.io/helm-chart/jupyterhub-0.9.1.tgz"
  namespace = var.hub_namespace

  values = [
    file("values.yml")
  ]
}
