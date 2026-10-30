variable "aws_region" {
  description = "AWS China region"
  type        = string
  default     = "cn-north-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "project" {
  description = "Project name used for resource naming"
  type        = string
  default     = "knowledge-assistant"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "azs" {
  type    = list(string)
  default = ["cn-north-1a", "cn-north-1b"]
}

variable "container_images" {
  description = "ECR image tags for the services and workers"
  type = object({
    rag              = string
    memory           = string
    model_gateway    = string
    agent            = string
    memory_worker    = string
    ingestion_worker = string
  })
  default = {
    rag              = ""
    memory           = ""
    model_gateway    = ""
    agent            = ""
    memory_worker    = ""
    ingestion_worker = ""
  }
}

variable "model_gateway_primary_base_url" {
  description = "OpenAI-compatible base URL of the in-region inference endpoint"
  type        = string
  default     = ""
}

variable "model_gateway_fallback_base_url" {
  description = "OpenAI-compatible base URL of the domestic API fallback"
  type        = string
  default     = ""
}

variable "model_api_key_primary" {
  description = "API key for the in-region inference endpoint (stored in Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "model_api_key_fallback" {
  description = "API key for the domestic API fallback (stored in Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "alb_certificate_arn" {
  description = "ACM certificate ARN for the internal ALB HTTPS listener (must be in the same aws-cn region)"
  type        = string
}

variable "sagemaker_llm_image" {
  type    = string
  default = ""
}

variable "sagemaker_llm_model_data" {
  type    = string
  default = ""
}

variable "sagemaker_embed_image" {
  type    = string
  default = ""
}

variable "sagemaker_embed_model_data" {
  type    = string
  default = ""
}

variable "create_sagemaker_endpoints" {
  description = "Create SageMaker real-time endpoints (requires model artifacts/images)"
  type        = bool
  default     = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
