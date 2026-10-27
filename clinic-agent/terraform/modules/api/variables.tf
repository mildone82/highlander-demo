variable "name_prefix" {
  type = string
}

variable "python_runtime" {
  type = string
}

variable "api_handler_name" {
  type = string
}

variable "api_handler_arn" {
  type = string
}

variable "api_handler_invoke_arn" {
  type = string
}

variable "domain_name" {
  type    = string
  default = ""
}

variable "certificate_arn" {
  type    = string
  default = ""
}

variable "region" {
  type = string
}

variable "dns_suffix" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
