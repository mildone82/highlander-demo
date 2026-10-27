module "network" {
  source = "./modules/network"

  vpc_name             = local.name_prefix
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  data_subnet_cidrs    = var.data_subnet_cidrs
  tags                 = local.common_tags
}

module "kms" {
  source = "./modules/kms"

  name_prefix = local.name_prefix
  tenants     = var.tenants
  tags        = local.common_tags
}

module "storage" {
  source = "./modules/storage"

  name_prefix   = local.name_prefix
  tenant_keys   = module.kms.tenant_key_arns
  app_key_arn   = module.kms.app_key_arn
  force_destroy = var.report_bucket_force_destroy
  tags          = local.common_tags
  depends_on    = [module.kms]
}

module "vector" {
  source = "./modules/vector"

  name_prefix     = local.name_prefix
  tenants         = var.tenants
  tenant_keys     = module.kms.tenant_key_arns
  app_key_arn     = module.kms.app_key_arn
  index_dimension = var.embedding_dimension
  tags            = local.common_tags
  depends_on      = [module.kms]
}

module "auth" {
  source = "./modules/auth"

  name_prefix          = local.name_prefix
  vpc_id               = module.network.vpc_id
  public_subnet_ids    = module.network.public_subnet_ids
  private_subnet_ids   = module.network.private_subnet_ids
  data_subnet_ids      = module.network.data_subnet_ids
  db_name              = var.db_name
  db_username          = var.db_username
  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  kms_key_arn          = module.kms.app_key_arn
  keycloak_image       = var.keycloak_image
  keycloak_hostname    = var.keycloak_hostname
  certificate_arn      = var.alb_certificate_arn
  tags                 = local.common_tags
  depends_on           = [module.network, module.kms]
}

module "compute" {
  source = "./modules/compute"

  name_prefix              = local.name_prefix
  python_runtime           = var.python_runtime
  memory_size              = var.lambda_memory_size
  timeout                  = var.lambda_timeout
  embedding_model_image    = var.embedding_model_image
  embedding_model_data_url = var.embedding_model_data_url
  deepseek_base_url        = var.deepseek_base_url
  deepseek_model_pro       = var.deepseek_model_pro
  deepseek_model_flash     = var.deepseek_model_flash
  vector_index_arns        = module.vector.index_arns
  report_bucket_arn        = module.storage.report_bucket_arn
  report_bucket_name       = module.storage.report_bucket_name
  data_bucket_arn          = module.storage.data_bucket_arn
  data_bucket_name         = module.storage.data_bucket_name
  kms_key_arn              = module.kms.app_key_arn
  tags                     = local.common_tags
  depends_on               = [module.network, module.vector, module.storage, module.kms]
}

module "api" {
  source = "./modules/api"

  name_prefix            = local.name_prefix
  python_runtime         = var.python_runtime
  api_handler_name       = module.compute.api_handler_function_name
  api_handler_arn        = module.compute.api_handler_function_arn
  api_handler_invoke_arn = module.compute.api_handler_invoke_arn
  domain_name            = var.api_domain_name
  certificate_arn        = var.api_domain_certificate_arn
  region                 = local.region
  dns_suffix             = local.dns_suffix
  tags                   = local.common_tags
  depends_on             = [module.compute]
}

module "state" {
  source = "./modules/state"

  name_prefix     = local.name_prefix
  data_subnet_ids = module.network.data_subnet_ids
  kms_key_arn     = module.kms.app_key_arn
  tags            = local.common_tags
  depends_on      = [module.network, module.kms]
}

module "async" {
  source = "./modules/async"

  name_prefix           = local.name_prefix
  report_generator_arn  = module.compute.report_generator_function_arn
  report_generator_name = module.compute.report_generator_function_name
  tags                  = local.common_tags
  depends_on            = [module.compute]
}

module "security" {
  source = "./modules/security"

  name_prefix = local.name_prefix
  enable      = var.enable_waf
  alb_arn     = module.auth.alb_arn
  tags        = local.common_tags
  depends_on  = [module.auth]
}

module "observability" {
  source = "./modules/observability"

  name_prefix       = local.name_prefix
  enable_cloudtrail = var.enable_cloudtrail
  log_bucket_name   = module.storage.log_bucket_name
  lambda_function_names = {
    authorizer       = module.api.authorizer_function_name
    api_handler      = module.compute.api_handler_function_name
    model_gateway    = module.compute.model_gateway_function_name
    report_generator = module.compute.report_generator_function_name
    ingest           = module.compute.ingest_function_name
  }
  report_dlq_name = module.async.report_dlq_name
  tags            = local.common_tags
  depends_on      = [module.api, module.compute, module.async, module.storage]
}
