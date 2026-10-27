variable "aws_region" {
  description = "AWS region to deploy into. Defaults to China (Beijing)."
  type        = string
  default     = "cn-north-1"
}

variable "name_prefix" {
  description = "Prefix applied to resource names."
  type        = string
  default     = "clinicsvc"
}

variable "environment" {
  description = "Environment name (dev/staging/prod)."
  type        = string
  default     = "dev"
}

variable "workspace_name" {
  description = "Workspace / project name used in tags."
  type        = string
  default     = "clinic-agent"
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}

variable "tenants" {
  description = "Map of clinic tenant short codes. Each tenant gets isolated S3 prefixes, KMS keys and S3 Vectors indexes."
  type        = map(string)
  default = {
    demo = "Demo Clinic"
  }
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones to use."
  type        = list(string)
  default     = ["cn-north-1a", "cn-north-1b"]
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs (one per AZ)."
  type        = list(string)
  default     = ["10.0.0.0/24", "10.0.1.0/24"]
}

variable "private_subnet_cidrs" {
  description = "Private (compute) subnet CIDRs (one per AZ)."
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "data_subnet_cidrs" {
  description = "Data (storage) subnet CIDRs (one per AZ)."
  type        = list(string)
  default     = ["10.0.20.0/24", "10.0.21.0/24"]
}

variable "db_name" {
  description = "Keycloak database name."
  type        = string
  default     = "keycloak"
}

variable "db_username" {
  description = "Keycloak database master username."
  type        = string
  default     = "keycloak"
}

variable "db_instance_class" {
  description = "RDS instance class for Keycloak."
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB."
  type        = number
  default     = 20
}

variable "keycloak_image" {
  description = "Keycloak container image URI (mirror to ECR in China before deploy)."
  type        = string
  default     = "quay.io/keycloak/keycloak:26.0"
}

variable "keycloak_hostname" {
  description = "Public hostname for Keycloak (requires ICP filing)."
  type        = string
  default     = ""
}

variable "alb_certificate_arn" {
  description = "ACM certificate ARN for HTTPS on the ALB. Optional in dev."
  type        = string
  default     = ""
}

variable "api_domain_name" {
  description = "Custom domain for the API Gateway (requires ICP filing). Optional."
  type        = string
  default     = ""
}

variable "api_domain_certificate_arn" {
  description = "ACM certificate ARN for the API Gateway custom domain."
  type        = string
  default     = ""
}

variable "embedding_model_image" {
  description = "SageMaker inference image for TEI + BGE-M3 (must be mirrored to an in-region ECR repository)."
  type        = string
  default     = "763104351884.dkr.ecr.cn-north-1.amazonaws.com.cn/tei-bge-m3:latest"
}

variable "embedding_model_data_url" {
  description = "S3 URI of the BGE-M3 model artifacts."
  type        = string
  default     = ""
}

variable "embedding_dimension" {
  description = "Embedding dimension of BGE-M3."
  type        = number
  default     = 1024
}

variable "deepseek_base_url" {
  description = "OpenAI-compatible base URL for the external LLM."
  type        = string
  default     = "https://api.deepseek.com"
}

variable "deepseek_model_pro" {
  description = "Primary model for complex analysis."
  type        = string
  default     = "deepseek-v4-pro"
}

variable "deepseek_model_flash" {
  description = "Fallback/fast model."
  type        = string
  default     = "deepseek-flash"
}

variable "report_bucket_force_destroy" {
  description = "Whether to force-destroy buckets on teardown (dev only)."
  type        = bool
  default     = false
}

variable "enable_waf" {
  description = "Enable the WAFv2 web ACL association."
  type        = bool
  default     = true
}

variable "enable_cloudtrail" {
  description = "Enable the CloudTrail trail."
  type        = bool
  default     = true
}

variable "lambda_memory_size" {
  description = "Default Lambda memory in MB."
  type        = number
  default     = 1024
}

variable "lambda_timeout" {
  description = "Default Lambda timeout in seconds."
  type        = number
  default     = 60
}

variable "python_runtime" {
  description = "Python runtime for Lambda functions."
  type        = string
  default     = "python3.12"
}
