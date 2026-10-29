output "region" {
  description = "Deployment region."
  value       = local.region
}

output "vpc_id" {
  description = "VPC id."
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet ids."
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet ids."
  value       = module.network.private_subnet_ids
}

output "data_subnet_ids" {
  description = "Data subnet ids."
  value       = module.network.data_subnet_ids
}

output "client_data_bucket" {
  description = "Client data bucket name."
  value       = module.storage.data_bucket_name
}

output "report_bucket" {
  description = "HTML report bucket name."
  value       = module.storage.report_bucket_name
}

output "spa_bucket" {
  description = "SPA static asset bucket name."
  value       = module.storage.spa_bucket_name
}

output "vector_bucket" {
  description = "S3 Vectors vector bucket name."
  value       = module.vector.vector_bucket_name
}

output "vector_index_arns" {
  description = "S3 Vectors index ARNs keyed by tenant."
  value       = module.vector.index_arns
}

output "sagemaker_endpoint_name" {
  description = "SageMaker embedding endpoint name."
  value       = module.compute.sagemaker_endpoint_name
}

output "agentcore_runtime_id" {
  description = "Bedrock AgentCore runtime id."
  value       = module.compute.agentcore_runtime_id
}

output "keycloak_alb_dns_name" {
  description = "Keycloak ALB DNS name."
  value       = module.auth.alb_dns_name
}

output "api_gateway_invoke_url" {
  description = "API Gateway stage invoke URL."
  value       = module.api.invoke_url
}

output "keycloak_db_endpoint" {
  description = "Keycloak RDS endpoint."
  value       = module.auth.db_endpoint
}

output "report_job_queue_url" {
  description = "Async report job queue URL."
  value       = module.async.report_queue_url
}
