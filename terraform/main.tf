terraform {
  required_version = ">= 1.5.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "local" {}

resource "local_file" "platform_demo" {
  filename = "${path.module}/platform-demo.txt"

  content = <<-EOT
    Personal AI Assistant Platform

    Environment: development
    Managed by: Terraform
  EOT
}