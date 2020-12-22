resource "kubernetes_namespace" "vault" {
  metadata {
    name = "vault"
  }
}

resource "helm_release" "vault" {
  name = "vault"
  repository = "https://helm.releases.hashicorp.com/"
  chart = "vault"
  namespace = kubernetes_namespace.vault.metadata.0.name

  values = [
    file("values.yaml")
  ]
}
