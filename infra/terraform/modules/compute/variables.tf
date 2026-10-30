variable "environment" {
  type = string
}

variable "project" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "service_security_group_id" {
  type = string
}

variable "container_images" {
  type = object({
    rag              = string
    memory           = string
    model_gateway    = string
    agent            = string
    memory_worker    = string
    ingestion_worker = string
  })
}

variable "model_gateway_primary_base_url" {
  type    = string
  default = ""
}

variable "model_gateway_fallback_base_url" {
  type    = string
  default = ""
}

variable "model_api_key_primary_arn" {
  description = "Secrets Manager ARN holding the in-region inference API key"
  type        = string
}

variable "model_api_key_fallback_arn" {
  description = "Secrets Manager ARN holding the domestic fallback API key"
  type        = string
}

variable "alb_certificate_arn" {
  description = "ACM certificate ARN for the HTTPS listener"
  type        = string
}

variable "document_bucket_arn" {
  type = string
}

variable "ingestion_queue_arn" {
  type = string
}

variable "memory_queue_arn" {
  type = string
}

variable "memory_queue_url" {
  type = string
}

variable "ingestion_queue_url" {
  type = string
}

variable "ingestion_state_table_name" {
  type = string
}

variable "ingestion_state_table_arn" {
  type = string
}

variable "memory_write_state_table_name" {
  type = string
}

variable "memory_write_state_table_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
