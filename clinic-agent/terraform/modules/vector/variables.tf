variable "name_prefix" {
  type = string
}

variable "tenants" {
  type = map(string)
}

variable "tenant_keys" {
  description = "Per-tenant KMS key ARNs keyed by tenant code."
  type        = map(string)
}

variable "app_key_arn" {
  type = string
}

variable "index_dimension" {
  type    = number
  default = 1024
}

variable "tags" {
  type    = map(string)
  default = {}
}
