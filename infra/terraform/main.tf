provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = merge(var.tags, { Environment = var.environment, Project = var.project })
}

module "network" {
  source = "./modules/network"

  environment = var.environment
  project     = var.project
  vpc_cidr    = var.vpc_cidr
  azs         = var.azs
  tags        = local.common_tags
}

module "storage" {
  source = "./modules/storage"

  environment = var.environment
  project     = var.project
  tags        = local.common_tags
}

module "inference" {
  source = "./modules/inference"

  environment            = var.environment
  project                = var.project
  subnet_ids             = module.network.private_subnet_ids
  security_group_ids     = [module.network.sagemaker_security_group_id]
  llm_image              = var.sagemaker_llm_image
  llm_model_data         = var.sagemaker_llm_model_data
  embed_image            = var.sagemaker_embed_image
  embed_model_data       = var.sagemaker_embed_model_data
  create_endpoints       = var.create_sagemaker_endpoints
  tags                   = local.common_tags
}

module "compute" {
  source = "./modules/compute"

  environment        = var.environment
  project            = var.project
  vpc_id             = module.network.vpc_id
  private_subnet_ids = module.network.private_subnet_ids
  public_subnet_ids  = module.network.public_subnet_ids
  alb_security_group_id = module.network.alb_security_group_id
  service_security_group_id = module.network.service_security_group_id
  container_images   = var.container_images
  model_gateway_primary_base_url  = var.model_gateway_primary_base_url
  model_gateway_fallback_base_url = var.model_gateway_fallback_base_url
  tags               = local.common_tags
}

module "observability" {
  source = "./modules/observability"

  environment    = var.environment
  project        = var.project
  ingestion_dlq_name = module.storage.ingestion_dlq_name
  memory_dlq_name    = module.storage.memory_dlq_name
  tags           = local.common_tags
}
