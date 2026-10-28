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
    rag           = string
    memory        = string
    model_gateway = string
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

variable "tags" {
  type    = map(string)
  default = {}
}
