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
  description = "ECR image tags for the three services"
  type = object({
    rag           = string
    memory        = string
    model_gateway = string
  })
  default = {
    rag           = ""
    memory        = ""
    model_gateway = ""
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
