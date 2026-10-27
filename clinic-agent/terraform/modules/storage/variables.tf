variable "name_prefix" {
  type = string
}

variable "tenant_keys" {
  description = "Per-tenant KMS key ARNs keyed by tenant code."
  type        = map(string)
}

variable "app_key_arn" {
  type = string
}

variable "force_destroy" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
