variable "name_prefix" {
  type = string
}

variable "python_runtime" {
  type = string
}

variable "memory_size" {
  type = number
}

variable "timeout" {
  type = number
}

variable "embedding_model_image" {
  type = string
}

variable "embedding_model_data_url" {
  type = string
}

variable "deepseek_base_url" {
  type = string
}

variable "deepseek_model_pro" {
  type = string
}

variable "deepseek_model_flash" {
  type = string
}

variable "vector_index_arns" {
  type = map(string)
}

variable "report_bucket_arn" {
  type = string
}

variable "report_bucket_name" {
  type = string
}

variable "data_bucket_arn" {
  type = string
}

variable "data_bucket_name" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
