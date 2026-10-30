output "llm_endpoint_name" {
  value = var.create_endpoints ? aws_sagemaker_endpoint.llm[0].name : ""
}

output "embed_endpoint_name" {
  value = var.create_endpoints ? aws_sagemaker_endpoint.embed[0].name : ""
}
