terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.17"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
  
  cloud {
    organization = "aurastream"
    workspaces {
      name = "aurastream-*"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "AuraStream"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Repository  = "https://github.com/your-org/aurastream"
    }
  }
}
