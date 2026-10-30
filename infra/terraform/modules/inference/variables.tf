variable "environment" {
  type = string
}

variable "project" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_ids" {
  type = list(string)
}

variable "llm_image" {
  type    = string
  default = ""
}

variable "llm_model_data" {
  type    = string
  default = ""
}

variable "embed_image" {
  type    = string
  default = ""
}

variable "embed_model_data" {
  type    = string
  default = ""
}

variable "create_endpoints" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
