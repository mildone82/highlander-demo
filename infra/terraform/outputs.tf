output "vpc_id" {
  value = module.network.vpc_id
}

output "alb_dns_name" {
  value = module.compute.alb_dns_name
}

output "document_bucket_name" {
  value = module.storage.document_bucket_name
}

output "ingestion_queue_url" {
  value = module.storage.ingestion_queue_url
}

output "sagemaker_llm_endpoint_name" {
  value = module.inference.llm_endpoint_name
}

output "sagemaker_embed_endpoint_name" {
  value = module.inference.embed_endpoint_name
}
