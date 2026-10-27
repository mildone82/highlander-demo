variable "name_prefix" {
  type = string
}

variable "enable_cloudtrail" {
  type    = bool
  default = true
}

variable "log_bucket_name" {
  type = string
}

variable "lambda_function_names" {
  type = map(string)
}

variable "report_dlq_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
